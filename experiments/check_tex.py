r"""Structural validation of paper.tex without a LaTeX installation.

The authoring machine has no pdflatex, so this catches the errors that would
otherwise only surface on the first Overleaf build: unbalanced environments,
cite/bibitem mismatches, empty bibitems, missing figure files, and a rough word
count against the 6-page limit.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper.tex"
s = TEX.read_text(encoding="utf-8")

errs: list[str] = []

if s.count(r"\begin{document}") != 1 or s.count(r"\end{document}") != 1:
    errs.append("document environment not exactly once")

for env in ("table", "figure", "figure*", "tabular", "thebibliography",
            "abstract", "quote", "equation", "IEEEkeywords"):
    b = s.count("\\begin{%s}" % env)
    e = s.count("\\end{%s}" % env)
    if b != e:
        errs.append(f"{env}: {b} begin vs {e} end")

# Undefined \ref -> renders as "??" in the PDF. This escaped the original
# validator and shipped two "\S??" into a compiled draft, so it is checked now.
refs = set()
for m in re.finditer(r"\\(?:ref|autoref|eqref)\{([^}]*)\}", s):
    refs.add(m.group(1).strip())
labels = set(re.findall(r"\\label\{([^}]*)\}", s))
undef_refs = sorted(refs - labels)
unused_labels = sorted(labels - refs)
if undef_refs:
    errs.append(f"UNDEFINED \\ref (renders as ??): {undef_refs}")

# An unescaped _ in TEXT mode is a hard LaTeX error ("Missing $ inserted"). It is
# legitimate in math and in file/label/citation keys, so strip those first. An email
# address in the author block is the usual way one sneaks in.
txt = s.split(r"\begin{document}", 1)[-1]
txt = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?)\}.*?"
             r"\\end\{\1\}", " ", txt, flags=re.S)     # display math
txt = re.sub(r"\$[^$]*\$", " ", txt)                    # inline math
txt = re.sub(r"\\(?:includegraphics(?:\[[^\]]*\])?|label|ref|autoref|eqref"
             r"|cite|bibitem|input|graphicspath)\{[^}]*\}", " ", txt)
for m in re.finditer(r"(?<!\\)_", txt):
    ctx = txt[max(0, m.start() - 45):m.start() + 15].replace("\n", " ").strip()
    errs.append(f"unescaped underscore in text (needs \\_): ...{ctx}...")

# Author-identity and URL placeholders must not reach a compiled submission.
placeholders = [p for p in ("[[Author]]", "[[Affiliation]]", "[[email]]",
                            "[[URL]]", "[[VERIFY") if p in s]
if placeholders:
    errs.append(f"placeholders still present: {placeholders}")

keys: set[str] = set()
for m in re.finditer(r"\\cite\{([^}]*)\}", s):
    keys.update(k.strip() for k in m.group(1).split(","))
items = set(re.findall(r"\\bibitem\{([^}]*)\}", s))
missing = sorted(keys - items)
unused = sorted(items - keys)
empty = [ln.strip() for ln in s.splitlines()
         if re.match(r"\s*\\bibitem\{[^}]*\}\s*$", ln)]

if missing:
    errs.append(f"cited without bibitem: {missing}")
if empty:
    errs.append(f"empty bibitems (break compilation): {empty}")
if s.count("{") != s.count("}"):
    errs.append(f"brace imbalance: {s.count('{')} vs {s.count('}')}")

figs = re.findall(r"includegraphics\[[^\]]*\]\{([^}]*)\}", s)
for f in figs:
    p = ROOT / "figures" / f
    if not p.exists():
        errs.append(f"missing figure: figures/{f}")

body = s.split(r"\begin{document}", 1)[-1].split(r"\begin{thebibliography}", 1)[0]
words = len(re.sub(r"\\[a-zA-Z*]+|[{}\\&$_^~%]", " ", body).split())

# Page estimate, calibrated against compiled output:
#   8.0 pp at 5536 body words, 8 floats (3 full width), 33 bibitems
#   7.0 pp at 5223 body words, 6 floats (0 full width), 33 bibitems
# Solving the second for the text rate, with 0.30 page per full-width float,
# 0.15 per single-column float, 1/66 page per bibitem and 0.25 for the title
# free space, gives 1008 words/page and 0.195 page per single-column float.
# Target: content <= 6.00 so the sixth page does not overflow.
n_wide = s.count(r"\begin{figure*}") + s.count(r"\begin{table*}")
n_col = (s.count(r"\begin{figure}") + s.count(r"\begin{table}"))
float_words = sum(len(re.sub(r"\\[a-zA-Z*]+|[{}\\&$_^~%]", " ", m).split())
                  for m in re.findall(
                      r"\\begin\{(?:table\*?|figure\*?)\}.*?"
                      r"\\end\{(?:table\*?|figure\*?)\}", s, re.S))
n_bib = s.count(r"\bibitem{")
est = ((words - float_words) / 1008.0 + 0.39 * n_wide + 0.195 * n_col
       + n_bib / 66.0 + 0.25)

print(f"paper.tex  ({len(s.splitlines())} lines)")
print(f"  environments        : {'OK' if not any('begin vs' in e for e in errs) else 'MISMATCH'}")
print(f"  cite/bibitem        : {len(keys)} cited, {len(items)} bibitems, "
      f"{len(missing)} missing")
print(f"  ref/label           : {len(refs)} refs, {len(labels)} labels, "
      f"{len(undef_refs)} UNDEFINED" + (f" -> {undef_refs}" if undef_refs else ""))
print(f"  labels never ref'd  : {len(unused_labels)}")
print(f"  bibitems not cited  : {len(unused)}"
      f"{' -> ' + str(unused) if unused else ''}")
print(f"  figures referenced  : {len(figs)} -> all present"
      if not any('missing figure' in e for e in errs) else "  figures: MISSING")
print(f"  approx body words   : {words}  ({float_words} inside floats)")
print(f"  floats              : {n_wide} full-width, {n_col} single-column")
print("  page estimate        : run experiments/check_pages.py "
      "(measures float geometry; this file no longer guesses)")
print()
if errs:
    print("ERRORS:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
print("No structural errors. Compile on Overleaf to confirm page count and "
      "check for overfull boxes.")
