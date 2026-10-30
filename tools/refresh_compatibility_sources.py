"""Keep historical manuscript entry filenames pointed at the verified revision."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=(ROOT/'paper.tex').read_text(encoding='utf-8')
    macros={}
    for path in (ROOT/'results/revision/manuscript').glob('*_numbers.tex'):
        macros.update(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^{}]+)\}',path.read_text()))
    match=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',source,re.S)
    if not match:
        raise RuntimeError('Main manuscript has no abstract')
    abstract=re.sub(r'\\([A-Za-z]+)',lambda found:macros.get(found.group(1),found.group(0)),match.group(1))
    abstract=re.sub(r'(?<=\d)\{\}','',abstract)
    (ROOT/'abstract_new.tex').write_text('% Exact numerical abstract from the verified revision.\n'
        '\\begin{abstract}'+abstract+'\\end{abstract}\n',encoding='utf-8')
    (ROOT/'paper_extended.tex').write_text(
        '% Compatibility entry point for the current verified conference manuscript.\n'
        '% The original extended draft is preserved in archive/manuscripts_before_revision/.\n'
        '% Detailed current evidence is in docs/revision/ and results/revision/.\n'
        '\\input{paper.tex}\n',encoding='utf-8')
    print('Updated the abstract and legacy manuscript entry point')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
