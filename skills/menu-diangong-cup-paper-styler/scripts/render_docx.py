from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": WORD_NS, "r": REL_NS}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ORDERED_LIST_RE = re.compile(r"^\s*(?:\d+[.)]|\[\d+\])\s+")
FIGURE_CAPTION_RE = re.compile(r"^\s*图\s*\d+(?:\s*[-—–]\s*\d+)?(?:\s+|$)")
TABLE_CAPTION_RE = re.compile(r"^\s*表\s*\d+(?:\s*[-—–]\s*\d+)?(?:\s+|$)")
KEYWORDS_RE = re.compile(r"^\s*(?:\*\*)?\s*关键词\s*[：:]\s*(.*?)(?:\s*\*\*)?\s*$")

TOP_LEVEL_SECTIONS = {
    "摘要",
    "问题重述",
    "问题分析",
    "模型假设",
    "符号说明",
    "模型假设与符号说明",
    "数据预处理",
    "模型建立与求解",
    "模型分析检验",
    "模型检验与分析",
    "模型评价与推广",
    "参考文献",
    "附录",
}

ET.register_namespace("w", WORD_NS)
ET.register_namespace("r", REL_NS)


@dataclass
class PaperParts:
    title: str
    abstract_blocks: list[str]
    keywords: str
    body_markdown: str


def w_tag(name: str) -> str:
    return f"{{{WORD_NS}}}{name}"


