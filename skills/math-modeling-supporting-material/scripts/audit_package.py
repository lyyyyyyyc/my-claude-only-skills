"""只读盘点数学建模项目，检查支撑材料结构及证据一致性。"""

import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from check_privacy import scan_privacy


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_excel_sheet(path, name):
    """不仅核对表名，也检查关系指向的工作表实体确实存在。"""
    with zipfile.ZipFile(path) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        matches = [
            n
            for n in book.iter()
            if n.tag.endswith("}sheet") and n.attrib.get("name") == name
        ]
        if len(matches) != 1:
            raise ValueError("声明的工作表名不存在或重复")
        sheet = matches[0]
        rel_id = next((v for k, v in sheet.attrib.items() if k.endswith("}id")), None)
        if rel_id is None:
            raise ValueError("工作表没有关系ID")
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = [n for n in relations if n.attrib.get("Id") == rel_id]
        if len(targets) != 1 or targets[0].attrib.get("TargetMode") == "External":
            raise ValueError("工作表关系缺失或指向外部")
        target = targets[0].attrib.get("Target", "")
        if not target or "\\" in target:
            raise ValueError("工作表目标不合法")
        member = posixpath.normpath(
            target.lstrip("/") if target.startswith("/") else "xl/" + target
        )
        if member.startswith("../"):
            raise ValueError("工作表目标越界")
        worksheet = ET.fromstring(archive.read(member))
        if worksheet.tag.rsplit("}", 1)[-1] != "worksheet":
            raise ValueError("关系目标不是数据工作表")


