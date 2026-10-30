"""Convert the presentation's Markdown documents to Word (.docx).

python tools/md_to_docx.py file.md [more.md ...]
Handles what those files use: #-#### headings, paragraphs, - and 1. lists, | tables |,
--- rules, **bold**, *italic* and `code`. Writes file.docx next to each input.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Pt, RGBColor

INLINE = re.compile(r'(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)')
NAVY = RGBColor(0x00, 0x20, 0x60)


def add_inline(par, text):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith('**'):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith('`'):
            r = par.add_run(part[1:-1])
            r.font.name = 'Consolas'
        elif part.startswith('*'):
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def convert(md_path):
    lines = Path(md_path).read_text(encoding='utf8').splitlines()
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Calibri'
    st.font.size = Pt(11)
    for lvl in range(1, 5):
        h = doc.styles[f'Heading {lvl}']
        h.font.name = 'Calibri'
        h.font.color.rgb = NAVY
    i, para = 0, []

    def flush():
        if para:
            add_inline(doc.add_paragraph(), ' '.join(para))
            para.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        m = re.match(r'^(#{1,4})\s+(.*)', ln)
        if m:
            flush()
            doc.add_heading(m.group(2).strip(), level=len(m.group(1)) if len(m.group(1)) > 1 else 0)
        elif ln.startswith('|'):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=max(len(r) for r in rows))
            t.style = 'Light Grid Accent 1'
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r, cells in enumerate(rows):
                for c, val in enumerate(cells):
                    p = t.cell(r, c).paragraphs[0]
                    add_inline(p, val)
                    if r == 0:
                        for run in p.runs:
                            run.bold = True
            continue
        elif re.match(r'^\s*[-*]\s+', ln):
            flush()
            add_inline(doc.add_paragraph(style='List Bullet'), re.sub(r'^\s*[-*]\s+', '', ln))
        elif re.match(r'^\s*\d+\.\s+', ln):
            flush()
            add_inline(doc.add_paragraph(style='List Number'), re.sub(r'^\s*\d+\.\s+', '', ln))
        elif re.fullmatch(r'-{3,}', ln.strip()):
            flush()
        elif not ln.strip():
            flush()
        else:
            para.append(ln.strip())
        i += 1
    flush()
    out = Path(md_path).with_suffix('.docx')
    doc.save(out)
    return out


if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(convert(f))
