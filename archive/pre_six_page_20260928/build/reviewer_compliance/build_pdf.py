"""Build the final reviewer response PDF without changing scientific outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
SOURCE = ROOT / 'docs/revision/REVIEWER_RESPONSE.md'
sys.path.insert(0, str(ROOT))
from tools.prepare_manuscript_tools import compile_tex


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    original = SOURCE.read_text(encoding='utf-8')
    text = re.sub(r'^# .*\n', '', original, count=1).lstrip()
    text = text.translate(str.maketrans({'\u2013':'-', '\u2014':'-', '\u2011':'-',
                                         '\u2018':"'", '\u2019':"'", '\u201c':'"', '\u201d':'"'}))
    text = text.replace('×', r'$\times$')
    text = re.sub(r'\[([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)\]',
                  r'[\1, \2]', text)
    evidence = []
    def path_reference(match):
        label, target = match.groups()
        if target.startswith(('https://', 'http://')):
            raise ValueError('Review remote hyperlinks before publishing the compliance PDF')
        resolved = (SOURCE.parent / target.split('#')[0]).resolve()
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        relative = resolved.relative_to(ROOT).as_posix()
        evidence.append({'label':label, 'path':relative})
        return r'\path{' + relative + '}'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', path_reference, text)
    text = re.sub(r'(?<![A-Za-z0-9])[0-9a-f]{64}(?![A-Za-z0-9])',
                  lambda m:r'\path{'+m.group(0)+'}', text)
    if len(re.findall(r'^## R1-', text, re.M)) != 21:
        raise ValueError('Expected every official actionable section')
    if re.search(r'Pending|TODO|sec:|fig:|tab:', text):
        raise ValueError('Unresolved working label in final response')
    markdown = STAGE/'Reviewer_Compliance.md'
    markdown.write_text(text, encoding='utf-8')
    body_file = STAGE/'body.tex'
    command = [str(ROOT/'tools/pandoc/pandoc.exe'),str(markdown),
               '--from=markdown+raw_tex+tex_math_dollars', '--to=latex',
               '--wrap=none', '--output',str(body_file)]
    result = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',check=True)
    (STAGE/'pandoc.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    body = body_file.read_text(encoding='utf-8')
    body = body.replace(r'\subsection',r'\Needspace{5\baselineskip}\subsection')
    body = body.replace(r'\Needspace{5\baselineskip}\subsection{Appendix A',
                        r'\clearpage\subsection{Appendix A')
    preamble = r'''\documentclass[a4paper,11pt]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=22mm,headheight=13pt,headsep=8mm,footskip=11mm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{longtable,booktabs,array,calc}
\usepackage{xcolor,graphicx}
\usepackage{etoolbox,needspace,titlesec,fancyhdr}
\usepackage{xurl}
\usepackage[hidelinks,unicode]{hyperref}
\urlstyle{tt}
\def\UrlFont{\small\ttfamily}
\setcounter{secnumdepth}{0}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5.5pt plus 1pt minus 1pt}
\setlength{\emergencystretch}{2em}
\setlength{\LTpre}{6pt}
\setlength{\LTpost}{8pt}
\setlength{\tabcolsep}{5pt}
\AtBeginEnvironment{longtable}{\small\renewcommand{\arraystretch}{1.15}}
\titleformat{\subsection}{\fontsize{12}{14}\selectfont\bfseries\color{black}}{}{0pt}{}
\titlespacing*{\subsection}{0pt}{12pt}{5pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small WiCOMM 2026 / Paper 167}
\fancyhead[R]{\small Reviewer compliance}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\providecommand{\passthrough}[1]{#1}
\widowpenalty=10000
\clubpenalty=10000
\hypersetup{pdftitle={Reviewer Compliance for WiCOMM 2026 Paper 167},
 pdfauthor={Lakshya Jain, Siddhi Arora, Divya Mishra},
 pdfsubject={Responses to all official reviewer comments and questions}}
\begin{document}
\begin{center}
{\fontsize{18}{21}\selectfont\bfseries Reviewer Compliance}\\[5pt]
{\large WiCOMM 2026 Paper 167}\\[7pt]
{\normalsize Fail-Closed or Fail-Degraded? A Simulation Study of Forced Assurance\\
Loss in Contested Multi-Hop QKD Networks}\\[5pt]
{\normalsize Lakshya Jain, Siddhi Arora and Divya Mishra}
\end{center}
\vspace{4pt}
'''
    tex = STAGE/'Reviewer_Compliance.tex'
    tex.write_text(preamble+body+'\n\\end{document}\n',encoding='utf-8')
    out = STAGE/'pdf_build'
    compilation = compile_tex(tex.resolve(),out.resolve())
    final = ROOT/'submission/Reviewer_Compliance.pdf'
    final.parent.mkdir(parents=True,exist_ok=True)
    final.write_bytes((out/'Reviewer_Compliance.pdf').read_bytes())
    manifest = {'source':str(SOURCE.relative_to(ROOT)), 'source_sha256':sha(SOURCE),
                'paper_source_sha256':sha(ROOT/'paper.tex'),
                'paper_aux_sha256':sha(ROOT/'build/final_latex/paper.aux'),
                'latex_reference_pdf_sha256':sha(ROOT/'build/final_latex/paper.pdf'),
                'authoritative_manuscript_pdf':'submission/Paper167_Manuscript.pdf',
                'authoritative_manuscript_pdf_sha256':sha(ROOT/'submission/Paper167_Manuscript.pdf'),
                'builder_sha256':sha(__file__), 'tex_sha256':sha(tex),
                'output':str(final.relative_to(ROOT)), 'pdf_sha256':sha(final),
                'official_sections':21, 'evidence_references':evidence,
                'compilation':compilation}
    (STAGE/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(final),'sha256':manifest['pdf_sha256']}))


if __name__ == '__main__':
    build()
