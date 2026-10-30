r"""Replace the \begin{abstract}...\end{abstract} body in both paper variants.

Kept as a script rather than an inline shell command because bash heredocs in
this environment collapse backslash escapes, which corrupts LaTeX.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
new_body = (ROOT / "abstract_new.tex").read_text(encoding="utf-8").strip()

OPEN, CLOSE = r"\begin{abstract}", r"\end{abstract}"

for name in ("paper.tex", "paper_extended.tex"):
    p = ROOT / name
    s = p.read_text(encoding="utf-8")
    i, j = s.index(OPEN), s.index(CLOSE)
    old_words = len(s[i + len(OPEN):j].split())
    s = s[:i + len(OPEN)] + "\n" + new_body + "\n" + s[j:]
    p.write_text(s, encoding="utf-8")
    print(f"{name}: abstract {old_words} -> {len(new_body.split())} words")

if len(sys.argv) > 1 and sys.argv[1] == "--check":
    for name in ("paper.tex", "paper_extended.tex"):
        s = (ROOT / name).read_text(encoding="utf-8")
        assert s.count(OPEN) == 1 and s.count(CLOSE) == 1, name
    print("both files: abstract environment intact")
