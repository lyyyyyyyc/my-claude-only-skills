"""Validate Claude Code metadata, hashes, and migration preservation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml


FIELDS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
    "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
    "user-invocable", "disallowed-tools", "model", "effort", "context", "agent",
    "background", "hooks", "paths", "shell",
}


def split_skill(content: bytes):
    text = content.decode("utf-8-sig")
    match = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not match:
        raise ValueError("Missing frontmatter")
    return yaml.safe_load(match.group(1)), text[match.end():]


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_child(root: Path, relative: str):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe relative path: {relative}")
    child = root / rel
    child.resolve().relative_to(root.resolve())
    return child


def validate(repo: Path, update: bool = False, source_check: bool = False):
    catalog_path = repo / "_meta/codex-export.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert catalog["schemaVersion"] == 1
    errors = []
    files_checked = 0
    names = set()
    for skill in catalog["skills"]:
        try:
            name = skill["name"]
            assert name not in names, "Duplicate skill name"
            names.add(name)
            assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) and len(name) <= 64
            assert skill["path"] == ("skills/" if skill["default"] else "variants/") + name
            root = safe_child(repo, skill["path"])
            meta, body = split_skill((root / "SKILL.md").read_bytes())
            assert isinstance(meta, dict) and not (set(meta) - FIELDS), "Unknown metadata fields"
            assert meta["name"] == name
            assert isinstance(meta["description"], str) and 0 < len(meta["description"]) <= 1024
            if "compatibility" in meta:
                assert isinstance(meta["compatibility"], str) and 0 < len(meta["compatibility"]) <= 500
            if "context" in meta:
                assert meta["context"] == "fork"
            if "metadata" in meta:
                assert isinstance(meta["metadata"], dict)
                assert all(isinstance(k, str) and isinstance(v, str) for k, v in meta["metadata"].items())
            assert hashlib.sha256(body.encode("utf-8")).hexdigest() == skill["bodySha256"], "Instruction body changed"
            for original in skill["sourceFiles"]:
                target = safe_child(root, original["path"])
                if original["path"] != "SKILL.md":
                    assert digest(target) == original["sha256"], f"Source resource changed: {original['path']}"
                if source_check:
                    source = Path(skill["source"]) / original["path"]
                    assert digest(source) == original["sha256"], f"Original source changed: {source}"
            actual = []
            for file in sorted(root.rglob("*")):
                assert not file.is_symlink(), f"Link remains: {file}"
                if file.is_file():
                    actual.append({
                        "path": file.relative_to(root).as_posix(),
                        "sha256": digest(file), "size": file.stat().st_size,
                    })
            if update:
                skill["exportFiles"] = actual
            else:
                assert actual == skill["exportFiles"], "Export file inventory changed"
            files_checked += len(actual)
        except (AssertionError, OSError, ValueError, KeyError, TypeError) as error:
            errors.append({"skill": skill["name"], "error": str(error) or "Schema validation failed"})
    if update and not errors:
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "packagesChecked": len(catalog["skills"]), "filesChecked": files_checked,
        "sourcePreservationChecked": source_check, "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--record-hashes", action="store_true")
    parser.add_argument("--check-source", action="store_true")
    args = parser.parse_args()
    raise SystemExit(validate(args.repo, args.record_hashes, args.check_source))
