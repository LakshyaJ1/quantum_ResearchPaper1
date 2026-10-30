"""Order the manuscript's \\bibitem entries by first citation (IEEE numbering).

python tools/order_bibliography.py paper.tex
Rewrites the thebibliography block of the given file in first-citation order and
fails if any cited key lacks an entry or any entry is never cited.
"""
import re
import sys
from pathlib import Path

CITE = re.compile(r'\\cite\{([^}]+)\}')
ITEM = re.compile(r'\\bibitem\{([^}]+)\}')


def main(path):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    head, rest = text.split('\\begin{thebibliography}{00}', 1)
    bib, tail = rest.split('\\end{thebibliography}', 1)
    items = {}
    for block in re.split(r'(?=\\bibitem\{)', bib):
        m = ITEM.match(block.strip())
        if m:
            items[m.group(1)] = block.strip()
    order = []
    for m in CITE.finditer(head):
        for key in (k.strip() for k in m.group(1).split(',')):
            if key not in order:
                order.append(key)
    missing = [k for k in order if k not in items]
    unused = [k for k in items if k not in order]
    if missing or unused:
        raise SystemExit(f'missing entries {missing}; uncited entries {unused}')
    body = '\n'.join(items[k] for k in order)
    p.write_text(head + '\\begin{thebibliography}{00}\n' + body + '\n\\end{thebibliography}'
                 + tail, encoding='utf-8')
    print(f'{len(order)} references in first-citation order')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'paper.tex')
