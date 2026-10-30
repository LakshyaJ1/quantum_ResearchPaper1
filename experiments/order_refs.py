r"""Renumber the bibliography into IEEE order: first appearance in the text.

With a manual thebibliography the printed number is the position of the \bibitem, so
the list has to be sorted by where each key is first cited. This is what BibTeX's
unsrt style does, using source order; floats are numbered by their position in the
source, which is the conventional reading.

Verifies afterwards that every key survives, none is added, and that each key's
bibitem index equals its rank in first-appearance order.

Run: python experiments/order_refs.py [--apply]
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

TEX = Path(__file__).resolve().parents[1] / "paper.tex"
s = TEX.read_text(encoding="utf-8")

head, bib_block = s.split(r"\begin{thebibliography}", 1)
bib_open, bib_rest = bib_block.split("\n", 1)
bib_body, tail = bib_rest.split(r"\end{thebibliography}", 1)

# ---- first-appearance order in the body -------------------------------
order: list[str] = []
for m in re.finditer(r"\\cite\{([^}]*)\}", head):
    for k in (x.strip() for x in m.group(1).split(",")):
        if k and k not in order:
            order.append(k)

# ---- current bibitems, keyed -----------------------------------------
items: dict[str, str] = {}
for m in re.finditer(r"(\\bibitem\{([^}]*)\}.*?)(?=\\bibitem\{|\Z)",
                     bib_body, re.S):
    items[m.group(2)] = m.group(1).rstrip() + "\n"

missing = [k for k in order if k not in items]
orphan = [k for k in items if k not in order]
if missing or orphan:
    print(f"ABORT: cited without bibitem {missing}; bibitem never cited {orphan}")
    raise SystemExit(1)

print(f"{len(order)} references, first-appearance order:")
for i, k in enumerate(order, 1):
    was = list(items).index(k) + 1
    flag = "" if i == was else f"   (was [{was}])"
    print(f"  [{i:>2}] {k}{flag}")

moved = sum(1 for i, k in enumerate(order, 1) if list(items).index(k) + 1 != i)
print(f"\n{moved} of {len(order)} entries change number.")

if "--apply" not in sys.argv:
    print("\nDry run. Re-run with --apply to rewrite paper.tex.")
    raise SystemExit(0)

new_bib = "".join(items[k] for k in order)
out = (head + r"\begin{thebibliography}" + bib_open + "\n" + new_bib
       + r"\end{thebibliography}" + tail)
shutil.copy(TEX, TEX.with_suffix(".tex.preorder"))
TEX.write_text(out, encoding="utf-8")

# ---- verify ----------------------------------------------------------
s2 = TEX.read_text(encoding="utf-8")
h2, b2 = s2.split(r"\begin{thebibliography}", 1)
keys2 = re.findall(r"\\bibitem\{([^}]*)\}", b2)
order2: list[str] = []
for m in re.finditer(r"\\cite\{([^}]*)\}", h2):
    for k in (x.strip() for x in m.group(1).split(",")):
        if k and k not in order2:
            order2.append(k)
assert keys2 == order2, "bibitem order does not match first-appearance order"
assert sorted(keys2) == sorted(items), "a reference was lost or duplicated"
print(f"\nOK: {len(keys2)} bibitems now in first-appearance order; "
      f"none lost or added.")
