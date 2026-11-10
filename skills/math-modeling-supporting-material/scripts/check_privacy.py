"""扫描提交文本、图片元数据和办公文件属性中的身份及来源信息。"""

import re
import struct
import xml.etree.ElementTree as ET
import zipfile
import zlib

SOURCE_WORDS = re.compile(
    r"(?i)notebook|ipynb|markdown|latex|(?<![A-Za-z])MD(?![A-Za-z])"
)
PRIVATE_PATHS = re.compile(
    r"(?i)[A-Z]:[\\/]+(?:Users|Documents and Settings)[\\/]|/(?:Users|home)/|\.skillshub|\.codex[\\/]|\.agents[\\/]"
)
MAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TEXT_TYPES = {
    ".py",
    ".txt",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".lock",
    ".svg",
    ".md",
    ".log",
}


def png_metadata(path):
    with path.open("rb") as stream:
        if stream.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("PNG文件头错误")
        while True:
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError("PNG截断")
            size, kind = struct.unpack(">I4s", header)
            if kind in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
                if size > 4 * 1024 * 1024:
                    raise ValueError("元数据过大，需单独检查")
                content = stream.read(size)
                if kind == b"zTXt":
                    keyword, body = content.split(b"\0", 1)
                    content = keyword + b" " + zlib.decompress(body[1:])
                elif kind == b"iTXt":
                    keyword, body = content.split(b"\0", 1)
                    flag = body[0]
                    body = body[2:].split(b"\0", 2)[2]
                    content = keyword + b" " + (zlib.decompress(body) if flag else body)
                yield kind.decode("ascii"), content.decode("utf-8", errors="replace")
                if kind == b"eXIf":
                    yield "EXIF宽字符", content.decode("utf-16-le", errors="ignore")
            else:
                stream.seek(size, 1)
            if len(stream.read(4)) != 4:
                raise ValueError("PNG校验段截断")
            if kind == b"IEND":
                break


def scan_privacy(package, private_terms=()):
    issues = []

    def inspect(location, text):
        matches = []
        if SOURCE_WORDS.search(text):
            matches.append("制作来源字眼")
        if PRIVATE_PATHS.search(text):
            matches.append("个人目录")
        if MAIL.search(text):
            matches.append("邮箱")
        normalized = text.casefold().replace("\\", "/")
        if any(
            term and term.casefold().replace("\\", "/") in normalized
            for term in private_terms
        ):
            matches.append("已知个人信息")
        if matches:
            issues.append(f"{location}: {', '.join(matches)}")

    for path in package.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(package).as_posix()
        if not path.resolve().is_relative_to(package.resolve()):
            issues.append(f"{relative}: 包外连接")
            continue
        inspect(relative, relative)
        try:
            if path.suffix.lower() in TEXT_TYPES:
                inspect(relative, path.read_text(encoding="utf-8-sig"))
            elif path.suffix.lower() in {".xlsx", ".docx"}:
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if name.endswith((".xml", ".rels")):
                            raw = archive.read(name)
                            parser = ET.XMLParser(
                                target=ET.TreeBuilder(insert_comments=True)
                            )
                            root = ET.fromstring(raw, parser=parser)
                            # 检查内容、批注及属性值，格式标签不是用户身份信息。
                            values = list(root.itertext())
                            values.extend(
                                value
                                for node in root.iter()
                                for value in node.attrib.values()
                            )
                            inspect(relative + ":" + name, "\n".join(values))
                            if name == "docProps/core.xml":
                                for node in root.iter():
                                    if (
                                        isinstance(node.tag, str)
                                        and node.tag.rsplit("}", 1)[-1]
                                        in {"creator", "lastModifiedBy"}
                                        and (node.text or "").strip()
                                        and node.text.strip().casefold() != "openpyxl"
                                    ):
                                        issues.append(f"{relative}: 非空作者属性")
            elif path.suffix.lower() == ".png":
                for kind, text in png_metadata(path):
                    inspect(relative + ":" + kind, text)
        except (
            OSError,
            ValueError,
            IndexError,
            UnicodeError,
            zipfile.BadZipFile,
            zlib.error,
            ET.ParseError,
        ) as exc:
            issues.append(f"{relative}: 隐私检查无法读取: {exc}")
    return issues
