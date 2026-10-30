r"""Check every tabular in paper.tex for column-count and width errors.

A row whose cell count differs from the column spec is a LaTeX error. A table wider
than \columnwidth is not: it silently overprints the adjacent column, so the width is
estimated here from the widest cell in each column plus inter-column spacing.

Usage: python experiments/check_tables.py
"""
from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).resolve().parents[1] / "paper.tex"
s = TEX.read_text(encoding="utf-8")

PT_PER_CHAR = 4.3
COL_PT = 252.0          # 3.5 in, single column
TEXT_PT = 516.0         # full width, for table*
DEFAULT_SEP = 6.0

TAB = re.compile(r"\\begin\{table(\*?)\}(.*?)\\end\{table\1\}", re.S)
TABULAR = re.compile(
    r"\\begin\{tabular\}\{@\{\}([lcr]+)@\{\}\}(.*?)\\end\{tabular\}", re.S)
MARKUP = re.compile(
    r"\\(?:emph|textbf|textsc|checkmark|circ|dagger|ast|times|le|ge|rightarrow"
    r"|sim|approx|phi|Delta|GI{1,4}|GII|GIII|GIV)\b|\\,|[{}$~\\]")


def cell_chars(c: str) -> int:
    """Rendered width of one cell in characters; each cited key becomes '[nn]'."""
    keys = sum(len(m.group(1).split(","))
               for m in re.finditer(r"\\cite\{([^}]*)\}", c))
    t = MARKUP.sub("", re.sub(r"\\cite\{[^}]*\}", "", c)).strip()
    return len(t) + keys * 4 + max(0, keys - 1) * 2


bad = 0
for tm in TAB.finditer(s):
    star, body = tm.group(1), tm.group(2)
    avail = TEXT_PT if star else COL_PT
    m_sep = re.search(r"\\setlength\{\\tabcolsep\}\{([\d.]+)pt\}", body)
    sep = float(m_sep.group(1)) if m_sep else DEFAULT_SEP
    label = (re.search(r"\\label\{([^}]*)\}", body) or [None, "?"])[1]
    for m in TABULAR.finditer(body):
        spec, rows = m.group(1), m.group(2)
        n = len(spec)
        widest = [0] * n
        for ln in rows.splitlines():
            t = ln.strip()
            if "&" not in t or t.startswith(r"\multicolumn"):
                continue
            cells = t.rstrip("\\").split("&")
            if len(cells) != n:
                print(f"  {label:<14} COUNT MISMATCH {len(cells)} vs {n}: {t[:55]}")
                bad += 1
                continue
            for i, c in enumerate(cells):
                widest[i] = max(widest[i], cell_chars(c))
        content = sum(w * PT_PER_CHAR for w in widest)
        gaps = 2 * sep * n - 2 * sep
        total = content + gaps
        pct = total / avail * 100
        flag = "OVERFULL" if total > avail else "tight" if pct > 95 else "ok"
        print(f"  {label:<14} {n} cols, tabcolsep {sep:>4}pt: "
              f"content {content:5.0f} + gaps {gaps:4.0f} = {total:5.0f}pt "
              f"of {avail:.0f} ({pct:3.0f}%) {flag}")
        if total > avail:
            bad += 1
            print(f"      widest cell per column, chars: {widest}")

print()
if bad:
    print(f"{bad} problem(s) -- fix before compiling.")
    raise SystemExit(1)
print("All tabulars: column counts match and widths fit.")
