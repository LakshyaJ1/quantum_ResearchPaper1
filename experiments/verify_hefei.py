r"""Verify the load-bearing traffic parameter: the OTP voice rate in the Hefei
46-node metropolitan QKD network paper (arXiv:2109.04736).

Our ISR class demand is 144 000 bit = 2.4 kbps x 60 s, so if 2.4 kbps is wrong
the traffic model's provenance breaks. The abstract does not state the rate, so
it must be confirmed in the body.

Usage: python experiments/verify_hefei.py <path-to-pdf>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from pypdf import PdfReader
except ImportError:
    raise SystemExit("pip install pypdf")

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
pdf = Path(sys.argv[1])
if not pdf.exists():
    raise SystemExit(f"not found: {pdf}")

txt = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
print(f"{pdf.name}: {len(txt)} chars extracted\n")

PATTERNS = {
    "voice rate 2.4 kbps": r"2\.4\s*kbps",
    "file rate 320 kbps": r"320\s*kbps",
    "11 simultaneous pairs": r"11\s+pairs",
    "31 months operation": r"31\s+months",
    "one-time pad": r"one[- ]time[- ]pad",
    "any kbps figure": r"\d+(?:\.\d+)?\s*kbps",
}

for label, pat in PATTERNS.items():
    ms = list(re.finditer(pat, txt, re.I))
    print(f"[{len(ms):>3} hit(s)] {label}")
    for m in ms[:3]:
        a, b = max(0, m.start() - 300), min(len(txt), m.end() + 200)
        print("    ..." + " ".join(txt[a:b].split()) + "...")
    print()
