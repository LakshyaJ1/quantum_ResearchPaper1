"""Extract the delivered source ZIP, compile it and compare every rendered page."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import zipfile

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.prepare_manuscript_tools import compile_tex


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    archive_path = ROOT / 'submission/Manuscript_Source.zip'
    parent = ROOT / 'build/package_compile_check'
    parent.mkdir(parents=True, exist_ok=True)
    # An empty, unique extraction prevents a missing archive member from being
    # accidentally supplied by the previous five-page build or another check.
    target = Path(tempfile.mkdtemp(prefix='six_page_', dir=parent))
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
            if not (target / member).resolve().is_relative_to(target.resolve()):
                raise ValueError('Archive member leaves extraction directory')
        assert archive.testzip() is None
        archive.extractall(target)
        for row in archive.read('MANIFEST.sha256').decode('utf-8').splitlines():
            digest, member = row.split('  ', 1)
            assert sha(target / member) == digest
    build = compile_tex(target / 'paper.tex', target / 'compiled')
    reference = ROOT / 'build/final_latex/paper.pdf'
    rebuilt = target / 'compiled/paper.pdf'
    page_matches = []
    with fitz.open(reference) as original, fitz.open(rebuilt) as copy:
        assert len(original) == len(copy) == 6
        for a, b in zip(original, copy):
            x = hashlib.sha256(a.get_pixmap(matrix=fitz.Matrix(1.7, 1.7)).samples).hexdigest()
            y = hashlib.sha256(b.get_pixmap(matrix=fitz.Matrix(1.7, 1.7)).samples).hexdigest()
            page_matches.append(x == y)
    assert build['exit_code'] == 0 and len(page_matches) == 6 and all(page_matches), page_matches
    report = {
        'source_archive': str(archive_path.relative_to(ROOT)),
        'source_archive_sha256': sha(archive_path),
        'extracted_members_verified': True,
        'fresh_extraction_directory': str(target.relative_to(ROOT)),
        'build_exit_code': build['exit_code'],
        'rebuilt_pdf_sha256': sha(rebuilt), 'reference_pdf_sha256': sha(reference),
        'pages': 6, 'pixel_identical_pages': [i + 1 for i, same in enumerate(page_matches) if same],
        'renderer': 'Tectonic 0.17.0 with installed standard IEEEtran/TeX dependencies',
        'passed': True,
    }
    out = ROOT / 'results/revision/verification/packaged_manuscript.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
