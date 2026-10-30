"""Apply whitespace-insensitive text replacements to paper.tex (each must match once).

python tools/apply_text_edits.py edits.json
edits.json: [["old text", "new text"], ...]. Used for manuscript revisions so that
every replacement is checked to match exactly one place in the source.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(edits_path, target=ROOT / 'paper.tex'):
    s = target.read_text(encoding='utf-8')
    edits = json.loads(Path(edits_path).read_text(encoding='utf-8'))
    for old, new in edits:
        pat = r'\s+'.join(re.escape(w) for w in old.split())
        s, n = re.subn(pat, lambda m, new=new: new, s)
        if n != 1:
            raise SystemExit(f'{n} matches for: {old[:80]}')
    target.write_text(s, encoding='utf-8')
    print(f'{len(edits)} edits applied to {target.name}')


if __name__ == '__main__':
    main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'paper.tex')