def split_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        stripped = line.strip()
        fence_match = re.match(r"^(```|~~~)", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                if current:
                    blocks.append("\n".join(current))
                    current = []
                in_fence = True
                fence_marker = marker
                current.append(line)
                continue
            current.append(line)
            if marker == fence_marker:
                in_fence = False
                fence_marker = ""
                blocks.append("\n".join(current))
                current = []
            continue

        if in_fence:
            current.append(line)
            continue

        if not stripped:
            if current:
                blocks.append("\n".join(current))
                current = []
            blocks.append("")
            continue

        current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


def collapse_blank_blocks(blocks: list[str]) -> list[str]:
    collapsed: list[str] = []
    for block in blocks:
        if block == "":
            if not collapsed or collapsed[-1] == "":
                continue
        collapsed.append(block)

    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return collapsed


def join_blocks(blocks: list[str]) -> str:
    normalized = collapse_blank_blocks(blocks)
    if not normalized:
        return ""
    return "\n\n".join(normalized).rstrip() + "\n"


def is_passthrough_block(block: str) -> bool:
    stripped = block.strip()
    if not stripped:
        return True
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return True
    if stripped.startswith(">"):
        return True
    if stripped.startswith("![]") or stripped.startswith("!["):
        return True
    if "\n|" in block or stripped.startswith("|"):
        return True
    if stripped.startswith("- ") or stripped.startswith("* "):
        return True
    if ORDERED_LIST_RE.match(stripped):
        return True
    return False


def normalize_heading_block(block: str) -> str:
    stripped = block.strip()
    heading_match = HEADING_RE.match(stripped)
    if not heading_match:
        return block
    level = len(heading_match.group(1))
    title = heading_match.group(2).strip()
    return f"{'#' * level} {title}"


def strip_simple_markdown(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"!\[[^\]]*]\([^)]+\)", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "")
    cleaned = cleaned.replace("`", "")
    return cleaned.strip()


def extract_paper_parts(text: str, fallback_title: str) -> PaperParts:
    title = ""
    abstract_blocks: list[str] = []
    body_blocks: list[str] = []
    in_abstract = False
    keywords = ""
    seen_abstract = False

    for block in split_blocks(text):
        if block == "":
            if in_abstract:
                abstract_blocks.append("")
            elif body_blocks:
                body_blocks.append("")
            continue

        stripped = block.strip().lstrip("\ufeff")
        single_line = "\n" not in block
        heading_match = HEADING_RE.match(stripped)
        block_title = heading_match.group(2).strip() if heading_match else stripped

        if not title:
            if heading_match and len(heading_match.group(1)) == 1 and block_title not in TOP_LEVEL_SECTIONS:
                title = block_title
                continue
            if single_line and block_title not in TOP_LEVEL_SECTIONS and not KEYWORDS_RE.match(stripped):
                title = strip_simple_markdown(block_title)
                continue

        if (heading_match and block_title == "摘要") or (single_line and stripped == "摘要"):
            in_abstract = True
            seen_abstract = True
            continue

        keyword_match = KEYWORDS_RE.match(stripped)
        if keyword_match:
            keywords = strip_simple_markdown(keyword_match.group(1))
            in_abstract = False
            continue

        if in_abstract:
            abstract_blocks.append(strip_simple_markdown(block))
            continue

        if not seen_abstract and not keywords and not body_blocks and title:
            # Allow drafts that omit an explicit 摘要 heading. Treat content before 关键词 as abstract.
            abstract_blocks.append(strip_simple_markdown(block))
            continue

        body_blocks.append(normalize_heading_block(block))

    title = title or fallback_title
    abstract_blocks = collapse_blank_blocks(abstract_blocks)
    body_markdown = join_blocks(body_blocks)
    return PaperParts(title=title, abstract_blocks=abstract_blocks, keywords=keywords, body_markdown=body_markdown)


def run_pandoc(
    input_md: Path,
    output_docx: Path,
    template_docx: Path,
    resource_path: Path,
) -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is not installed or not on PATH.")

    command = [
        pandoc,
        "--from",
        "markdown+raw_attribute",
        "--reference-doc",
        str(template_docx),
        "--resource-path",
        str(resource_path),
        "--output",
        str(output_docx),
        str(input_md),
    ]
    subprocess.run(command, check=True)


def ensure_child(parent: ET.Element, tag: str, attrib: dict[str, str] | None = None) -> ET.Element:
    child = parent.find(tag, NS)
    if child is None:
        child = ET.SubElement(parent, w_tag(tag.split(":", 1)[1]), attrib or {})
    elif attrib is not None:
        child.attrib.clear()
        child.attrib.update(attrib)
    return child


def remove_child(parent: ET.Element, tag: str) -> None:
    child = parent.find(tag, NS)
    if child is not None:
        parent.remove(child)


def find_style(styles_root: ET.Element, style_id: str, style_type: str) -> ET.Element | None:
    for style in styles_root.findall("w:style", NS):
        if (
            style.get(f"{{{WORD_NS}}}styleId") == style_id
            and style.get(f"{{{WORD_NS}}}type") == style_type
        ):
            return style
    return None


def clone_element(element: ET.Element) -> ET.Element:
    return deepcopy(element)


def get_relationship_id(
    rels_root: ET.Element,
    target: str,
    rel_type_suffix: str,
) -> str | None:
    for rel in rels_root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        if rel.get("Target") == target and rel.get("Type", "").endswith(rel_type_suffix):
            return rel.get("Id")
    return None


def get_style_name(style: ET.Element) -> str:
    name = style.find("w:name", NS)
    if name is None:
        return ""
    return name.get(f"{{{WORD_NS}}}val", "")


def get_style_aliases(style: ET.Element) -> str:
    aliases = style.find("w:aliases", NS)
    if aliases is None:
        return ""
    return aliases.get(f"{{{WORD_NS}}}val", "")


def create_text_run(
    text: str,
    *,
    size: int | None = None,
    bold: bool | None = None,
    east_asia_font: str | None = None,
) -> ET.Element:
    run = ET.Element(w_tag("r"))
    if size is not None or bold is not None or east_asia_font is not None:
        rpr = ET.SubElement(run, w_tag("rPr"))
        if east_asia_font is not None:
            ET.SubElement(
                rpr,
                w_tag("rFonts"),
                {
                    f"{{{WORD_NS}}}ascii": "Times New Roman",
                    f"{{{WORD_NS}}}hAnsi": "Times New Roman",
                    f"{{{WORD_NS}}}eastAsia": east_asia_font,
                    f"{{{WORD_NS}}}cs": "Times New Roman",
                },
            )
        if size is not None:
            ET.SubElement(rpr, w_tag("sz"), {f"{{{WORD_NS}}}val": str(size)})
            ET.SubElement(rpr, w_tag("szCs"), {f"{{{WORD_NS}}}val": str(size)})
        if bold is not None:
            val = "1" if bold else "0"
            ET.SubElement(rpr, w_tag("b"), {f"{{{WORD_NS}}}val": val})
            ET.SubElement(rpr, w_tag("bCs"), {f"{{{WORD_NS}}}val": val})
    text_node = ET.SubElement(run, w_tag("t"))
    if text.startswith(" ") or text.endswith(" "):
        text_node.set(f"{{{XML_NS}}}space", "preserve")
    text_node.text = text
    return run


def create_paragraph(
    text: str = "",
    *,
    style_id: str | None = None,
    align: str | None = None,
    size: int | None = None,
    bold: bool | None = None,
    east_asia_font: str | None = None,
    first_line_chars: int | None = None,
    first_line: int | None = None,
    spacing_before: int | None = None,
    spacing_after: int | None = None,
) -> ET.Element:
    paragraph = ET.Element(w_tag("p"))
    if (
        style_id
        or align
        or first_line_chars is not None
        or first_line is not None
        or spacing_before is not None
        or spacing_after is not None
    ):
        ppr = ET.SubElement(paragraph, w_tag("pPr"))
        if style_id:
            ET.SubElement(ppr, w_tag("pStyle"), {f"{{{WORD_NS}}}val": style_id})
        if align:
            ET.SubElement(ppr, w_tag("jc"), {f"{{{WORD_NS}}}val": align})
        if first_line_chars is not None or first_line is not None:
            ind_attr: dict[str, str] = {}
            if first_line_chars is not None:
                ind_attr[f"{{{WORD_NS}}}firstLineChars"] = str(first_line_chars)
            if first_line is not None:
                ind_attr[f"{{{WORD_NS}}}firstLine"] = str(first_line)
            ET.SubElement(ppr, w_tag("ind"), ind_attr)
        if spacing_before is not None or spacing_after is not None:
            spacing_attr: dict[str, str] = {}
            if spacing_before is not None:
                spacing_attr[f"{{{WORD_NS}}}before"] = str(spacing_before)
            if spacing_after is not None:
                spacing_attr[f"{{{WORD_NS}}}after"] = str(spacing_after)
            ET.SubElement(ppr, w_tag("spacing"), spacing_attr)
    if text:
        paragraph.append(
            create_text_run(
                text,
                size=size,
                bold=bold,
                east_asia_font=east_asia_font,
            )
        )
    return paragraph


def build_toc_field_paragraph() -> ET.Element:
    paragraph = ET.Element(w_tag("p"))
    run_begin = ET.SubElement(paragraph, w_tag("r"))
    ET.SubElement(
        run_begin,
        w_tag("fldChar"),
        {
            f"{{{WORD_NS}}}fldCharType": "begin",
            f"{{{WORD_NS}}}dirty": "true",
        },
    )

    run_instr = ET.SubElement(paragraph, w_tag("r"))
    instr = ET.SubElement(run_instr, w_tag("instrText"))
    instr.set(f"{{{XML_NS}}}space", "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '

    run_sep = ET.SubElement(paragraph, w_tag("r"))
    ET.SubElement(run_sep, w_tag("fldChar"), {f"{{{WORD_NS}}}fldCharType": "separate"})

    placeholder = create_text_run("打开 Word/WPS 后更新目录", size=21, bold=False)
    paragraph.append(placeholder)

    run_end = ET.SubElement(paragraph, w_tag("r"))
    ET.SubElement(run_end, w_tag("fldChar"), {f"{{{WORD_NS}}}fldCharType": "end"})
    return paragraph


def make_section_break(
    footer_rel_id: str | None,
    *,
    start_page_number: int | None = None,
) -> ET.Element:
    sect_pr = ET.Element(w_tag("sectPr"))
    if footer_rel_id:
        ET.SubElement(
            sect_pr,
            w_tag("footerReference"),
            {
                f"{{{WORD_NS}}}type": "default",
                f"{{{REL_NS}}}id": footer_rel_id,
            },
        )
    ET.SubElement(sect_pr, w_tag("type"), {f"{{{WORD_NS}}}val": "nextPage"})
    ET.SubElement(
        sect_pr,
        w_tag("pgSz"),
        {
            f"{{{WORD_NS}}}w": "11906",
            f"{{{WORD_NS}}}h": "16838",
        },
    )
    ET.SubElement(
        sect_pr,
        w_tag("pgMar"),
        {
            f"{{{WORD_NS}}}top": "1134",
            f"{{{WORD_NS}}}right": "1418",
            f"{{{WORD_NS}}}bottom": "1134",
            f"{{{WORD_NS}}}left": "1418",
            f"{{{WORD_NS}}}header": "851",
            f"{{{WORD_NS}}}footer": "992",
            f"{{{WORD_NS}}}gutter": "0",
        },
    )
    ET.SubElement(sect_pr, w_tag("cols"), {f"{{{WORD_NS}}}space": "720"})
    ET.SubElement(
        sect_pr,
        w_tag("docGrid"),
        {
            f"{{{WORD_NS}}}type": "lines",
            f"{{{WORD_NS}}}linePitch": "312",
        },
    )
    if start_page_number is not None:
        ET.SubElement(
            sect_pr,
            w_tag("pgNumType"),
            {f"{{{WORD_NS}}}start": str(start_page_number)},
        )
    return sect_pr


def build_section_break_paragraph(sect_pr: ET.Element) -> ET.Element:
    paragraph = ET.Element(w_tag("p"))
    ppr = ET.SubElement(paragraph, w_tag("pPr"))
    ppr.append(sect_pr)
    return paragraph


def set_update_fields(settings_root: ET.Element) -> None:
    update = settings_root.find("w:updateFields", NS)
    if update is None:
        update = ET.SubElement(settings_root, w_tag("updateFields"))
    update.set(f"{{{WORD_NS}}}val", "true")


def ensure_paragraph_style(
    styles_root: ET.Element,
    *,
    style_id: str,
    name: str,
    based_on: str = "a",
    next_style: str = "a",
    outline_level: int | None = None,
    size: int | None = None,
    bold: bool | None = None,
    east_asia_font: str | None = None,
    spacing_before: int | None = None,
    spacing_after: int | None = None,
    alignment: str | None = None,
    first_line_chars: int | None = None,
    first_line: int | None = None,
    aliases: str | None = None,
    ui_priority: int | None = None,
    quick_format: bool = True,
    font_color: str | None = None,
) -> None:
    style = find_style(styles_root, style_id, "paragraph")
    if style is None:
        style = ET.SubElement(
            styles_root,
            w_tag("style"),
            {
                f"{{{WORD_NS}}}type": "paragraph",
                f"{{{WORD_NS}}}styleId": style_id,
                f"{{{WORD_NS}}}customStyle": "1",
            },
        )

    ensure_child(style, "w:name", {f"{{{WORD_NS}}}val": name})
    if aliases:
        ensure_child(style, "w:aliases", {f"{{{WORD_NS}}}val": aliases})
    ensure_child(style, "w:basedOn", {f"{{{WORD_NS}}}val": based_on})
    ensure_child(style, "w:next", {f"{{{WORD_NS}}}val": next_style})
    if ui_priority is not None:
        ensure_child(style, "w:uiPriority", {f"{{{WORD_NS}}}val": str(ui_priority)})
    if quick_format:
        ensure_child(style, "w:qFormat")
        ensure_child(style, "w:unhideWhenUsed")

    ppr = ensure_child(style, "w:pPr")
    if spacing_before is not None or spacing_after is not None:
        attrs: dict[str, str] = {}
        if spacing_before is not None:
            attrs[f"{{{WORD_NS}}}before"] = str(spacing_before)
        if spacing_after is not None:
            attrs[f"{{{WORD_NS}}}after"] = str(spacing_after)
        ensure_child(ppr, "w:spacing", attrs)
    if alignment is not None:
        ensure_child(ppr, "w:jc", {f"{{{WORD_NS}}}val": alignment})
    if first_line_chars is not None or first_line is not None:
        ind_attr: dict[str, str] = {}
        if first_line_chars is not None:
            ind_attr[f"{{{WORD_NS}}}firstLineChars"] = str(first_line_chars)
        if first_line is not None:
            ind_attr[f"{{{WORD_NS}}}firstLine"] = str(first_line)
        ensure_child(ppr, "w:ind", ind_attr)
    if outline_level is not None:
        ensure_child(ppr, "w:outlineLvl", {f"{{{WORD_NS}}}val": str(outline_level)})

    rpr = ensure_child(style, "w:rPr")
    if east_asia_font is not None:
        ensure_child(
            rpr,
            "w:rFonts",
            {
                f"{{{WORD_NS}}}ascii": "Times New Roman",
                f"{{{WORD_NS}}}hAnsi": "Times New Roman",
                f"{{{WORD_NS}}}eastAsia": east_asia_font,
                f"{{{WORD_NS}}}cs": "Times New Roman",
            },
        )
    if size is not None:
        ensure_child(rpr, "w:sz", {f"{{{WORD_NS}}}val": str(size)})
        ensure_child(rpr, "w:szCs", {f"{{{WORD_NS}}}val": str(size)})
    if bold is not None:
        val = "1" if bold else "0"
        ensure_child(rpr, "w:b", {f"{{{WORD_NS}}}val": val})
        ensure_child(rpr, "w:bCs", {f"{{{WORD_NS}}}val": val})
    if font_color is not None:
        ensure_child(rpr, "w:color", {f"{{{WORD_NS}}}val": font_color})


def ensure_table_style(
    styles_root: ET.Element,
    *,
    style_id: str,
    name: str,
    ui_priority: int | None = None,
) -> None:
    style = find_style(styles_root, style_id, "table")
    if style is None:
        style = ET.SubElement(
            styles_root,
            w_tag("style"),
            {
                f"{{{WORD_NS}}}type": "table",
                f"{{{WORD_NS}}}styleId": style_id,
                f"{{{WORD_NS}}}customStyle": "1",
            },
        )

    ensure_child(style, "w:name", {f"{{{WORD_NS}}}val": name})
    ensure_child(style, "w:basedOn", {f"{{{WORD_NS}}}val": "TableNormal"})
    if ui_priority is not None:
        ensure_child(style, "w:uiPriority", {f"{{{WORD_NS}}}val": str(ui_priority)})
    ensure_child(style, "w:qFormat")
    ensure_child(style, "w:unhideWhenUsed")

    tbl_pr = ensure_child(style, "w:tblPr")
    ensure_child(
        tbl_pr,
        "w:tblCellMar",
    )
    rpr = ensure_child(style, "w:rPr")
    ensure_child(
        rpr,
        "w:rFonts",
        {
            f"{{{WORD_NS}}}ascii": "Times New Roman",
            f"{{{WORD_NS}}}hAnsi": "Times New Roman",
            f"{{{WORD_NS}}}eastAsia": "宋体",
            f"{{{WORD_NS}}}cs": "Times New Roman",
        },
    )
    ensure_child(rpr, "w:sz", {f"{{{WORD_NS}}}val": "24"})
    ensure_child(rpr, "w:szCs", {f"{{{WORD_NS}}}val": "24"})


def demote_style(style: ET.Element) -> None:
    remove_child(style, "w:qFormat")
    remove_child(style, "w:unhideWhenUsed")
    ensure_child(style, "w:uiPriority", {f"{{{WORD_NS}}}val": "99"})


def ensure_missing_styles(styles_root: ET.Element) -> None:
    ensure_paragraph_style(
        styles_root,
        style_id="a",
        name="Normal",
        size=24,
        bold=False,
        east_asia_font="宋体",
        alignment="both",
        first_line_chars=200,
        first_line=420,
        ui_priority=1,
        quick_format=False,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="1",
        name="标题 1",
        outline_level=0,
        size=28,
        bold=False,
        east_asia_font="黑体",
        spacing_before=120,
        spacing_after=120,
        alignment="center",
        first_line_chars=0,
        first_line=0,
        aliases="heading 1,Heading 1",
        ui_priority=9,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="BodyText",
        name="正文",
        size=24,
        bold=False,
        east_asia_font="宋体",
        alignment="both",
        first_line_chars=200,
        first_line=420,
        ui_priority=1,
        quick_format=False,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="FirstParagraph",
        name="First Paragraph",
        size=24,
        bold=False,
        east_asia_font="宋体",
        alignment="both",
        first_line_chars=200,
        first_line=420,
        ui_priority=22,
        quick_format=False,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="2",
        name="标题 2",
        outline_level=1,
        size=24,
        bold=False,
        east_asia_font="黑体",
        spacing_before=120,
        spacing_after=120,
        alignment="left",
        first_line_chars=0,
        first_line=0,
        aliases="Heading 2,heading 2",
        ui_priority=10,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="3",
        name="标题 3",
        outline_level=2,
        size=24,
        bold=False,
        east_asia_font="黑体",
        spacing_before=120,
        spacing_after=120,
        alignment="left",
        first_line_chars=0,
        first_line=0,
        aliases="Heading 3,heading 3",
        ui_priority=11,
        font_color="000000",
    )
    ensure_paragraph_style(
        styles_root,
        style_id="ReferenceText",
        name="参考文献",
        size=24,
        bold=False,
        east_asia_font="宋体",
        alignment="left",
        first_line_chars=0,
        first_line=0,
        ui_priority=12,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="FigureCaption",
        name="图注",
        size=21,
        bold=True,
        east_asia_font="宋体",
        alignment="center",
        first_line_chars=0,
        first_line=0,
        spacing_before=0,
        spacing_after=120,
        ui_priority=13,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="TableCaption",
        name="表注",
        size=21,
        bold=True,
        east_asia_font="宋体",
        alignment="center",
        first_line_chars=0,
        first_line=0,
        spacing_before=120,
        spacing_after=0,
        ui_priority=14,
    )
    ensure_paragraph_style(
        styles_root,
        style_id="ImageParagraph",
        name="图",
        size=24,
        bold=False,
        east_asia_font="宋体",
        alignment="center",
        first_line_chars=0,
        first_line=0,
        ui_priority=15,
    )
    ensure_table_style(
        styles_root,
        style_id="PaperTable",
        name="表格",
        ui_priority=16,
    )


def get_paragraph_style_id(paragraph: ET.Element) -> str:
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        return ""
    pstyle = ppr.find("w:pStyle", NS)
    if pstyle is None:
        return ""
    return pstyle.get(f"{{{WORD_NS}}}val", "")


def get_paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def get_used_paragraph_style_ids(document_root: ET.Element) -> set[str]:
    used: set[str] = set()
    for paragraph in document_root.findall(".//w:body/w:p", NS):
        style_id = get_paragraph_style_id(paragraph)
        if style_id:
            used.add(style_id)
    return used


def get_used_table_style_ids(document_root: ET.Element) -> set[str]:
    used: set[str] = set()
    for tbl in document_root.findall(".//w:tbl", NS):
        tbl_pr = tbl.find("w:tblPr", NS)
        if tbl_pr is None:
            continue
        tbl_style = tbl_pr.find("w:tblStyle", NS)
        if tbl_style is None:
            continue
        style_id = tbl_style.get(f"{{{WORD_NS}}}val", "")
        if style_id:
            used.add(style_id)
    return used


def remap_heading_style_ids(document_root: ET.Element) -> None:
    mapping = {
        "Heading2": "2",
        "Heading3": "3",
    }
    for paragraph in document_root.findall(".//w:p", NS):
        ppr = paragraph.find("w:pPr", NS)
        if ppr is None:
            continue
        pstyle = ppr.find("w:pStyle", NS)
        if pstyle is None:
            continue
        current = pstyle.get(f"{{{WORD_NS}}}val", "")
        if current in mapping:
            pstyle.set(f"{{{WORD_NS}}}val", mapping[current])


def remap_body_style_ids(document_root: ET.Element) -> None:
    mapping = {
        "FirstParagraph": "BodyText",
        "11": "BodyText",
    }
    for paragraph in document_root.findall(".//w:p", NS):
        ppr = paragraph.find("w:pPr", NS)
        if ppr is None:
            continue
        pstyle = ppr.find("w:pStyle", NS)
        if pstyle is None:
            continue
        current = pstyle.get(f"{{{WORD_NS}}}val", "")
        if current in mapping:
            pstyle.set(f"{{{WORD_NS}}}val", mapping[current])


def normalize_gallery_styles(styles_root: ET.Element, document_root: ET.Element) -> None:
    used_paragraph_ids = get_used_paragraph_style_ids(document_root)
    used_table_ids = get_used_table_style_ids(document_root)
    allowed_quick_styles: set[str] = set()

    def paragraph_candidates(match: callable) -> list[str]:
        result: list[str] = []
        for style in styles_root.findall("w:style", NS):
            if style.get(f"{{{WORD_NS}}}type") != "paragraph":
                continue
            sid = style.get(f"{{{WORD_NS}}}styleId", "")
            if match(style, sid):
                result.append(sid)
        return result

    def table_candidates(match: callable) -> list[str]:
        result: list[str] = []
        for style in styles_root.findall("w:style", NS):
            if style.get(f"{{{WORD_NS}}}type") != "table":
                continue
            sid = style.get(f"{{{WORD_NS}}}styleId", "")
            if match(style, sid):
                result.append(sid)
        return result

    def choose_preferred(candidates: list[str], used: set[str], fallback: str) -> str:
        for sid in candidates:
            if sid in used:
                return sid
        if fallback in candidates:
            return fallback
        return candidates[0] if candidates else fallback

    def normalize_paragraph_group(
        candidates: list[str],
        used: set[str],
        fallback: str,
        params: dict[str, object],
    ) -> None:
        if not candidates:
            return
        preferred = choose_preferred(candidates, used, fallback)
        allowed_quick_styles.add(preferred)
        ensure_paragraph_style(styles_root, style_id=preferred, **params)
        for sid in candidates:
            if sid == preferred:
                continue
            style = find_style(styles_root, sid, "paragraph")
            if style is not None:
                demote_style(style)

    def normalize_table_group(
        candidates: list[str],
        used: set[str],
        fallback: str,
        name: str,
        ui_priority: int,
    ) -> None:
        if not candidates:
            return
        preferred = choose_preferred(candidates, used, fallback)
        allowed_quick_styles.add(preferred)
        ensure_table_style(styles_root, style_id=preferred, name=name, ui_priority=ui_priority)
        for sid in candidates:
            if sid == preferred:
                continue
            style = find_style(styles_root, sid, "table")
            if style is not None:
                demote_style(style)

    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: get_style_name(style) in {"正文", "正文文本1", "Body Text", "First Paragraph", "Normal"}
            or sid in {"BodyText", "FirstParagraph", "11", "a"}
        ),
        used_paragraph_ids,
        "BodyText",
        {
            "name": "正文",
            "based_on": "a",
            "next_style": "BodyText",
            "size": 24,
            "bold": False,
            "east_asia_font": "宋体",
            "alignment": "both",
            "first_line_chars": 200,
            "first_line": 420,
            "ui_priority": 1,
        },
    )
    allowed_quick_styles.add("1")
    ensure_paragraph_style(
        styles_root,
        style_id="1",
        name="标题 1",
        based_on="a",
        next_style="BodyText",
        outline_level=0,
        size=28,
        bold=False,
        east_asia_font="黑体",
        spacing_before=120,
        spacing_after=120,
        alignment="center",
        first_line_chars=0,
        first_line=0,
        aliases="heading 1,Heading 1",
        ui_priority=9,
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: "Heading 2" in get_style_aliases(style)
            or get_style_name(style) in {"Heading 2", "heading 2", "标题 2", "标题 21"}
            or sid in {"2", "21", "Heading2"}
        ),
        used_paragraph_ids,
        "2",
        {
            "name": "标题 2",
            "based_on": "a",
            "next_style": "a",
            "outline_level": 1,
            "size": 24,
            "bold": False,
            "east_asia_font": "黑体",
            "spacing_before": 120,
            "spacing_after": 120,
            "alignment": "left",
            "first_line_chars": 0,
            "first_line": 0,
            "aliases": "Heading 2,heading 2",
            "ui_priority": 10,
        },
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: "Heading 3" in get_style_aliases(style)
            or get_style_name(style) in {"Heading 3", "heading 3", "标题 3", "标题 31"}
            or sid in {"3", "310", "Heading3"}
        ),
        used_paragraph_ids,
        "3",
        {
            "name": "标题 3",
            "based_on": "a",
            "next_style": "a",
            "outline_level": 2,
            "size": 24,
            "bold": False,
            "east_asia_font": "黑体",
            "spacing_before": 120,
            "spacing_after": 120,
            "alignment": "left",
            "first_line_chars": 0,
            "first_line": 0,
            "aliases": "Heading 3,heading 3",
            "ui_priority": 11,
            "font_color": "000000",
        },
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: get_style_name(style) == "参考文献" or sid == "ReferenceText"
        ),
        used_paragraph_ids,
        "ReferenceText",
        {
            "name": "参考文献",
            "based_on": "a",
            "next_style": "a",
            "size": 24,
            "bold": False,
            "east_asia_font": "宋体",
            "alignment": "left",
            "first_line_chars": 0,
            "first_line": 0,
            "ui_priority": 12,
        },
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: get_style_name(style) == "图注" or sid in {"FigureCaption", "ab", "ImageCaption"}
        ),
        used_paragraph_ids,
        "FigureCaption",
        {
            "name": "图注",
            "based_on": "a",
            "next_style": "a",
            "size": 21,
            "bold": True,
            "east_asia_font": "宋体",
            "alignment": "center",
            "first_line_chars": 0,
            "first_line": 0,
            "spacing_before": 0,
            "spacing_after": 120,
            "ui_priority": 13,
        },
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: get_style_name(style) == "表注" or sid in {"TableCaption", "ac"}
        ),
        used_paragraph_ids,
        "TableCaption",
        {
            "name": "表注",
            "based_on": "a",
            "next_style": "a",
            "size": 21,
            "bold": True,
            "east_asia_font": "宋体",
            "alignment": "center",
            "first_line_chars": 0,
            "first_line": 0,
            "spacing_before": 120,
            "spacing_after": 0,
            "ui_priority": 14,
        },
    )
    normalize_paragraph_group(
        paragraph_candidates(
            lambda style, sid: get_style_name(style) == "图" or sid in {"ImageParagraph", "CaptionedFigure"}
        ),
        used_paragraph_ids,
        "ImageParagraph",
        {
            "name": "图",
            "based_on": "a",
            "next_style": "a",
            "size": 24,
            "bold": False,
            "east_asia_font": "宋体",
            "alignment": "center",
            "first_line_chars": 0,
            "first_line": 0,
            "ui_priority": 15,
        },
    )
    normalize_table_group(
        table_candidates(lambda style, sid: get_style_name(style) == "表格" or sid in {"PaperTable", "Table"}),
        used_table_ids,
        "PaperTable",
        "表格",
        16,
    )

    for style in styles_root.findall("w:style", NS):
        sid = style.get(f"{{{WORD_NS}}}styleId", "")
        if sid in allowed_quick_styles:
            continue
        if style.find("w:qFormat", NS) is not None or style.find("w:unhideWhenUsed", NS) is not None:
            demote_style(style)


