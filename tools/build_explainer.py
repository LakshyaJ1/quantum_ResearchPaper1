"""Build a single-column beginner guide from the verified Markdown source.

Default output is an INTERNAL PREVIEW under tools/explainer_preview. Invoke
--final only after the coordinating revision task has finalized the source.
The builder never changes the Markdown or scientific experiment files.

Portable Pandoc preserves editable OMML equations and Word tables. The authorized
Windows fallback uses an isolated hidden Word instance through the existing
render_word helper, then renders every PDF page with PyMuPDF for visual review.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.prepare_manuscript_tools import render_word

PANDOC = ROOT / 'tools/pandoc/pandoc.exe'
DEFAULT_SOURCE = ROOT / 'docs/revision/RESEARCH_EXPLAINED.md'
PREVIEW = ROOT / 'tools/explainer_preview'
TITLE = 'Understanding QKD network research'
SUBTITLE = 'Keys policies simulations and evidence explained from the beginning'
BODY_FONT = 'Calibri'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font_properties(owner, size, bold=None):
    owner.font.name = BODY_FONT
    owner.font.size = Pt(size)
    owner.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        owner.font.bold = bold
    rpr = owner.element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.insert(0, fonts)
    for attr in list(fonts.attrib):
        if 'theme' in attr.lower():
            del fonts.attrib[attr]
    for attr in ('ascii', 'hAnsi', 'cs', 'eastAsia'):
        fonts.set(qn('w:' + attr), BODY_FONT)
    color = rpr.find(qn('w:color'))
    if color is not None:
        for attr in list(color.attrib):
            if 'theme' in attr.lower():
                del color.attrib[attr]


def set_document_styles(doc, preview):
    for section in doc.sections:
        section.page_width, section.page_height = Mm(210), Mm(297)
        section.top_margin, section.bottom_margin = Mm(22), Mm(20)
        section.left_margin = section.right_margin = Mm(23)
        section.header_distance = section.footer_distance = Mm(10)
        cols = section._sectPr.find(qn('w:cols'))
        if cols is not None:
            cols.set(qn('w:num'), '1')
    for name in ('Normal', 'Body Text', 'First Paragraph', 'Compact'):
        if name not in doc.styles:
            continue
        style = doc.styles[name]
        font_properties(style, 11, False)
        fmt = style.paragraph_format
        fmt.space_before, fmt.space_after = Pt(0), Pt(6)
        fmt.line_spacing = 1.12
        fmt.first_line_indent = Mm(0)
        fmt.widow_control = True
        fmt.keep_with_next = False
    for level in range(1, 10):
        style = doc.styles[f'Heading {level}']
        font_properties(style, 16 if level == 1 else 12, True)
        style.paragraph_format.space_before = Pt(17 if level == 1 else 10)
        style.paragraph_format.space_after = Pt(8)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.keep_together = True
        style.paragraph_format.line_spacing = 1.0
    font_properties(doc.styles['Title'], 26, False)
    doc.styles['Title'].paragraph_format.space_after = Pt(8)
    font_properties(doc.styles['Subtitle'], 12, False)
    doc.styles['Subtitle'].paragraph_format.space_after = Pt(12)
    for name in ('Header', 'Footer', 'Caption'):
        if name in doc.styles:
            font_properties(doc.styles[name], 9, False)
    if 'Hyperlink' in doc.styles:
        font_properties(doc.styles['Hyperlink'], 11)
        doc.styles['Hyperlink'].font.underline = True
    for name in ('Verbatim Char', 'Source Code'):
        if name in doc.styles:
            doc.styles[name].font.name = 'Consolas'
            doc.styles[name].font.size = Pt(9.5)
            doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    # Remove inherited title rules and colored paragraph decoration.
    for element in list(doc.styles.element.iter(qn('w:pBdr'))):
        element.getparent().remove(element)
    for element in list(doc.element.iter(qn('w:pBdr'))):
        element.getparent().remove(element)


def prepare_markdown(source, stage):
    original = source.read_text(encoding='utf-8')
    lines = original.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise ValueError('Expected the Markdown guide to start with a title')
    # The original title remains in the source; the document title is a clearer
    # packaging title. Research paragraphs and tables are not rewritten.
    output = []
    for line in lines[1:]:
        match = re.match(r'^(#{2,6})\s+(.*)$', line)
        if match:
            heading = match[2].replace('AI/ML', 'AI and ML')
            heading = re.sub(r'[^\w\s]', ' ', heading, flags=re.UNICODE)
            heading = re.sub(r'\s+', ' ', heading).strip()
            line = '#' * (len(match[1]) - 1) + ' ' + heading
        output.append(line)
    staged = stage / 'guide_source.md'
    staged.write_text('\n'.join(output).strip() + '\n', encoding='utf-8')
    return staged


def add_bookmark(paragraph, name, identifier):
    start, end = OxmlElement('w:bookmarkStart'), OxmlElement('w:bookmarkEnd')
    start.set(qn('w:id'), str(identifier))
    start.set(qn('w:name'), name)
    end.set(qn('w:id'), str(identifier))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def add_internal_link(paragraph, label, anchor, size=10.5):
    link = OxmlElement('w:hyperlink')
    link.set(qn('w:anchor'), anchor)
    link.set(qn('w:history'), '1')
    run, properties = OxmlElement('w:r'), OxmlElement('w:rPr')
    fonts, color, font_size = OxmlElement('w:rFonts'), OxmlElement('w:color'), OxmlElement('w:sz')
    fonts.set(qn('w:ascii'), BODY_FONT)
    fonts.set(qn('w:hAnsi'), BODY_FONT)
    color.set(qn('w:val'), '000000')
    font_size.set(qn('w:val'), str(round(size * 2)))
    properties.extend([fonts, color, font_size])
    text = OxmlElement('w:t')
    text.text = label
    run.extend([properties, text])
    link.append(run)
    paragraph._p.append(link)


def add_cover_and_contents(doc, preview):
    headings = [p for p in doc.paragraphs if p.style.name == 'Heading 1']
    if not headings:
        raise ValueError('No section headings survived conversion')
    first = doc.paragraphs[0]
    title = first.insert_paragraph_before(TITLE, style='Title')
    title.paragraph_format.keep_with_next = True
    subtitle = first.insert_paragraph_before(SUBTITLE, style='Subtitle')
    subtitle.paragraph_format.keep_with_next = True
    if preview:
        notice = first.insert_paragraph_before(
            'Internal layout preview. Completed research evidence is included; '
            'final source approval and delivery checks remain pending.')
        for run in notice.runs:
            font_properties(run, 10, True)
        notice.paragraph_format.space_after = Pt(10)
    contents = headings[0].insert_paragraph_before('Contents', style='Heading 1')
    contents.paragraph_format.space_before = Pt(12)
    add_bookmark(contents, 'guide_contents', 10000)
    note = headings[0].insert_paragraph_before('Select an entry to jump to that section.')
    note.paragraph_format.space_after = Pt(6)
    for run in note.runs:
        font_properties(run, 10)
    entries = []
    for index, heading in enumerate(headings, 1):
        anchor = f'guide_section_{index}'
        add_bookmark(heading, anchor, 10000 + index)
        entry = headings[0].insert_paragraph_before()
        entry.paragraph_format.line_spacing = 1.0
        entry.paragraph_format.space_before = Pt(0)
        entry.paragraph_format.space_after = Pt(3)
        entry.paragraph_format.keep_with_next = False
        add_internal_link(entry, heading.text, anchor)
        entries.append({'heading': heading.text, 'anchor': anchor})
    headings[0].paragraph_format.page_break_before = True
    for heading in headings:
        next_element = heading._p.getnext()
        if next_element is not None and next_element.tag == qn('w:p'):
            ppr = next_element.find(qn('w:pPr'))
            if ppr is None:
                ppr = OxmlElement('w:pPr')
                next_element.insert(0, ppr)
            ppr.append(OxmlElement('w:keepLines'))
    return entries


def keep_display_equations_with_context(doc):
    """Do not strand a display formula away from its introducing paragraph."""
    for paragraph in doc.paragraphs:
        if paragraph._p.find(qn('m:oMathPara')) is None:
            continue
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.keep_with_next = True
        previous = paragraph._p.getprevious()
        if previous is not None and previous.tag == qn('w:p'):
            ppr = previous.find(qn('w:pPr'))
            if ppr is None:
                ppr = OxmlElement('w:pPr')
                previous.insert(0, ppr)
            ppr.append(OxmlElement('w:keepNext'))


def keep_figures_with_captions(doc):
    """Keep each supporting plot with its native Pandoc image caption."""
    for paragraph in doc.paragraphs:
        if not paragraph._p.xpath('.//w:drawing'):
            continue
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.keep_with_next = True
    for style_name in ('Image Caption', 'Figure Caption'):
        if style_name in doc.styles:
            font_properties(doc.styles[style_name], 10, False)
            doc.styles[style_name].paragraph_format.keep_together = True
            doc.styles[style_name].paragraph_format.space_after = Pt(8)


def style_tables(doc):
    table_details = []
    available_twips = int(Mm(164).twips)
    for index, table in enumerate(doc.tables):
        ncols = len(table.columns)
        fractions = [0.13, 0.49, 0.38] if ncols == 3 else [0.39, 0.61]
        if len(fractions) != ncols:
            fractions = [1/ncols] * ncols
        widths = [round(available_twips * fraction) for fraction in fractions]
        widths[-1] += available_twips - sum(widths)
        table.autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        props = table._tbl.tblPr
        borders = props.find(qn('w:tblBorders'))
        if borders is None:
            borders = OxmlElement('w:tblBorders')
            props.append(borders)
        for direction in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            border = OxmlElement('w:' + direction)
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:color'), 'D9D9D9')
            borders.append(border)
        margins = OxmlElement('w:tblCellMar')
        vertical_padding = 70 if ncols == 2 else 90
        for direction, value in (('top', vertical_padding), ('bottom', vertical_padding), ('left', 110), ('right', 110)):
            margin = OxmlElement('w:' + direction)
            margin.set(qn('w:w'), str(value))
            margin.set(qn('w:type'), 'dxa')
            margins.append(margin)
        props.append(margins)
        for grid, width in zip(table._tbl.tblGrid.gridCol_lst, widths):
            grid.set(qn('w:w'), str(width))
        for row_number, row in enumerate(table.rows):
            row.height = None
            trpr = row._tr.get_or_add_trPr()
            for height in list(trpr.findall(qn('w:trHeight'))):
                trpr.remove(height)
            no_split = OxmlElement('w:cantSplit')
            trpr.append(no_split)
            if row_number == 0:
                repeat = OxmlElement('w:tblHeader')
                trpr.append(repeat)
            for col_number, cell in enumerate(row.cells):
                cell.width = Mm(164 * fractions[col_number])
                tcw = cell._tc.get_or_add_tcPr().find(qn('w:tcW'))
                tcw.set(qn('w:w'), str(widths[col_number]))
                tcw.set(qn('w:type'), 'dxa')
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if row_number == 0:
                    fill = OxmlElement('w:shd')
                    fill.set(qn('w:fill'), 'EDEDED')
                    cell._tc.get_or_add_tcPr().append(fill)
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.line_spacing = 1.06
                    paragraph.paragraph_format.space_before = Pt(1)
                    paragraph.paragraph_format.space_after = Pt(1 if ncols == 2 else 2)
                    paragraph.paragraph_format.keep_with_next = row_number == 0
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if ncols == 3 and col_number == 0 else WD_ALIGN_PARAGRAPH.LEFT
                # Include hyperlink runs, which python-docx paragraph.runs omits.
                for run in cell._tc.iter(qn('w:r')):
                    rpr = run.find(qn('w:rPr'))
                    if rpr is None:
                        rpr = OxmlElement('w:rPr')
                        run.insert(0, rpr)
                    size = rpr.find(qn('w:sz'))
                    if size is None:
                        size = OxmlElement('w:sz')
                        rpr.append(size)
                    size.set(qn('w:val'), '20')
                    if row_number == 0 and rpr.find(qn('w:b')) is None:
                        rpr.append(OxmlElement('w:b'))
        table_details.append({'table': index + 1, 'rows': len(table.rows),
                              'columns': ncols, 'widths_twips': widths,
                              'repeated_header': True, 'fixed_row_heights': False})
        previous = table._tbl.getprevious()
        if previous is not None and previous.tag == qn('w:p'):
            ppr = previous.find(qn('w:pPr'))
            if ppr is None:
                ppr = OxmlElement('w:pPr')
                previous.insert(0, ppr)
            ppr.append(OxmlElement('w:keepNext'))
        following = table._tbl.getnext()
        if following is not None and following.tag == qn('w:p'):
            ppr = following.find(qn('w:pPr'))
            if ppr is None:
                ppr = OxmlElement('w:pPr')
                following.insert(0, ppr)
            spacing = ppr.find(qn('w:spacing'))
            if spacing is None:
                spacing = OxmlElement('w:spacing')
                ppr.append(spacing)
            spacing.set(qn('w:before'), '160')
    return table_details


def add_running_text(doc, preview):
    for section in doc.sections:
        header = section.header.paragraphs[0]
        header.text = 'QKD network research explained'
        header.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in header.runs:
            font_properties(run, 9)
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run('Internal preview | Page ' if preview else 'Page ')
        page = OxmlElement('w:fldSimple')
        page.set(qn('w:instr'), 'PAGE')
        footer._p.append(page)
        for run in footer.runs:
            font_properties(run, 9)


def rebase_local_hyperlinks(doc, source, logical_output_dir):
    """Keep repository links valid after moving the guide away from its source."""
    links = []
    for relation in doc.part.rels.values():
        if relation.reltype != RT.HYPERLINK or not relation.is_external:
            continue
        target = relation.target_ref
        parsed = urlsplit(target)
        # External URLs and internal fragment-only links retain their targets.
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        resolved = (source.parent / unquote(parsed.path)).resolve()
        relative = Path(os.path.relpath(resolved, logical_output_dir)).as_posix()
        emitted = urlunsplit(('', '', quote(relative, safe='/'), parsed.query, parsed.fragment))
        relation._target = emitted
        links.append({'source_target': target, 'emitted_target': emitted,
                      'resolved_target': str(resolved), 'exists': resolved.exists()})
    return links


def render_and_inspect(pdf_path, stage):
    import fitz
    pages = []
    with fitz.open(pdf_path) as pdf:
        for index, page in enumerate(pdf):
            image = stage / f'page_{index+1:02}.png'
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(image)
            spans = [span for block in page.get_text('dict')['blocks'] if 'lines' in block
                     for line in block['lines'] for span in line['spans']]
            outside = [span['text'] for span in spans if span['bbox'][0] < 0
                       or span['bbox'][2] > page.rect.width + .5
                       or span['bbox'][1] < 0 or span['bbox'][3] > page.rect.height + .5]
            embedded = [len(pdf.extract_font(font[0])[3]) > 0 for font in page.get_fonts()]
            pages.append({'page': index + 1, 'image': str(image),
                          'image_sha256': sha(image),
                          'width_pt': page.rect.width, 'height_pt': page.rect.height,
                          'text_characters': len(page.get_text()),
                          'out_of_page_text': outside,
                          'all_fonts_embedded': all(embedded),
                          'internal_links': sum(link['kind'] == fitz.LINK_GOTO for link in page.get_links())})
    # A shorter rebuild must not leave pages from an older, longer PDF. Remove
    # only this renderer's numbered PNGs, and only after all current pages exist.
    expected_images = {Path(page['image']).name for page in pages}
    for image in stage.glob('page_*.png'):
        if re.fullmatch(r'page_\d+\.png', image.name) and image.name not in expected_images:
            image.unlink()
    return pages


def build(source=DEFAULT_SOURCE, final=False, logical_output_dir=None):
    source = Path(source).resolve()
    source_hash = sha(source)
    stage = PREVIEW
    logical_output_dir = Path(logical_output_dir or (ROOT / 'submission' if final else stage)).resolve()
    stage.mkdir(parents=True, exist_ok=True)
    staged = prepare_markdown(source, stage)
    reference = stage / 'guide_reference.docx'
    refdoc = Document()
    set_document_styles(refdoc, not final)
    refdoc.save(reference)
    raw_docx = stage / 'guide_pandoc.docx'
    command = [str(PANDOC), str(staged), '--from=markdown+tex_math_dollars+pipe_tables',
               '--to=docx', f'--reference-doc={reference}', f'--output={raw_docx}']
    run = subprocess.run(command, cwd=source.parent, capture_output=True, text=True,
                         encoding='utf-8', errors='replace', timeout=90)
    (stage / 'pandoc.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    if run.returncode:
        raise RuntimeError(f'Pandoc failed with exit {run.returncode}: {run.stderr}')
    doc = Document(raw_docx)
    set_document_styles(doc, not final)
    contents = add_cover_and_contents(doc, not final)
    keep_display_equations_with_context(doc)
    keep_figures_with_captions(doc)
    tables = style_tables(doc)
    if doc.paragraphs:
        doc.paragraphs[-1].paragraph_format.keep_together = True
    add_running_text(doc, not final)
    doc.core_properties.title = TITLE
    doc.core_properties.subject = SUBTITLE
    doc.core_properties.author = ''
    doc.core_properties.last_modified_by = ''
    docx_path = stage / ('Research_Explained.docx' if final else 'Research_Explained_INTERNAL_PREVIEW.docx')
    pdf_path = stage / ('Research_Explained.pdf' if final else 'Research_Explained_INTERNAL_PREVIEW.pdf')
    local_links = rebase_local_hyperlinks(doc, source, logical_output_dir)
    doc.save(docx_path)
    exported = render_word(docx_path, pdf_path)
    pages = render_and_inspect(pdf_path, stage)
    if sha(source) != source_hash:
        raise RuntimeError('Markdown changed during this build; rerun before using the preview')
    with zipfile.ZipFile(docx_path) as archive:
        from lxml import etree
        xml = etree.fromstring(archive.read('word/document.xml'))
        math_count = len(xml.findall('.//m:oMath', NS))
        table_count = len(xml.findall('.//w:tbl', NS))
        image_count = len(xml.findall('.//w:drawing', NS))
    manifest = dict(
        created_utc=datetime.now(timezone.utc).isoformat(), internal_preview=not final,
        source=str(source), source_sha256=source_hash, builder_sha256=sha(Path(__file__)),
        pandoc_sha256=sha(PANDOC), docx=str(docx_path), docx_sha256=sha(docx_path),
        pdf=str(pdf_path), pdf_sha256=sha(pdf_path), word_export=exported,
        native_math_objects=math_count, editable_tables=table_count,
        embedded_images=image_count,
        contents=contents, table_geometry=tables, pages=pages,
        logical_output_directory=str(logical_output_dir), local_file_links=local_links,
        missing_local_targets=[link['source_target'] for link in local_links if not link['exists']],
        visual_review='Required on every rendered page before delivery',
        final_submission_copy='Not performed by this builder; coordinating agent controls delivery')
    (stage / 'build_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--final', action='store_true',
                        help='Remove preview labeling only after final source approval in the coordinating task')
    parser.add_argument('--logical-output-dir', type=Path,
                        help='Directory from which repository links will resolve; defaults to preview or ROOT/submission for --final')
    args = parser.parse_args(argv)
    manifest = build(args.source, args.final, args.logical_output_dir)
    print(json.dumps({'internal_preview': manifest['internal_preview'], 'pdf': manifest['pdf'],
                      'pages': len(manifest['pages']), 'native_math_objects': manifest['native_math_objects'],
                      'editable_tables': manifest['editable_tables'],
                      'missing_local_targets': manifest['missing_local_targets']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
