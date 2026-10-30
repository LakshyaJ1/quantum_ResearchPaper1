"""Assemble submission/ from the current camera-ready builds.

python tools/package_submission.py

Requires the LaTeX PDF (build/camera_ready/latex), the Word file and its PDF
(tools/build_word_cr.py) and the compliance report to be newer than paper.tex. Checks
that the LaTeX source package compiles on its own to six pages, then writes the
deliverables, SHA256SUMS.txt and DELIVERY_MANIFEST.json. submission/READ_ME.md is kept.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

import fitz

R = Path(__file__).resolve().parents[1]
SUB = R / 'submission'
LATEX_PDF = R / 'build/camera_ready/latex/paper.pdf'
WORD_DOCX = R / 'build/camera_ready/word/Paper167_Manuscript.docx'
WORD_PDF = R / 'build/camera_ready/word/Paper167_Manuscript.pdf'
COMPLIANCE = R / 'build/camera_ready/compliance/Reviewer_Compliance.pdf'
SOURCES = ['paper.tex',
           'results/camera_ready/manuscript/head_table.tex',
           'results/camera_ready/manuscript/envelope_table.tex',
           'results/camera_ready/manuscript/learning_table.tex',
           'figures/camera_ready/fig1_architecture.pdf',
           'figures/camera_ready/fig2_cut_scaling.pdf',
           'figures/camera_ready/fig3_forcing_cost.pdf']
PAGES = 6


def main():
    source_time = (R / 'paper.tex').stat().st_mtime
    for p in (LATEX_PDF, WORD_DOCX, WORD_PDF, COMPLIANCE):
        if not p.exists():
            raise SystemExit(f'missing build output: {p}')
    for p in (LATEX_PDF, WORD_DOCX):
        if p.stat().st_mtime < source_time:
            raise SystemExit(f'{p.name} is older than paper.tex; rebuild it first')

    SUB.mkdir(exist_ok=True)
    outputs = ('Paper167_LaTeX.pdf', 'Paper167_LaTeX_Source.zip', 'Paper167_Manuscript.docx',
               'Paper167_Manuscript.pdf', 'Reviewer_Compliance.pdf', 'SHA256SUMS.txt',
               'DELIVERY_MANIFEST.json')
    for name in outputs:                # files added by hand (e.g. the PDF eXpress download) stay
        (SUB / name).unlink(missing_ok=True)

    zip_path = SUB / 'Paper167_LaTeX_Source.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in SOURCES:
            z.write(R / rel, rel)
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        env = dict(os.environ)
        env['TECTONIC_CACHE_DIR'] = str(R / 'tools/tectonic_cache')
        subprocess.run([str(R / 'tools/tectonic/tectonic.exe'), '-X', 'compile', 'paper.tex'],
                       cwd=tmp, env=env, check=True, capture_output=True)
        with fitz.open(Path(tmp) / 'paper.pdf') as d:
            zip_pages = d.page_count
    if zip_pages != PAGES:
        raise SystemExit(f'source package compiles to {zip_pages} pages, not {PAGES}')

    shutil.copy2(LATEX_PDF, SUB / 'Paper167_LaTeX.pdf')
    shutil.copy2(WORD_DOCX, SUB / 'Paper167_Manuscript.docx')
    shutil.copy2(WORD_PDF, SUB / 'Paper167_Manuscript.pdf')
    shutil.copy2(COMPLIANCE, SUB / 'Reviewer_Compliance.pdf')

    info = {}
    for f in sorted(SUB.iterdir()):
        entry = dict(bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        if f.suffix == '.pdf':
            with fitz.open(f) as d:
                entry['pages'] = d.page_count
                entry['page_size_pt'] = [round(d[0].rect.width, 1), round(d[0].rect.height, 1)]
                fonts = [x for i in range(d.page_count) for x in d.get_page_fonts(i)]
                entry['fonts'] = sorted({x[3] for x in fonts})
                entry['all_fonts_embedded'] = all(x[1] != 'n/a' and x[0] > 0 for x in fonts)
        info[f.name] = entry
    (SUB / 'SHA256SUMS.txt').write_text(
        ''.join(f"{v['sha256']}  {k}\n" for k, v in info.items()), encoding='utf-8')
    (SUB / 'DELIVERY_MANIFEST.json').write_text(json.dumps(
        dict(paper='WiCOMM-2026 paper 167', built_from='paper.tex', files=info,
             latex_source_standalone_pages=zip_pages), indent=1), encoding='utf-8')
    for k, v in info.items():
        print(f"{k:32s} {v['bytes']:>9d}  {v.get('pages', '')}  {v.get('all_fonts_embedded', '')}")


if __name__ == '__main__':
    main()