def is_caption_text(text: str, pattern: re.Pattern[str]) -> bool:
    if not pattern.match(text):
        return False
    if any(mark in text for mark in ("，", "。", "；", "：", "！", "？")):
        return False
    return True


def apply_run_font_format(
    paragraph: ET.Element,
    *,
    size: int,
    east_asia_font: str,
    bold: bool,
) -> None:
    for run in paragraph.findall("w:r", NS):
        rpr = run.find("w:rPr", NS)
        if rpr is None:
            rpr = ET.SubElement(run, w_tag("rPr"))
        ensure_child(
            rpr,
            "w:rFonts",
            {
                f"{{{WORD_NS}}}ascii": "Times New Roman",
                f"{{{WORD_NS}}}hAnsi": "Times New Roman",
                f"{{{WORD_NS}}}eastAsia": east_asia_font,
                f"{{{WORD_NS}}}cs": "Times New Roman",
            },
        )
        ensure_child(rpr, "w:sz", {f"{{{WORD_NS}}}val": str(size)})
        ensure_child(rpr, "w:szCs", {f"{{{WORD_NS}}}val": str(size)})
        val = "1" if bold else "0"
        ensure_child(rpr, "w:b", {f"{{{WORD_NS}}}val": val})
        ensure_child(rpr, "w:bCs", {f"{{{WORD_NS}}}val": val})


