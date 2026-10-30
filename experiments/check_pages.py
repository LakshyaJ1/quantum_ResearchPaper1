r"""Estimate the compiled page count of paper.tex from float geometry.

Figures are measured from the PNG aspect ratio scaled to the column width; tables
from their row and rule counts. Captions and footnotes are counted separately, as is
the bibliography, from rendered rather than source character counts.

Geometry assumed: IEEEtran conference, 3.5 in column width, ~57 body lines per
column, 114 per page.

Usage: python experiments/check_pages.py
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper.tex"
s = TEX.read_text(encoding="utf-8")

COL_IN = 3.5           # column width, inches
LINES_PER_IN = 6.16    # 57 lines / 9.25 in
LINES_PER_COL = 57
LINES_PER_PAGE = 2 * LINES_PER_COL
CAPTION_WPL = 14       # words per caption line at \small, column width
# Body words per line, back-solved from a compiled 6-page build: content there was
# 5.81 pages (662 lines); floats 68.5, bibliography 63 and title block 28.5 leave
# 502 lines for 4452 body words.
BODY_WPL = 8.87
STRIP = re.compile(r"\\[a-zA-Z*]+|[{}\\&$_^~%]")


def words(t: str) -> int:
    return len(STRIP.sub(" ", t).split())


def png_aspect(name: str) -> float | None:
    p = ROOT / "figures" / (Path(name).stem + ".png")
    if not p.exists():
        return None
    w, h = struct.unpack(">II", p.read_bytes()[16:24])
    return h / w


FLOAT = re.compile(r"\\begin\{(figure|table)(\*?)\}(.*?)\\end\{\1\2\}", re.S)

total_float_lines = 0.0
rows_out = []
for m in FLOAT.finditer(s):
    kind, star, body = m.group(1), m.group(2), m.group(3)
    span = 2.0 if star else 1.0
    cap = re.search(r"\\caption\{(.*?)\}\s*\n\\label", body, re.S)
    cap_words = words(cap.group(1)) if cap else 0
    cap_lines = max(1, round(cap_words / (CAPTION_WPL * span)))
    if kind == "figure":
        g = re.search(r"includegraphics\[[^\]]*\]\{([^}]*)\}", body)
        ar = png_aspect(g.group(1)) if g else None
        art = (COL_IN * span * ar * LINES_PER_IN) if ar else 15.0
        label = g.group(1) if g else "figure"
    else:
        # body rows, plus toprule/midrule(s)/bottomrule and any addlinespace
        art = (len(re.findall(r"\\\\", body))
               + 1.4 * len(re.findall(r"rule", body))
               + 0.3 * len(re.findall(r"addlinespace", body)))
        fn = re.search(r"\\begin\{flushleft\}\\footnotesize(.*?)\\end\{flushleft\}",
                       body, re.S)
        if fn:
            art += max(1, round(words(fn.group(1)) / (CAPTION_WPL * span)))
        label = (re.search(r"\\label\{([^}]*)\}", body) or [None, "table"])[1]
    lines = (art + cap_lines + 1.2) * span   # 1.2 lines of float separation
    total_float_lines += lines
    rows_out.append((label, kind + star, round(art, 1), cap_lines, round(lines, 1)))

body_txt = s.split(r"\begin{document}", 1)[-1].split(
    r"\begin{thebibliography}", 1)[0]
# LaTeX comments do not render, so they must not count as body text. The author-block
# explanation sits after \begin{document} and was being charged ~5 lines.
body_txt = re.sub(r"(?<!\\)%[^\n]*", "", body_txt)
float_txt = "".join(m.group(0) for m in FLOAT.finditer(s))
body_words = words(body_txt) - words(float_txt)

bib = s.split(r"\begin{thebibliography}", 1)[-1]


def rendered(t: str) -> str:
    """Strip markup so the line count reflects glyphs, not LaTeX source. Counting
    source length inflated the list by four lines: \\emph{et al.} is 13 characters of
    source and six of output, ``x'' is four of source and three of output."""
    t = re.sub(r"\\(?:emph|textit)\{([^}]*)\}", r"\1", t)
    t = t.replace("``", '"').replace("''", '"')
    t = re.sub(r"\\['\"]([a-zA-Z])", r"\1", t)       # accents are one glyph
    t = t.replace("~", " ").replace(r"\,", " ")
    t = re.sub(r"\\[a-zA-Z]+", "", t)
    return " ".join(t.replace("{", "").replace("}", "").split())


bib_lines = 1.0
for m in re.finditer(r"\\bibitem\{[^}]*\}(.*?)(?=\\bibitem\{|\\end\{thebib)",
                     bib, re.S):
    bib_lines += max(1, -(-(len(rendered(m.group(1))) + 5) // 92))  # +5 for "[nn] "

body_lines = body_words / BODY_WPL

# Title block. The 0.25-page constant was fitted when the author block was two lines
# (one author, affiliation and email on one line). Measure the block and correct for
# the difference, since a three-author block is several lines taller.
AUTHOR_BASELINE = 2
auth = re.search(r"\\author\{(.*?)\n\}\s*\n\\maketitle", s, re.S)
if auth:
    blk = auth.group(1)
    a_lines = 1 + len(re.findall(r"\\\\", blk)) + 1   # names + wrapped lines + gap
    n_side = blk.count(r"\and") + 1
    if n_side > 1 and r"\IEEEauthorrefmark" not in blk:
        # side-by-side blocks: height is the tallest, not the sum
        a_lines = 1 + (len(re.findall(r"\\\\", blk)) // n_side) + 2
else:
    a_lines = AUTHOR_BASELINE
title_lines = 0.25 * LINES_PER_PAGE + (a_lines - AUTHOR_BASELINE)
print(f"author block  : {a_lines:.0f} lines "
      f"({a_lines - AUTHOR_BASELINE:+.0f} vs the fitted baseline)")

print(f"{'float':<16}{'kind':<9}{'art':>7}{'cap':>5}{'lines':>8}")
print("-" * 46)
for r in rows_out:
    print(f"{r[0]:<16}{r[1]:<9}{r[2]:>7}{r[3]:>5}{r[4]:>8}")
print("-" * 46)
print(f"{'float total':<16}{'':<9}{'':>7}{'':>5}{total_float_lines:>8.1f}")
print()
print(f"body text     : {body_words} words -> {body_lines:.1f} lines")
print(f"floats        : {total_float_lines:.1f} lines")
print(f"bibliography  : {bib_lines:.1f} lines")
print(f"title/abstract: {title_lines:.1f} lines")
tot = body_lines + total_float_lines + bib_lines + title_lines
print(f"\nTOTAL {tot:.0f} lines / {LINES_PER_PAGE} per page "
      f"= {tot / LINES_PER_PAGE:.2f} pages")
free = 6.0 - tot / LINES_PER_PAGE
print(f"{'FITS 6 pages, ' + format(free * LINES_PER_PAGE, '.0f') + ' lines spare'
       if free >= 0 else 'OVER by ' + format(-free * LINES_PER_PAGE, '.0f') + ' lines'}")