def file_in(root, relative, prefix=None):
    """清单只接受包内相对路径，不能借连接点访问包外文件。"""
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("缺少有效相对路径")
    rel = PurePosixPath(relative)
    if (
        "\\" in relative
        or rel.is_absolute()
        or PureWindowsPath(relative).drive
        or ".." in rel.parts
        or (
            prefix
            and rel.parts[: len(PurePosixPath(prefix).parts)]
            != PurePosixPath(prefix).parts
        )
    ):
        raise ValueError(f"路径不合法或不在指定目录: {relative}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"文件缺失或越界: {relative}")
    if path.stat().st_size == 0:
        raise ValueError(f"文件为空: {relative}")
    return path


def walk_files(root, exclude=()):
    ignored = {".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints"}
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        dirs[:] = [
            name
            for name in dirs
            if name not in ignored
            and not (here / name).is_symlink()
            and (here / name).resolve().is_relative_to(root)
            and not any((here / name).resolve().is_relative_to(p) for p in exclude)
        ]
        for name in sorted(files):
            path = here / name
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                continue
            if not any(path.resolve().is_relative_to(p) for p in exclude):
                yield path


def inventory(project, exclude=()):
    types = {
        ".ipynb",
        ".py",
        ".md",
        ".tex",
        ".pdf",
        ".csv",
        ".tsv",
        ".xlsx",
        ".json",
        ".png",
        ".jpg",
        ".svg",
        ".docx",
        ".txt",
    }
    rows = []
    for path in walk_files(project, exclude):
        if path.suffix.lower() not in types:
            continue
        row = {
            "文件": path.relative_to(project).as_posix(),
            "字节数": path.stat().st_size,
            "SHA256": sha256(path),
        }
        if path.suffix.lower() == ".ipynb":
            try:
                notebook = read_json(path)
                cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
                sources = [c.get("source", "") for c in cells]
                code = "\n".join(
                    s if isinstance(s, str) else "".join(s) for s in sources
                )
                row["代码单元数"] = len(cells)
                row["需检查Notebook专用语法"] = bool(
                    re.search(r"(?m)^\s*[%!]|get_ipython\(", code)
                )
                row["历史错误输出数"] = sum(
                    o.get("output_type") == "error"
                    for c in cells
                    for o in c.get("outputs", [])
                )
            except (ValueError, KeyError, TypeError, UnicodeError) as exc:
                row["读取错误"] = str(exc)
        rows.append(row)
    return {
        "说明": "只读候选盘点，不能替代论文引用及计算依赖核对；不跟随包外链接",
        "文件数": len(rows),
        "文件": rows,
    }


def check_package(project, package, audit_dir):
    errors = []
    warnings = []

    def require(ok, message):
        if not ok:
            errors.append(message)

    def checked_file(root, relative, prefix=None):
        try:
            return file_in(root, relative, prefix)
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
            return None

    require(
        {p.name for p in package.iterdir()}
        == {"Code", "Figures", "User_data", "Readme.txt"},
        "根目录必须恰好为 Code、Figures、User_data、Readme.txt",
    )
    for directory in ("Code", "Figures", "User_data"):
        require((package / directory).is_dir(), f"缺少目录: {directory}")
    require(
        not audit_dir.resolve().is_relative_to(package.resolve()),
        "审核目录必须在交付包外",
    )
    figures = package / "Figures"
    require(
        figures.is_dir()
        and {p.name for p in figures.iterdir()}
        == {"paper_figures", "paper_tables", "results"},
        "Figures只能含图片、论文表格与结果三个目录",
    )
    image_dir = figures / "paper_figures"
    if image_dir.is_dir():
        images = list(image_dir.iterdir())
        matches = [
            re.fullmatch(r"(\d{2,})\.(?:png|svg|pdf|jpg|jpeg|tif|tiff)", p.name, re.I)
            for p in images
        ]
        require(
            all(p.is_file() for p in images) and all(matches),
            "图片必须采用01开始的纯数字文件名",
        )
        numbers = sorted({int(m[1]) for m in matches if m})
        require(
            numbers == list(range(1, len(numbers) + 1)), "图片编号必须从01连续、不跳号"
        )
    else:
        require(False, "缺少图片目录")
    table_dir = figures / "paper_tables"
    require(table_dir.is_dir(), "缺少论文表格目录")
    if table_dir.is_dir():
        require(
            all(
                p.is_file() and p.suffix.lower() in {".xlsx", ".csv", ".tsv"}
                for p in table_dir.iterdir()
            ),
            "论文表格目录仅放可编辑表格",
        )
    for path in package.rglob("*"):
        require(
            path.resolve().is_relative_to(package),
            f"包内包含外部连接: {path.relative_to(package)}",
        )
        require(
            path.suffix.lower() not in {".ipynb", ".pyc", ".pyo"},
            f"不应交付Notebook或字节码: {path.relative_to(package)}",
        )
    readme = checked_file(package, "Readme.txt")
    if readme:
        text = readme.read_text(encoding="utf-8-sig")
        headers = re.findall(r"(?m)^(\d+)\.\s+(.+)$", text)
        require(
            headers == [("1", "材料说明"), ("2", "代码运行说明")],
            "Readme一级标题应仅为1. 材料说明、2. 代码运行说明",
        )
        require(
            "{{" not in text and "\ufffd" not in text, "Readme有未填占位符或替代字符"
        )
        runtime_text = text.split("2. 代码运行说明", 1)[-1].strip()
        require(len(runtime_text) <= 300, "运行说明仅需简短环境介绍")
        require(
            not re.search(
                r"(?im)^\s*(?:pip\s+install|conda\s+(?:run|create|activate)|python\s+(?:-m|Code[/\\]))",
                runtime_text,
            ),
            "运行说明不放安装或执行教程",
        )
        require(
            not re.search(
                r"实际验证记录|不以简化代码|不用复算图冒充|support_verification|run_logs|results[/\\]_cache",
                text,
            ),
            "Readme含过程记录或防御性说明",
        )
    checked_file(package, "Code/run_all.py", "Code")
    checked_file(package, "Code/requirements.txt", "Code")

    code = {
        p.relative_to(package).as_posix(): p for p in (package / "Code").rglob("*.py")
    }
    allowed_code_files = {
        ".py",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".csv",
        ".lock",
    }
    for path in (package / "Code").rglob("*"):
        if path.is_file():
            require(
                path.suffix.lower() in allowed_code_files,
                f"Code存在非PY源码或未声明文件类型: {path.relative_to(package)}",
            )
    require(bool(code), "缺少PY源码")
    for relative, path in code.items():
        try:
            source = path.read_text(encoding="utf-8-sig")
            require("\ufffd" not in source, f"源码存在替代字符: {relative}")
            tree = ast.parse(source, filename=relative)
            compile(tree, relative, "exec")
            for node in ast.walk(tree):
                if (isinstance(node, ast.Name) and node.id == "get_ipython") or (
                    isinstance(node, ast.Attribute) and node.attr == "get_ipython"
                ):
                    errors.append(f"源码仍依赖Notebook内核: {relative}")
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and ".ipynb" in node.value.lower()
                ):
                    warnings.append(
                        f"发现Notebook路径字符串，请人工区分出处说明与运行依赖: {relative}"
                    )
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"源码语法或编码错误: {relative}: {exc}")

    manifest_path = checked_file(audit_dir, "manifest.json")
    if not manifest_path:
        return {"通过": False, "错误": errors}
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("清单必须是JSON对象")
    require(manifest.get("schema_version") == 3, "清单版本必须为3")
    for key in (
        "paper_versions",
        "required_sections",
        "helpers",
        "sources",
        "artifacts",
        "external_data",
    ):
        require(isinstance(manifest.get(key), list), f"清单字段必须是列表: {key}")
    if any(
        not isinstance(manifest.get(key), list)
        for key in (
            "paper_versions",
            "required_sections",
            "helpers",
            "sources",
            "artifacts",
            "external_data",
        )
    ):
        return {"通过": False, "错误": errors, "需人工复核": warnings}
    versions = manifest["paper_versions"]
    require(
        bool(versions) and all(isinstance(v, str) and v.strip() for v in versions),
        "缺少论文版本",
    )
    helpers = set(manifest["helpers"])
    result_groups = manifest.get("result_groups", [])
    result_root = figures / "results"
    require(
        isinstance(result_groups, list)
        and bool(result_groups)
        and all(
            isinstance(g, str) and re.fullmatch(r"problem_[1-9]\d*_results", g)
            for g in result_groups
        ),
        "缺少有效题号结果目录清单",
    )
    if result_root.is_dir():
        require(
            {p.name for p in result_root.iterdir()} == set(result_groups),
            "results下只能含指定题号结果目录",
        )
        for group in result_root.iterdir():
            require(group.is_dir(), "结果分组必须为目录")
            if group.is_dir():
                require(any(group.iterdir()), "题号结果目录不能为空")
                require(
                    all(
                        p.is_file() and p.suffix.lower() in {".xlsx", ".csv", ".tsv"}
                        for p in group.iterdir()
                    ),
                    "结果目录仅放直接答题表格，不嵌套过程目录",
                )
    else:
        require(False, "缺少结果目录")
    require(
        helpers <= set(code) and "Code/run_all.py" not in helpers, "公共代码声明不合法"
    )
    required = set(manifest["required_sections"])
    require(bool(required), "缺少应覆盖功能清单")
    sections, functional, source_paths = set(), set(), set()
    require(bool(manifest["sources"]), "缺少源程序覆盖清单")
    for item in manifest["sources"]:
        path = checked_file(project, item["path"])
        require(item["path"] not in source_paths, f"源文件重复登记: {item['path']}")
        source_paths.add(item["path"])
        if path:
            require(sha256(path) == item["sha256"], f"源文件哈希不符: {item['path']}")
        scripts = set(item["scripts"])
        if scripts:
            require(scripts <= set(code), f"源文件对应PY缺失: {item['path']}")
            require(
                not scripts & (helpers | {"Code/run_all.py"}),
                "源计算不能仅映射到公共代码或总入口",
            )
            sections.update(item["sections"])
            functional.update(scripts)
        else:
            require(
                bool(item.get("exclude_reason", "").strip()),
                f"未交付源程序且未说明排除理由: {item['path']}",
            )
    require(required <= sections, f"缺少功能覆盖: {sorted(required - sections)}")
    require(
        set(code) == functional | helpers | {"Code/run_all.py"},
        "有PY未纳入功能或公共代码清单",
    )

    artifact_ids = set()
    declared_tables = set()
    for item in manifest["artifacts"]:
        kind = item["kind"]
        require(
            kind in {"paper_figure", "paper_table", "result"}, f"图表类型错误: {kind}"
        )
        version = item.get("paper_version", "")
        key = (version, item["id"])
        require(
            bool(item["id"]) and key not in artifact_ids, f"图表编号重复或为空: {key}"
        )
        artifact_ids.add(key)
        if kind != "result":
            require(version in versions, f"图表论文版本未登记: {key}")
        path = checked_file(
            package,
            item["path"],
            {"result": "Figures/results", "paper_table": "Figures/paper_tables"}.get(
                kind, "Figures/paper_figures"
            ),
        )
        if not path:
            continue
        if kind == "paper_figure":
            require(sha256(path) == item.get("sha256"), f"论文图哈希不符: {item['id']}")
        elif kind in {"result", "paper_table"}:
            if kind == "result":
                original = checked_file(audit_dir, item.get("source_output"))
                if original:
                    require(
                        sha256(path) == sha256(original),
                        f"结果文件不是程序原样输出: {item['id']}",
                    )
            else:
                declared_tables.add(item["path"])
            require(
                path.suffix.lower() in {".csv", ".tsv", ".xlsx"},
                f"表格不是可编辑数据: {item['id']}",
            )
            if path.suffix.lower() == ".xlsx":
                try:
                    verify_excel_sheet(path, item.get("sheet"))
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    zipfile.BadZipFile,
                    ET.ParseError,
                ) as exc:
                    errors.append(f"表格工作表缺失或损坏: {item['id']}: {exc}")
            elif path.suffix.lower() in {".csv", ".tsv"}:
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    rows = csv.reader(
                        stream, delimiter="\t" if path.suffix.lower() == ".tsv" else ","
                    )
                    require(bool(next(rows, [])), f"表格无表头: {item['id']}")

    if table_dir.is_dir():
        require(
            declared_tables
            == {
                p.relative_to(package).as_posix()
                for p in table_dir.iterdir()
                if p.is_file()
            },
            "论文表格实体与清单不一致",
        )

    external_paths = set()
    for item in manifest["external_data"]:
        checked_file(package, item["path"], "User_data")
        external_paths.add(item["path"])
        require(
            all(
                isinstance(item.get(k), str) and item[k].strip()
                for k in ("source", "use", "license")
            ),
            "题外数据缺少来源、用途或分发说明",
        )
    actual_external = {
        p.relative_to(package).as_posix()
        for p in (package / "User_data").rglob("*")
        if p.is_file()
    }
    require(external_paths == actual_external, "User_data实际文件与题外数据清单不一致")
    if not external_paths:
        require(
            not any((package / "User_data").iterdir()), "无题外数据时User_data必须留空"
        )

    errors.extend(scan_privacy(package, manifest.get("private_terms", [])))
    record_path = checked_file(audit_dir, manifest["verification"])
    if record_path:
        record = read_json(record_path)
        require(record.get("clean_run") is True, "缺少从空缓存运行的声明")
        require(
            isinstance(record.get("command"), list)
            and bool(record["command"])
            and all(isinstance(arg, str) for arg in record["command"])
            and bool(record["command"][0].strip()),
            "缺少实际运行命令",
        )
        require(
            bool(record.get("environment", {}).get("python")), "缺少实际Python环境记录"
        )
        require(
            record.get("code_sha256")
            == {name: sha256(path) for name, path in code.items()},
            "代码哈希与运行记录不一致，可能沿用旧日志",
        )
        steps = record["steps"]
        require(
            {step["script"] for step in steps} == functional,
            "运行记录未覆盖全部功能PY或包含未知步骤",
        )
        for step in steps:
            require(
                type(step.get("exit_code")) is int and step["exit_code"] == 0,
                f"功能脚本未成功: {step['script']}",
            )
            checked_file(audit_dir, step["log"])
        for name in ("coverage", "numerical", "visual"):
            check = record.get("checks", {}).get(name, {})
            require(check.get("status") == "passed", f"缺少通过的检查: {name}")
            checked_file(audit_dir, check.get("evidence"))
    return {
        "通过": not errors,
        "错误": errors,
        "需人工复核": sorted(set(warnings)),
        "Python文件数": len(code),
        "已登记图表项数": len(artifact_ids),
        "检查边界": "仅结构、已声明清单、哈希、语法及证据文件一致性；不替代完整实跑、业务数值及图面检查",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    listing = commands.add_parser("inventory", help="只读盘点候选文件")
    listing.add_argument("--project", type=Path, required=True)
    listing.add_argument("--exclude", type=Path, action="append", default=[])
    checking = commands.add_parser("check", help="核查交付目录及清单")
    checking.add_argument("--project", type=Path, required=True)
    checking.add_argument("--package", type=Path, required=True)
    checking.add_argument("--audit-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        project = args.project.resolve(strict=True)
        if not project.is_dir():
            raise ValueError("项目根路径不是目录")
        if args.action == "inventory":
            result = inventory(project, [p.resolve() for p in args.exclude])
            code = 0
        else:
            package = args.package.resolve(strict=True)
            result = check_package(
                project, package, args.audit_dir.resolve(strict=True)
            )
            code = 0 if result["通过"] else 1
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        zipfile.BadZipFile,
        ET.ParseError,
    ) as exc:
        result, code = {"通过": False, "读取或清单格式错误": str(exc)}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