def apply_paragraph_layout(
    paragraph: ET.Element,
    *,
    align: str,
    first_line_chars: int = 0,
    first_line: int = 0,
    spacing_before: int = 0,
    spacing_after: int = 0,
    remove_style: bool = False,
    style_id: str | None = None,
) -> ET.Element:
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        ppr = ET.Element(w_tag("pPr"))
        paragraph.insert(0, ppr)
    if remove_style:
        remove_child(ppr, "w:pStyle")
    if style_id is not None:
        ensure_child(ppr, "w:pStyle", {f"{{{WORD_NS}}}val": style_id})
    ensure_child(ppr, "w:jc", {f"{{{WORD_NS}}}val": align})
    ensure_child(
        ppr,
        "w:ind",
        {
            f"{{{WORD_NS}}}left": "0",
            f"{{{WORD_NS}}}right": "0",
            f"{{{WORD_NS}}}firstLine": str(first_line),
            f"{{{WORD_NS}}}firstLineChars": str(first_line_chars),
        },
    )
    ensure_child(
        ppr,
        "w:spacing",
        {
            f"{{{WORD_NS}}}before": str(spacing_before),
            f"{{{WORD_NS}}}after": str(spacing_after),
        },
    )
    return ppr


def apply_reference_formatting(paragraph: ET.Element) -> None:
    apply_paragraph_layout(
        paragraph,
        align="left",
        first_line_chars=0,
        first_line=0,
        spacing_before=0,
        spacing_after=0,
        style_id="ReferenceText",
    )
    apply_run_font_format(paragraph, size=24, east_asia_font="宋体", bold=False)


