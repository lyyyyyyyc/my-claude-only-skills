"""Inspect or change reasoning tiers for a Codex++ relay model.

Usage:
    python tiers.py status  --model deepseek-v4.1-flash-1017
    python tiers.py inspect --model deepseek-v4.1-flash-1017
    python tiers.py patch   --model deepseek-v4.1-flash-1017 [--add max,ultra] [--default max]
                              [--dry-run]

Writes go through the running Codex++ bridge, which is the only mutation path
that survives the app's own settings.json rewrites. Native catalog fields are
persisted in the profile's modelMetadata, so regeneration retains the tiers.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import CdpError, CdpSession, probe  # noqa: E402

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DEFAULT_LEVELS = {
    "none": "Fast responses without reasoning",
    "minimal": "Minimal reasoning, fastest responses",
    "low": "Fast responses with lighter reasoning",
    "medium": "Balances speed and reasoning depth for everyday tasks",
    "high": "Greater reasoning depth for complex problems",
    "xhigh": "Extra high reasoning depth for complex problems",
    "max": "Maximum reasoning depth for the hardest problems",
    "ultra": "Maximum reasoning with automatic task delegation",
}

LEVEL_ORDER = ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"]


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def plus_home() -> Path:
    return Path.home() / ".codex-session-delete"


def settings_path() -> Path:
    return plus_home() / "settings.json"


def read_settings() -> dict:
    with settings_path().open(encoding="utf-8") as handle:
        return json.load(handle)


def active_profile(settings: dict) -> dict:
    active = settings.get("activeRelayId") or ""
    for profile in settings.get("relayProfiles") or []:
        if profile.get("id") == active:
            return profile
    raise SystemExit(f"未找到激活的供应商档案：{active or '(空)'}")


def catalog_path_for(settings: dict, profile: dict) -> Path:
    content = profile.get("configContents") or ""
    match = re.search(r'^\s*model_catalog_json\s*=\s*"([^"]+)"', content, re.M)
    if not match:
        raise SystemExit("激活档案的 configContents 里没有 model_catalog_json。")
    raw = match.group(1).replace("\\\\", "\\")
    path = Path(raw)
    return path if path.is_absolute() else codex_home() / path


def load_catalog(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"catalog 文件不存在：{path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def find_model(catalog: dict, slug: str) -> dict | None:
    for model in catalog.get("models") or []:
        if model.get("slug") == slug:
            return model
    return None


def levels_of(model: dict) -> list[str]:
    raw = model.get("supported_reasoning_levels") or []
    return [str(item.get("effort", "")) for item in raw if isinstance(item, dict)]


def find_codex_cli() -> str | None:
    found = shutil.which("codex")
    if found:
        return found
    bin_dir = Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin"
    if bin_dir.exists():
        candidates = sorted(bin_dir.glob("*/codex.exe"), key=lambda p: p.stat().st_mtime)
        if candidates:
            return str(candidates[-1])
    return None


def cli_levels(slug: str) -> tuple[list[str], str] | None:
    """Ask the Codex CLI what it actually loads, mirroring the UI path."""
    exe = find_codex_cli()
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, "debug", "models"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = result.stdout or ""
    start = text.find('{"models"')
    if start < 0:
        return None
    try:
        payload, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None
    model = find_model(payload, slug)
    if not model:
        return None
    return levels_of(model), str(model.get("default_reasoning_level") or "")


def report(slug: str, use_cli: bool = True) -> int:
    settings = read_settings()
    profile = active_profile(settings)
    catalog_file = catalog_path_for(settings, profile)
    catalog = load_catalog(catalog_file)
    model = find_model(catalog, slug)
    reachable = probe()

    print(f"供应商档案 : {profile.get('id')} ({profile.get('name', '')})")
    print(f"catalog   : {catalog_file}")
    print(f"实时桥接   : {'可用 (端口 %s)' % reachable.get('port') if reachable.get('available') else '不可用 - ' + str(reachable.get('reason'))}")
    if not model:
        print(f"模型       : {slug} 不在 catalog 中")
        return 1
    print(f"模型       : {slug}")
    print(f"默认档位   : {model.get('default_reasoning_level')}")
    print(f"档位       : {'/'.join(levels_of(model))}")
    meta_raw = profile.get("modelMetadata") or ""
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except ValueError:
            meta = {}
        entry = meta.get(slug)
        if entry:
            native = "supported_reasoning_levels" in entry
            efforts = levels_of(entry) if native else [
                item.get("reasoningEffort") for item in entry.get("supportedReasoningEfforts") or []
            ]
            default = entry.get("default_reasoning_level") if native else entry.get("defaultReasoningEffort")
            schema = "native" if native else "legacy UI, ignored by generator"
            print(f"modelMetadata: {'/'.join(str(e) for e in efforts)} (默认 {default}, {schema})")
    if use_cli:
        actual = cli_levels(slug)
        if actual is None:
            print("CLI 校验   : 跳过（未找到 codex 可执行文件）")
        else:
            tiers, default = actual
            print(f"CLI 实际   : {'/'.join(tiers)} (默认 {default})")
    return 0


def build_catalog(catalog: dict, slug: str, add: list[str], default: str | None) -> dict:
    model = find_model(catalog, slug)
    if not model:
        raise SystemExit(f"catalog 中没有模型 {slug}")
    existing = model.get("supported_reasoning_levels") or []
    have = {str(item.get("effort")) for item in existing if isinstance(item, dict)}
    for level in add:
        if level in have:
            continue
        if level not in DEFAULT_LEVELS:
            raise SystemExit(f"未知档位：{level}")
        existing.append({"effort": level, "description": DEFAULT_LEVELS[level]})
        have.add(level)
    existing.sort(key=lambda item: LEVEL_ORDER.index(str(item.get("effort")))
                  if str(item.get("effort")) in LEVEL_ORDER else len(LEVEL_ORDER))
    model["supported_reasoning_levels"] = existing
    if default:
        if default not in have:
            raise SystemExit(f"默认档位 {default} 不在支持列表里")
        model["default_reasoning_level"] = default
    return catalog


def write_catalog(path: Path, catalog: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(catalog, handle, ensure_ascii=False)
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise


def patch(slug: str, add: list[str], default: str | None, dry_run: bool) -> int:
    settings = read_settings()
    profile = active_profile(settings)
    main_catalog = catalog_path_for(settings, profile)
    target = main_catalog
    catalog = load_catalog(main_catalog)
    updated = build_catalog(catalog, slug, add, default)
    model = find_model(updated, slug)
    print(f"目标文件 : {target}")
    print(f"档位     : {'/'.join(levels_of(model))}")
    print(f"默认档位 : {model.get('default_reasoning_level')}")
    if dry_run:
        print("dry-run：未写入任何文件。")
        return 0

    if not profile.get("configContents"):
        raise SystemExit("激活档案缺少 configContents，已停止，避免破坏配置。")
    relative = f"model-catalogs/{target.name}"
    content = profile["configContents"]
    pattern = re.compile(r'^[ \t]*model_catalog_json[ \t]*=[ \t]*"[^"\r\n]*"[ \t]*(?=\r?$)', re.M)
    if pattern.search(content):
        new_content = pattern.sub(f'model_catalog_json = "{relative}"', content, count=1)
    else:
        new_content = f'model_catalog_json = "{relative}"\n' + content

    meta_raw = profile.get("modelMetadata") or ""
    try:
        meta = json.loads(meta_raw) if meta_raw else {}
    except ValueError as error:
        raise SystemExit("modelMetadata 不是有效 JSON，已停止，未丢弃已有元数据。") from error
    if not isinstance(meta, dict):
        raise SystemExit("modelMetadata 必须是 JSON 对象，已停止。")
    previous = meta.get(slug) or {}
    if not isinstance(previous, dict):
        raise SystemExit(f"modelMetadata 中的 {slug} 必须是 JSON 对象，已停止。")
    entry = dict(previous)
    for key in ("displayName", "defaultReasoningEffort", "supportedReasoningEfforts"):
        entry.pop(key, None)
    entry["default_reasoning_level"] = model.get("default_reasoning_level")
    entry["supported_reasoning_levels"] = model.get("supported_reasoning_levels") or []
    meta[slug] = entry

    reachable = probe()
    if reachable.get("available"):
        session = CdpSession()
        try:
            live = session.bridge("/settings/get")
            profiles = live.get("relayProfiles") or []
            for item in profiles:
                if item.get("id") == profile.get("id"):
                    item["configContents"] = new_content
                    item["modelMetadata"] = json.dumps(meta, ensure_ascii=False)
            session.bridge("/settings/set", {"relayProfiles": profiles})
            print("已通过实时桥接写入 settings.json")
        finally:
            session.close()
    else:
        backup = settings_path().with_suffix(
            ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        )
        shutil.copy2(settings_path(), backup)
        for item in settings.get("relayProfiles") or []:
            if item.get("id") == profile.get("id"):
                item["configContents"] = new_content
                item["modelMetadata"] = json.dumps(meta, ensure_ascii=False)
        write_catalog(settings_path(), settings)
        print(f"桥接不可用，已备份并直接改 settings.json：{backup.name}")

    write_catalog(target, updated)
    print("catalog 已写入")

    config = codex_home() / "config.toml"
    if config.exists():
        with config.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
        new_text, count = pattern.subn(f'model_catalog_json = "{relative}"', text, count=1)
        if count and new_text != text:
            with config.open("w", encoding="utf-8", newline="") as handle:
                handle.write(new_text)
            print("config.toml 已同步")
    print("完成。重启 Codex++ 后新档位生效。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="调整 Codex++ 中转模型的思考档位")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "inspect"):
        item = sub.add_parser(name)
        item.add_argument("--model", required=True, help="模型 slug，例如 deepseek-v4.1-flash-1017")
    item = sub.add_parser("patch")
    item.add_argument("--model", required=True)
    item.add_argument("--add", default="max", help="逗号分隔，例如 max,ultra")
    item.add_argument("--default", default=None, help="默认档位，例如 max")
    item.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.command in ("status", "inspect"):
        return report(args.model)
    levels = [part.strip() for part in (args.add or "").split(",") if part.strip()]
    return patch(args.model, levels, args.default, args.dry_run)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CdpError as error:
        print(f"调试通道错误：{error}", file=sys.stderr)
        sys.exit(1)
