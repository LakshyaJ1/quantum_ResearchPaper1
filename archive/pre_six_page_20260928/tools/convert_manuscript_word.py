"""Derive editable Word from compiled IEEE LaTeX, using AUX labels as authority.

This converts representation only. It does not write or rewrite the source paper.
The output requires a full visual review after Microsoft Word PDF export.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
PANDOC = ROOT / "tools/pandoc/pandoc.exe"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
WIDE_START = "WORD-WIDE-START"
WIDE_END = "WORD-WIDE-END"
EQ_MARKER = "WORD-EQUATION-NUMBER:"
TEXT_WIDTH_IN = 516 / 72.27
COL_GAP_IN = 12 / 72.27
COL_WIDTH_IN = (TEXT_WIDTH_IN - COL_GAP_IN) / 2
TOP_IN = (72.27 - 55.7659 + 12 + 18.45703) / 72.27
TEXT_HEIGHT_IN = 672 / 72.27


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def balanced(text: str, start: int) -> tuple[str, int]:
    if text[start] != "{":
        raise ValueError("Expected opening brace")
    depth = 1
    i = start + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError("Unbalanced source braces")


def aux_maps(aux: Path) -> tuple[dict, dict]:
    text = aux.read_text(encoding="utf-8", errors="strict")
    labels = {}
    for match in re.finditer(r"\\newlabel\{([^}]+)\}\s*\{", text):
        outer, _ = balanced(text, match.end() - 1)
        value, _ = balanced(outer, 0)
        value = re.sub(r"\\mbox\s*\{([^}]*)\}", r"\1", value)
        labels[match.group(1)] = value
    cites = dict(re.findall(r"\\bibcite\{([^}]+)\}\{([^}]*)\}", text))
    return labels, cites


def clean_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def expand_inputs(source: Path, root: Path, records: list, active: tuple = ()) -> str:
    source = source.resolve()
    if source in active:
        raise ValueError(f"Recursive LaTeX input: {source}")
    records.append({"path": str(source), "sha256": sha(source)})
    text = clean_comments(source.read_text(encoding="utf-8"))

    def include(match):
        name = match.group(1).strip()
        candidates = [source.parent / name, root / name]
        candidates += [p.with_suffix(".tex") for p in candidates if not p.suffix]
        target = next((p for p in candidates if p.is_file()), None)
        if target is None:
            raise FileNotFoundError(f"Cannot resolve LaTeX input {name} from {source}")
        return expand_inputs(target, root, records, active + (source,))

    return re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", include, text)


def expand_shortstacks(text: str) -> str:
    # \newline stays within a table cell, unlike TeX's outer row separator \\.
    while match := re.search(r"\\shortstack(?:\[[^\]]*\])?\s*\{", text):
        body, end = balanced(text, match.end() - 1)
        replacement = "{" + body.replace(r"\\", r"\newline ") + "}"
        text = text[:match.start()] + replacement + text[end:]
    return text


def plain_cites(keys: str, cites: dict) -> str:
    key_list = [x.strip() for x in keys.split(",")]
    missing = [x for x in key_list if x not in cites]
    if missing:
        raise ValueError(f"Unresolved citation keys in AUX: {missing}")
    numbers = sorted({int(cites[x]) for x in key_list})
    groups = []
    i = 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        if j - i >= 2:
            groups.append(f"[{numbers[i]}]--[{numbers[j]}]")
        else:
            groups.extend(f"[{n}]" for n in numbers[i:j + 1])
        i = j + 1
    return ", ".join(groups)


def stage_source(tex: Path, aux: Path, stage: Path) -> dict:
    import fitz
    stage.mkdir(parents=True, exist_ok=True)
    assets = stage / "assets"
    assets.mkdir(exist_ok=True)
    labels, cites = aux_maps(aux)
    inputs = []
    text = expand_inputs(tex, tex.parent, inputs)
    text = expand_shortstacks(text)
    graphic_dirs = [tex.parent, tex.parent / "figures"]
    for match in re.finditer(r"\\graphicspath\s*\{((?:\{[^}]*\})+)\}", text):
        graphic_dirs += [tex.parent / value for value in re.findall(r"\{([^}]*)\}", match.group(1))]
    section_specs = [(bool(m.group(1)), m.group(2)) for m in re.finditer(r"\\section(\*)?\{([^}]+)\}", text)]
    original_bibkeys = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", text)
    if set(original_bibkeys) != set(cites):
        raise ValueError("AUX bibliography does not match source bibitems; compile the current source first")

    def bibliography(match):
        body = match.group(1)
        items = list(re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", body))
        entries = []
        for i, item in enumerate(items):
            end = items[i + 1].start() if i + 1 < len(items) else len(body)
            entries.append(f"[{cites[item.group(1)]}] " + body[item.end():end].strip())
        return "\\section*{References}\n\n" + "\n\n".join(entries) + "\n"

    text = re.sub(r"\\begin\{thebibliography\}\{[^}]*\}(.*?)\\end\{thebibliography\}",
                  bibliography, text, flags=re.S)
    text = re.sub(r"\\cite\{([^}]+)\}", lambda m: plain_cites(m.group(1), cites), text)

    def reference(match):
        key = match.group(2)
        if key not in labels:
            raise ValueError(f"Unresolved reference in AUX: {key}")
        val = labels[key]
        return "(" + val + ")" if match.group(1) == "eqref" else val

    text = re.sub(r"\\(eqref|ref)\{([^}]+)\}", reference, text)
    equations = []

    def equation(match):
        body = match.group(1)
        keys = re.findall(r"\\label\{([^}]+)\}", body)
        if len(keys) > 1:
            raise ValueError("Multiple labels in one equation need explicit handling")
        number = labels.get(keys[0]) if keys else str(len(equations) + 1)
        body = re.sub(r"\\label\{[^}]+\}", "", body)
        equations.append({"number": number, "latex": body.strip(), "label": keys[0] if keys else None})
        return "\n\n\\[" + body + "\\]\n\n" + EQ_MARKER + number + "\n\n"

    if re.search(r"\\begin\{(?:align|gather|multline)\}", text):
        raise ValueError("Numbered align/gather/multline requires row-specific AUX numbering support")
    text = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", equation, text, flags=re.S)
    floats = []
    counts = {"figure": 0, "table": 0}

    def process_float(match):
        kind, star, body = match.group(1), match.group(2), match.group(3)
        counts[kind] += 1
        keys = re.findall(r"\\label\{([^}]+)\}", body)
        number = next((labels[x] for x in keys if x in labels), str(counts[kind]))
        cap = re.search(r"\\caption(?:\[[^\]]*\])?\s*\{", body)
        if cap:
            opening = cap.end() - 1
            caption, end = balanced(body, opening)
            prefix = ("TABLE~" + number + "\\\\ ") if kind == "table" else ("Fig.~" + number + ". ")
            body = body[:opening + 1] + prefix + caption + body[end - 1:]
        body = re.sub(r"\\label\{[^}]+\}", "", body)
        floats.append({"kind": kind, "number": number, "wide": bool(star), "labels": keys})
        block = "\\begin{" + kind + "}" + body + "\\end{" + kind + "}"
        if star:
            return "\n\n" + WIDE_START + "\n\n" + block + "\n\n" + WIDE_END + "\n\n"
        return block

    text = re.sub(r"\\begin\{(figure|table)(\*?)\}(.*?)\\end\{\1\2\}", process_float, text, flags=re.S)
    image_records = []

    def graphic(match):
        options, name = match.group(1) or "", match.group(2)
        candidates = [directory / name for directory in graphic_dirs]
        if not Path(name).suffix:
            candidates = [p.with_suffix(ext) for p in candidates for ext in [".pdf", ".png", ".jpg"]]
        source = next((p for p in candidates if p.is_file()), None)
        if source is None:
            raise FileNotFoundError(f"Cannot locate source figure: {name}")
        dest = assets / (source.stem + ".png")
        if source.suffix.lower() == ".pdf":
            pdf = fitz.open(source)
            if len(pdf) != 1:
                raise ValueError(f"Expected a one-page figure: {source}")
            pdf[0].get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False).save(dest)
        else:
            dest = assets / source.name
            dest.write_bytes(source.read_bytes())
        # Explicit physical width avoids Pandoc treating unknown columnwidth as page width.
        width = TEXT_WIDTH_IN if "textwidth" in options else COL_WIDTH_IN
        fraction = re.search(r"width\s*=\s*([0-9.]+)\s*\\(?:textwidth|columnwidth|linewidth)", options)
        if fraction:
            width *= float(fraction.group(1))
        explicit = re.search(r"width\s*=\s*([0-9.]+)\s*(in|cm|mm|pt)\b", options)
        if explicit:
            width = float(explicit.group(1)) / {"in": 1, "cm": 2.54, "mm": 25.4, "pt": 72.27}[explicit.group(2)]
        image_records.append({"source": str(source), "source_sha256": sha(source), "raster": str(dest), "width_in": width})
        return "\\includegraphics[width=" + f"{width:.6f}" + "in]{" + dest.as_posix() + "}"

    text = re.sub(r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}", graphic, text)
    text = text.replace("\\begin{IEEEkeywords}", "\\begin{quote}Index Terms---")
    text = text.replace("\\end{IEEEkeywords}", "\\end{quote}")
    macros = ("\\newcommand{\\IEEEauthorblockN}[1]{#1\\\\}\n"
              "\\newcommand{\\IEEEauthorblockA}[1]{#1}\n"
              "\\newcommand{\\IEEEauthorrefmark}[1]{\\textsuperscript{#1}}\n")
    text = text.replace("\\begin{document}", macros + "\\begin{document}", 1)
    staged = stage / "manuscript_for_word.tex"
    staged.write_text(text, encoding="utf-8")
    return {"source": str(tex), "source_sha256": sha(tex), "aux": str(aux), "aux_sha256": sha(aux),
            "staged": str(staged), "inputs": inputs, "sections": section_specs, "labels": labels, "citations": cites,
            "equations": equations, "floats": floats, "images": image_records}


def force_font(style, size: float, bold=False, italic=False):
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.italic = italic
    style.font.color.rgb = RGBColor(0, 0, 0)
    fonts = style.element.get_or_add_rPr().find(qn("w:rFonts"))
    if fonts is not None:
        for key in list(fonts.attrib):
            if "theme" in key.lower():
                del fonts.attrib[key]
        for key in ["ascii", "hAnsi", "eastAsia", "cs"]:
            fonts.set(qn("w:" + key), "Times New Roman")


def set_cols(sect, number: int):
    cols = sect.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sect.append(cols)
    cols.set(qn("w:num"), str(number))
    cols.set(qn("w:space"), str(round(COL_GAP_IN * 1440)))
    for child in list(cols):
        cols.remove(child)


def roman(number: int) -> str:
    result = ""
    for val, digits in [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while number >= val:
            result += digits
            number -= val
    return result


def prefix(paragraph, text: str):
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    ppr = paragraph._p.find(qn("w:pPr"))
    paragraph._p.insert(1 if ppr is not None else 0, r)


def style_docx(path: Path, manifest: dict) -> dict:
    doc = Document(path)
    for style in doc.styles:
        if style.type == 1:
            force_font(style, 10)
            style.paragraph_format.space_before = Pt(0)
            style.paragraph_format.space_after = Pt(0)
            style.paragraph_format.page_break_before = False
    for name in ["Normal", "Body Text", "First Paragraph"]:
        if name in doc.styles:
            s = doc.styles[name]
            s.paragraph_format.line_spacing = 1
            s.paragraph_format.first_line_indent = Inches(0.14)
    force_font(doc.styles["Title"], 24)
    force_font(doc.styles["Heading 1"], 10)
    force_font(doc.styles["Heading 2"], 10, italic=True)
    for name in ["Caption", "Image Caption", "Table Caption"]:
        if name in doc.styles:
            force_font(doc.styles[name], 8)
    for name in ["Hyperlink", "FollowedHyperlink"]:
        if name in doc.styles:
            doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
            doc.styles[name].font.underline = False
    for element in list(doc.styles.element.iter(qn("w:pBdr"))) + list(doc.element.iter(qn("w:pBdr"))):
        element.getparent().remove(element)
    for section in doc.sections:
        section.page_width, section.page_height = Mm(210), Mm(297)
        section.left_margin = section.right_margin = Inches((210 / 25.4 - TEXT_WIDTH_IN) / 2)
        section.top_margin = Inches(TOP_IN)
        section.bottom_margin = Inches(297 / 25.4 - TOP_IN - TEXT_HEIGHT_IN)
        section.header_distance = section.footer_distance = Inches(0)
    final_sect = doc.sections[-1]._sectPr
    set_cols(final_sect, 2)
    final_type = final_sect.find(qn("w:type"))
    if final_type is None:
        final_type = OxmlElement("w:type")
        final_sect.insert(0, final_type)
    final_type.set(qn("w:val"), "continuous")
    section_template = deepcopy(final_sect)
    # All paragraph section breaks are rebuilt from source float markers.
    for element in list(doc.element.body.iter(qn("w:sectPr"))):
        if element is not final_sect:
            element.getparent().remove(element)

    def section_end(paragraph, columns):
        sect = deepcopy(section_template)
        set_cols(sect, columns)
        typ = sect.find(qn("w:type"))
        if typ is None:
            typ = OxmlElement("w:type")
            sect.insert(0, typ)
        typ.set(qn("w:val"), "continuous")
        paragraph._p.get_or_add_pPr().append(sect)

    heading_count = sub_count = 0
    source_sections = list(manifest["sections"])
    last_para = None
    before_abstract = True
    wide = False
    numbered_eqs = 0
    for paragraph in list(doc.paragraphs):
        text = paragraph.text.strip().replace("\u00a0", " ")
        name = paragraph.style.name
        paragraph.paragraph_format.widow_control = True
        if WIDE_START == text or WIDE_END == text:
            section_end(paragraph, 2 if text == WIDE_START else 1)
            wide = text == WIDE_START
            paragraph.clear()
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.paragraph_format.line_spacing = Pt(1)
            last_para = paragraph
            continue
        if text.startswith(EQ_MARKER):
            if last_para is None:
                raise ValueError("Equation marker has no equation paragraph")
            number = text[len(EQ_MARKER):]
            math_para = last_para._p.find(qn("m:oMathPara"))
            if math_para is None:
                raise ValueError(f"Expected native display equation before marker {number}")
            if math_para.find(qn("m:oMath")) is None:
                raise ValueError("Display equation has no OMML content")
            width = TEXT_WIDTH_IN if wide else COL_WIDTH_IN
            # Keep m:oMathPara: unwrapping it changes display sums and fractions
            # into inline layout. A borderless equation-number row preserves the
            # editable display object and keeps the number within the column.
            eq_table = doc.add_table(rows=1, cols=2)
            eq_table.autofit = False
            props = eq_table._tbl.tblPr
            caption = OxmlElement("w:tblCaption")
            caption.set(qn("w:val"), "Equation layout " + number)
            props.append(caption)
            borders = OxmlElement("w:tblBorders")
            for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
                item = OxmlElement("w:" + edge)
                item.set(qn("w:val"), "nil")
                borders.append(item)
            props.append(borders)
            margins = OxmlElement("w:tblCellMar")
            for edge in ["top", "left", "bottom", "right"]:
                item = OxmlElement("w:" + edge)
                item.set(qn("w:w"), "0")
                item.set(qn("w:type"), "dxa")
                margins.append(item)
            props.append(margins)
            for i, cell in enumerate(eq_table.rows[0].cells):
                cell.width = eq_table.columns[i].width = Inches(width * [0.92, 0.08][i])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                cell_borders = OxmlElement("w:tcBorders")
                for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
                    item = OxmlElement("w:" + edge)
                    item.set(qn("w:val"), "nil")
                    cell_borders.append(item)
                cell._tc.get_or_add_tcPr().append(cell_borders)
                p = cell.paragraphs[0]
                p.style = doc.styles["Normal"]
                p.paragraph_format.first_line_indent = Inches(0)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            eq_table.rows[0].cells[0].paragraphs[0]._p.append(math_para)
            number_run = eq_table.rows[0].cells[1].paragraphs[0].add_run("(" + number + ")")
            number_run.font.size = Pt(10)
            no_split = OxmlElement("w:cantSplit")
            eq_table.rows[0]._tr.get_or_add_trPr().append(no_split)
            prior = last_para._p.getprevious()
            if prior is not None and prior.tag == qn("w:p"):
                prop = prior.find(qn("w:pPr"))
                if prop is None:
                    prop = OxmlElement("w:pPr")
                    prior.insert(0, prop)
                prop.append(OxmlElement("w:keepNext"))
            last_para._p.addnext(eq_table._tbl)
            last_para._p.getparent().remove(last_para._p)
            paragraph._p.getparent().remove(paragraph._p)
            numbered_eqs += 1
            continue
        if name == "Title":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.paragraph_format.space_after = Pt(10)
        elif name == "Author" or (before_abstract and text != "Abstract"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Inches(0)
        elif text == "Abstract":
            if last_para is not None:
                section_end(last_para, 1)
            before_abstract = False
            paragraph._p.getparent().remove(paragraph._p)
            last_para = None
            continue
        elif last_para is None and not before_abstract:
            prefix(paragraph, "Abstract—")
            paragraph.paragraph_format.first_line_indent = Inches(0)
            for run in paragraph.runs:
                run.font.size = Pt(9)
                run.bold = True
        elif name == "Heading 1":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.paragraph_format.space_before = Pt(9)
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.paragraph_format.keep_with_next = True
            unnumbered = text == "References"
            if source_sections:
                unnumbered = source_sections.pop(0)[0]
            if not unnumbered:
                heading_count += 1
                prefix(paragraph, roman(heading_count) + ". ")
            sub_count = 0
            for run in paragraph.runs:
                run.font.small_caps = True
        elif name == "Heading 2":
            sub_count += 1
            prefix(paragraph, chr(64 + sub_count) + ". ")
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.paragraph_format.space_before = Pt(5)
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.keep_with_next = True
        elif text.startswith("Index Terms"):
            paragraph.paragraph_format.first_line_indent = Inches(0)
            for run in paragraph.runs:
                run.font.size = Pt(9)
                run.italic = True
        elif "Caption" in name or text.startswith("TABLE ") or text.startswith("Fig."):
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.paragraph_format.space_before = Pt(3)
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.paragraph_format.keep_with_next = text.startswith("TABLE ")
            if text.startswith("TABLE "):
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.font.size = Pt(8)
        elif re.match(r"^\[\d+\]", text):
            paragraph.paragraph_format.left_indent = Inches(0.15)
            paragraph.paragraph_format.first_line_indent = Inches(-0.15)
            for run in paragraph.runs:
                run.font.size = Pt(8)
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if paragraph._p.find('.//' + qn('w:drawing')) is not None:
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = Inches(0)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        last_para = paragraph

    # Read section state in document order when sizing editable tables.
    current_cols = 1
    table_index = 0
    for child in doc.element.body:
        if child.tag == qn("w:p"):
            sect = child.find('.//' + qn('w:sectPr'))
            if sect is not None:
                ended = int(sect.find(qn("w:cols")).get(qn("w:num"), "1"))
                current_cols = 2 if ended == 1 else 1
        elif child.tag == qn("w:tbl"):
            table = doc.tables[table_index]
            table_index += 1
            caption = table._tbl.tblPr.find(qn("w:tblCaption"))
            if caption is not None and caption.get(qn("w:val"), "").startswith("Equation layout "):
                continue
            width = COL_WIDTH_IN if current_cols == 2 else TEXT_WIDTH_IN
            n = len(table.columns)
            weights = [max(8, min(24, max((len(line) for row in table.rows for line in row.cells[i].text.splitlines()), default=3))) for i in range(n)]
            widths = [width * x / sum(weights) for x in weights]
            table.autofit = False
            for i, column in enumerate(table.columns):
                column.width = Inches(widths[i])
            for row_index, row in enumerate(table.rows):
                row.height = None
                for i, cell in enumerate(row.cells):
                    cell.width = Inches(widths[i])
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.first_line_indent = Inches(0)
                        paragraph.paragraph_format.space_before = Pt(1)
                        paragraph.paragraph_format.space_after = Pt(1)
                        for run in paragraph.runs:
                            run.font.name = "Times New Roman"
                            run.font.size = Pt(8)
                            run.bold = row_index == 0
            if table.rows:
                repeat = OxmlElement("w:tblHeader")
                table.rows[0]._tr.get_or_add_trPr().append(repeat)
    if numbered_eqs != len(manifest["equations"]):
        raise ValueError("Numbered-equation count changed during conversion")
    if len(doc.inline_shapes) != len(manifest["images"]):
        raise ValueError("Figure image count changed during conversion")
    for shape, record in zip(doc.inline_shapes, manifest["images"]):
        ratio = shape.height / shape.width
        shape.width = Inches(record["width_in"])
        shape.height = round(shape.width * ratio)
    raw_xml = doc.element.xml
    if any(x in raw_xml for x in [WIDE_START, WIDE_END, EQ_MARKER]):
        raise ValueError("Conversion control marker leaked into final OOXML")
    # Keep a leading numeric hyphen with its value (e.g. -0.09) without changing
    # the sign or the scientific text. Math signs already live in native OMML.
    for text_node in list(doc.element.iter(qn("w:t"))):
        value = text_node.text or ""
        matches = list(re.finditer(r"(?<![A-Za-z0-9])-(?=\d)", value))
        if not matches or text_node.getparent().tag != qn("w:r"):
            continue
        run = text_node.getparent()
        index = run.index(text_node)
        cursor = 0
        replacement = []
        for match in matches:
            part = OxmlElement("w:t")
            part.set(qn("xml:space"), "preserve")
            part.text = value[cursor:match.start()]
            replacement.extend([part, OxmlElement("w:noBreakHyphen")])
            cursor = match.end()
        part = OxmlElement("w:t")
        part.set(qn("xml:space"), "preserve")
        part.text = value[cursor:]
        replacement.append(part)
        run.remove(text_node)
        for offset, child in enumerate(replacement):
            run.insert(index + offset, child)
    doc.core_properties.author = ""
    doc.save(path)
    return {"numbered_equations": numbered_eqs, "native_math_elements": len(doc.element.findall('.//' + qn('m:oMath'))),
            "tables": len(doc.tables) - numbered_eqs, "equation_layout_tables": numbered_eqs,
            "inline_shapes": len(doc.inline_shapes), "sections": len(doc.sections)}


def convert(tex: Path, aux: Path, output: Path, stage: Path) -> dict:
    manifest = stage_source(tex.resolve(), aux.resolve(), stage.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(PANDOC), manifest["staged"], "--from=latex", "--to=docx", "--standalone", "--output=" + str(output)]
    run = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    (stage / "pandoc.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(run.stderr)
    manifest["word_structure"] = style_docx(output, manifest)
    manifest["output"] = str(output)
    manifest["output_sha256"] = sha(output)
    (stage / "conversion_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex", type=Path)
    parser.add_argument("--aux", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(convert(args.tex, args.aux, args.output, args.stage), indent=2))


if __name__ == "__main__":
    main()