def normalize_numbered_paragraph_alignment(document_root: ET.Element) -> None:
    for paragraph in document_root.findall(".//w:p", NS):
        ppr = paragraph.find("w:pPr", NS)
        if ppr is None:
            continue

        numpr = ppr.find("w:numPr", NS)
        if numpr is None:
            continue

        ilvl = numpr.find("w:ilvl", NS)
        try:
            level = int(ilvl.get(f"{{{WORD_NS}}}val", "0")) if ilvl is not None else 0
        except ValueError:
            level = 0

        left = 360 * (level + 1)
        ensure_child(
            ppr,
            "w:ind",
            {
                f"{{{WORD_NS}}}left": str(left),
                f"{{{WORD_NS}}}hanging": "360",
                f"{{{WORD_NS}}}firstLine": "0",
                f"{{{WORD_NS}}}firstLineChars": "0",
            },
        )
        ensure_child(ppr, "w:jc", {f"{{{WORD_NS}}}val": "left"})


def ensure_table_properties(tbl: ET.Element) -> ET.Element:
    tbl_pr = tbl.find("w:tblPr", NS)
    if tbl_pr is None:
        tbl_pr = ET.Element(w_tag("tblPr"))
        tbl.insert(0, tbl_pr)
    return tbl_pr


def rebalance_narrow_table_columns(tbl: ET.Element) -> None:
    tbl_grid = tbl.find("w:tblGrid", NS)
    if tbl_grid is None:
        return

    grid_cols = tbl_grid.findall("w:gridCol", NS)
    if len(grid_cols) < 2:
        return

    widths: list[int] = []
    for grid_col in grid_cols:
        raw = grid_col.get(f"{{{WORD_NS}}}w")
        try:
            widths.append(int(raw) if raw is not None else 0)
        except ValueError:
            widths.append(0)

    total_width = sum(widths)
    if total_width <= 0:
        return

    col_count = len(widths)
    if col_count <= 4:
        min_width = 1440
    elif col_count <= 6:
        min_width = 720
    else:
        return

    if total_width < min_width * col_count:
        min_width = max(360, total_width // col_count)

    adjusted = widths[:]
    for idx, width in enumerate(widths):
        if width >= min_width:
            continue

        needed = min_width - width
        donor_indices = sorted(
            (i for i in range(col_count) if i != idx),
            key=lambda i: adjusted[i],
            reverse=True,
        )

        moved = 0
        for donor in donor_indices:
            spare = adjusted[donor] - min_width
            if spare <= 0:
                continue
            take = min(spare, needed - moved)
            adjusted[donor] -= take
            moved += take
            if moved >= needed:
                break

        adjusted[idx] += moved

    if adjusted == widths:
        return

    for grid_col, width in zip(grid_cols, adjusted):
        grid_col.set(f"{{{WORD_NS}}}w", str(width))

    for row in tbl.findall("w:tr", NS):
        cells = row.findall("w:tc", NS)
        for idx, cell in enumerate(cells[:col_count]):
            tc_pr = cell.find("w:tcPr", NS)
            if tc_pr is None:
                tc_pr = ET.Element(w_tag("tcPr"))
                cell.insert(0, tc_pr)
            ensure_child(
                tc_pr,
                "w:tcW",
                {
                    f"{{{WORD_NS}}}w": str(adjusted[idx]),
                    f"{{{WORD_NS}}}type": "dxa",
                },
            )


def normalize_table_cell_paragraphs(tbl: ET.Element) -> None:
    for row in tbl.findall("w:tr", NS):
        for cell in row.findall("w:tc", NS):
            for para in cell.findall("w:p", NS):
                ppr = apply_paragraph_layout(
                    para,
                    align="center",
                    first_line_chars=0,
                    first_line=0,
                    spacing_before=0,
                    spacing_after=0,
                    style_id="BodyText",
                )
                ensure_child(ppr, "w:keepNext", {f"{{{WORD_NS}}}val": "0"})
                ensure_child(ppr, "w:keepLines", {f"{{{WORD_NS}}}val": "0"})
                apply_run_font_format(para, size=24, east_asia_font="宋体", bold=False)


def configure_table_as_full_grid(tbl: ET.Element) -> None:
    tbl_pr = ensure_table_properties(tbl)
    ensure_child(tbl_pr, "w:tblStyle", {f"{{{WORD_NS}}}val": "PaperTable"})

    tbl_borders = ensure_child(tbl_pr, "w:tblBorders")
    border_attrib = {
        f"{{{WORD_NS}}}val": "single",
        f"{{{WORD_NS}}}sz": "4",
        f"{{{WORD_NS}}}space": "0",
        f"{{{WORD_NS}}}color": "auto",
    }
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        ensure_child(tbl_borders, f"w:{name}", border_attrib)


def configure_table_as_light_grid(tbl: ET.Element) -> None:
    tbl_pr = ensure_table_properties(tbl)
    ensure_child(tbl_pr, "w:tblStyle", {f"{{{WORD_NS}}}val": "PaperTable"})

    tbl_borders = ensure_child(tbl_pr, "w:tblBorders")
    outer_border = {
        f"{{{WORD_NS}}}val": "single",
        f"{{{WORD_NS}}}sz": "4",
        f"{{{WORD_NS}}}space": "0",
        f"{{{WORD_NS}}}color": "BFBFBF",
    }
    inner_border = {
        f"{{{WORD_NS}}}val": "single",
        f"{{{WORD_NS}}}sz": "2",
        f"{{{WORD_NS}}}space": "0",
        f"{{{WORD_NS}}}color": "D9D9D9",
    }
    for name in ("top", "left", "bottom", "right"):
        ensure_child(tbl_borders, f"w:{name}", outer_border)
    for name in ("insideH", "insideV"):
        ensure_child(tbl_borders, f"w:{name}", inner_border)


def configure_table_as_three_line(tbl: ET.Element) -> None:
    tbl_pr = ensure_table_properties(tbl)
    ensure_child(tbl_pr, "w:tblStyle", {f"{{{WORD_NS}}}val": "PaperTable"})

    tbl_borders = ensure_child(tbl_pr, "w:tblBorders")
    # Word border size `w:sz` uses eighths of a point.
    # 12 -> 1.5 pt for the top/bottom rules, 8 -> 1.0 pt for the header rule.
    outer_visible = {
        f"{{{WORD_NS}}}val": "single",
        f"{{{WORD_NS}}}sz": "12",
        f"{{{WORD_NS}}}space": "0",
        f"{{{WORD_NS}}}color": "auto",
    }
    header_visible = {
        f"{{{WORD_NS}}}val": "single",
        f"{{{WORD_NS}}}sz": "8",
        f"{{{WORD_NS}}}space": "0",
        f"{{{WORD_NS}}}color": "auto",
    }
    hidden = {
        f"{{{WORD_NS}}}val": "nil",
    }
    ensure_child(tbl_borders, "w:top", outer_visible)
    ensure_child(tbl_borders, "w:left", hidden)
    ensure_child(tbl_borders, "w:bottom", outer_visible)
    ensure_child(tbl_borders, "w:right", hidden)
    ensure_child(tbl_borders, "w:insideH", hidden)
    ensure_child(tbl_borders, "w:insideV", hidden)

    first_row = tbl.find("w:tr", NS)
    if first_row is not None:
        for cell in first_row.findall("w:tc", NS):
            tc_pr = cell.find("w:tcPr", NS)
            if tc_pr is None:
                tc_pr = ET.Element(w_tag("tcPr"))
                cell.insert(0, tc_pr)
            tc_borders = ensure_child(tc_pr, "w:tcBorders")
            ensure_child(tc_borders, "w:bottom", header_visible)


def apply_caption_formatting(paragraph: ET.Element) -> None:
    text = get_paragraph_text(paragraph)
    if not text:
        return
    is_figure = is_caption_text(text, FIGURE_CAPTION_RE)
    is_table = is_caption_text(text, TABLE_CAPTION_RE)
    if not (is_figure or is_table):
        return

    apply_paragraph_layout(
        paragraph,
        align="center",
        first_line_chars=0,
        first_line=0,
        spacing_before=0 if is_figure else 120,
        spacing_after=120 if is_figure else 0,
        remove_style=True,
        style_id="FigureCaption" if is_figure else "TableCaption",
    )
    apply_run_font_format(paragraph, size=21, east_asia_font="宋体", bold=True)


def apply_image_style(paragraph: ET.Element) -> None:
    if paragraph.find(".//w:drawing", NS) is None and paragraph.find(".//w:pict", NS) is None:
        return
    apply_paragraph_layout(
        paragraph,
        align="center",
        first_line_chars=0,
        first_line=0,
        spacing_before=0,
        spacing_after=0,
        style_id="ImageParagraph",
    )


def patch_docx_layout(docx_path: Path, paper_parts: PaperParts, table_style: str) -> None:
    with ZipFile(docx_path, "r") as source:
        files = {name: source.read(name) for name in source.namelist()}

    styles_root = ET.fromstring(files["word/styles.xml"])
    document_root = ET.fromstring(files["word/document.xml"])
    settings_root = ET.fromstring(files["word/settings.xml"])
    rels_root = ET.fromstring(files["word/_rels/document.xml.rels"])

    ensure_missing_styles(styles_root)
    set_update_fields(settings_root)
    remap_heading_style_ids(document_root)
    remap_body_style_ids(document_root)

    footer_blank_id = get_relationship_id(rels_root, "footer1.xml", "/footer")
    footer_numbered_id = get_relationship_id(rels_root, "footer2.xml", "/footer")

    body = document_root.find("w:body", NS)
    if body is None:
        raise RuntimeError("DOCX body is missing.")

    original_children = list(body)
    final_sectpr = body.find("w:sectPr", NS)
    content_children = [child for child in original_children if child is not final_sectpr]

    body.clear()

    body.append(
        create_paragraph(
            paper_parts.title,
            align="center",
            size=32,
            bold=False,
            east_asia_font="黑体",
        )
    )
    body.append(
        create_paragraph(
            "摘要",
            align="center",
            size=28,
            bold=False,
            east_asia_font="黑体",
        )
    )
    if paper_parts.abstract_blocks:
        for block in paper_parts.abstract_blocks:
            body.append(
                create_paragraph(
                    block,
                    align="both",
                    size=24,
                    bold=False,
                    east_asia_font="宋体",
                    first_line_chars=200,
                    first_line=420,
                )
            )
    else:
        body.append(
            create_paragraph(
                "",
                align="both",
                size=24,
                bold=False,
                east_asia_font="宋体",
                first_line_chars=200,
                first_line=420,
            )
        )

    keyword_text = f"关键词：{paper_parts.keywords}".rstrip()
    keyword_para = create_paragraph(
        keyword_text,
        align="left",
        size=24,
        bold=False,
        east_asia_font="宋体",
        first_line_chars=0,
        first_line=0,
    )
    keyword_ppr = ensure_child(keyword_para, "w:pPr")
    keyword_ppr.append(
        make_section_break(
            footer_blank_id,
        )
    )
    body.append(keyword_para)

    body.append(create_paragraph("目录", align="center", size=28, bold=False))
    body.append(build_toc_field_paragraph())
    body.append(build_section_break_paragraph(make_section_break(footer_blank_id)))

    for child in content_children:
        body.append(clone_element(child))

    if final_sectpr is None:
        final_sectpr = ET.Element(w_tag("sectPr"))
    else:
        final_sectpr = clone_element(final_sectpr)

    for child in list(final_sectpr):
        tag = child.tag
        if tag in {
            w_tag("headerReference"),
            w_tag("footerReference"),
            w_tag("pgNumType"),
            w_tag("type"),
        }:
            final_sectpr.remove(child)

    if footer_numbered_id:
        final_sectpr.insert(
            0,
            ET.Element(
                w_tag("footerReference"),
                {
                    f"{{{WORD_NS}}}type": "default",
                    f"{{{REL_NS}}}id": footer_numbered_id,
                },
            ),
        )
    ET.SubElement(final_sectpr, w_tag("pgNumType"), {f"{{{WORD_NS}}}start": "1"})
    body.append(final_sectpr)

    normalize_numbered_paragraph_alignment(document_root)
    in_references = False
    for paragraph in document_root.findall(".//w:body/w:p", NS):
        apply_image_style(paragraph)
        text = get_paragraph_text(paragraph)
        style_id = get_paragraph_style_id(paragraph)
        if text == "参考文献":
            in_references = True
            continue
        if in_references and style_id == "1":
            in_references = False
        if in_references and text:
            apply_reference_formatting(paragraph)
        apply_caption_formatting(paragraph)

    for tbl in document_root.findall(".//w:tbl", NS):
        rebalance_narrow_table_columns(tbl)
        normalize_table_cell_paragraphs(tbl)
        if table_style == "three-line":
            configure_table_as_three_line(tbl)
        elif table_style == "light-grid":
            configure_table_as_light_grid(tbl)
        else:
            configure_table_as_full_grid(tbl)

    normalize_gallery_styles(styles_root, document_root)

    files["word/styles.xml"] = ET.tostring(styles_root, encoding="utf-8", xml_declaration=True)
    files["word/document.xml"] = ET.tostring(document_root, encoding="utf-8", xml_declaration=True)
    files["word/settings.xml"] = ET.tostring(settings_root, encoding="utf-8", xml_declaration=True)

    temp_docx = docx_path.with_suffix(".tmp.docx")
    with ZipFile(temp_docx, "w", ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)
    temp_docx.replace(docx_path)


def repair_docx_styles(docx_path: Path, table_style: str = "three-line") -> None:
    with ZipFile(docx_path, "r") as source:
        files = {name: source.read(name) for name in source.namelist()}

    styles_root = ET.fromstring(files["word/styles.xml"])
    document_root = ET.fromstring(files["word/document.xml"])
    settings_root = ET.fromstring(files["word/settings.xml"])

    ensure_missing_styles(styles_root)
    set_update_fields(settings_root)
    remap_heading_style_ids(document_root)
    remap_body_style_ids(document_root)
    normalize_numbered_paragraph_alignment(document_root)

    in_references = False
    for paragraph in document_root.findall(".//w:body/w:p", NS):
        apply_image_style(paragraph)
        text = get_paragraph_text(paragraph)
        style_id = get_paragraph_style_id(paragraph)
        if text == "参考文献":
            in_references = True
            continue
        if in_references and style_id == "1":
            in_references = False
        if in_references and text:
            apply_reference_formatting(paragraph)
        apply_caption_formatting(paragraph)

    for tbl in document_root.findall(".//w:tbl", NS):
        rebalance_narrow_table_columns(tbl)
        normalize_table_cell_paragraphs(tbl)
        if table_style == "three-line":
            configure_table_as_three_line(tbl)
        elif table_style == "light-grid":
            configure_table_as_light_grid(tbl)
        else:
            configure_table_as_full_grid(tbl)

    normalize_gallery_styles(styles_root, document_root)

    files["word/styles.xml"] = ET.tostring(styles_root, encoding="utf-8", xml_declaration=True)
    files["word/document.xml"] = ET.tostring(document_root, encoding="utf-8", xml_declaration=True)
    files["word/settings.xml"] = ET.tostring(settings_root, encoding="utf-8", xml_declaration=True)

    temp_docx = docx_path.with_suffix(".tmp.docx")
    with ZipFile(temp_docx, "w", ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)
    temp_docx.replace(docx_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a math-modeling markdown draft into a DOCX that matches the 2026 MathorCup layout."
    )
    parser.add_argument("input_md", type=Path, help="Source markdown file")
    parser.add_argument("output_docx", type=Path, help="Output DOCX path")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "diangong-cup-reference-template.docx",
        help="Reference DOCX template path",
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep the body-only markdown next to the output DOCX",
    )
    parser.add_argument(
        "--table-style",
        choices=("full-grid", "three-line", "light-grid"),
        default="three-line",
        help="Table border style for markdown tables. `three-line` means standard three-line tables with 1.5 pt top/bottom rules and 1.0 pt header rule.",
    )
    args = parser.parse_args()

    input_md = args.input_md.resolve()
    output_docx = args.output_docx.resolve()
    template_docx = args.template.resolve()

    if not input_md.exists():
        raise FileNotFoundError(f"Input markdown not found: {input_md}")
    if not template_docx.exists():
        raise FileNotFoundError(f"Template DOCX not found: {template_docx}")

    source_text = input_md.read_text(encoding="utf-8")
    paper_parts = extract_paper_parts(source_text, fallback_title=input_md.stem)
    body_markdown = paper_parts.body_markdown or "# 正文\n"
    output_docx.parent.mkdir(parents=True, exist_ok=True)

    if args.keep_intermediate:
        intermediate = output_docx.with_suffix(".prepared.md")
        intermediate.write_text(body_markdown, encoding="utf-8")
        run_pandoc(intermediate, output_docx, template_docx, input_md.parent)
    else:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".md",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(body_markdown)
        try:
            run_pandoc(temp_path, output_docx, template_docx, input_md.parent)
        finally:
            temp_path.unlink(missing_ok=True)

    patch_docx_layout(output_docx, paper_parts, args.table_style)
    print(f"Rendered DOCX: {output_docx}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
