"""Package the completed local revision and verify every delivered archive member."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
import sys
import zipfile

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
sys.path.insert(0, str(ROOT))
from experiments.revision_suite import fingerprint


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path: Path):
    def reject(value):
        raise ValueError(f'Nonfinite JSON value {value} in {path}')
    return json.loads(path.read_text(encoding='utf-8-sig'), parse_constant=reject)


def pdf_info(path: Path) -> dict:
    with fitz.open(path) as doc:
        fonts = {font[0] for page in doc for font in page.get_fonts()}
        return {
            'pages': len(doc),
            'all_fonts_embedded': all(bool(doc.extract_font(x)[3]) for x in fonts),
            'page_sizes_pt': [[round(p.rect.width, 2), round(p.rect.height, 2)] for p in doc],
        }


def files_under(folder: str, suffixes: set[str]) -> set[Path]:
    return {p for p in (ROOT / folder).rglob('*')
            if p.is_file() and p.suffix.lower() in suffixes and '__pycache__' not in p.parts}


def make_zip(name: str, paths: set[Path]) -> dict:
    files = sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())
    frozen = {}
    archive_path = OUT / name
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        def write_member(member, data):
            info = zipfile.ZipInfo(member, date_time=(2026, 9, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=6)
        for path in files:
            resolved = path.resolve()
            if not resolved.is_relative_to(ROOT) or path.is_symlink():
                raise ValueError(f'Unsafe archive member: {path}')
            member = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            frozen[member] = hashlib.sha256(data).hexdigest()
            write_member(member, data)
        manifest = ''.join(f'{digest}  {member}\n' for member, digest in frozen.items())
        write_member('MANIFEST.sha256', manifest.encode('utf-8'))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None, 'ZIP CRC failure'
        assert len(archive.namelist()) == len(set(archive.namelist()))
        for member, digest in frozen.items():
            assert hashlib.sha256(archive.read(member)).hexdigest() == digest
            assert sha(ROOT / member) == digest, f'Source changed during packaging: {member}'
        assert archive.read('MANIFEST.sha256').decode('utf-8') == manifest
    return {'file': name, 'members_including_manifest': len(files) + 1,
            'bytes': archive_path.stat().st_size, 'sha256': sha(archive_path),
            'crc_and_all_member_hashes_verified': True}


def main():
    OUT.mkdir(exist_ok=True)
    gate = strict_json(ROOT / 'results/revision/verification/research_gate.json')
    assert gate['passed'] and gate['regression_tests_run'] == 127
    assert gate['failures'] == gate['errors'] == gate['skipped'] == 0
    assert gate['legacy_validation']['returncode'] == 0
    assert '43/43 checks passed' in gate['legacy_validation']['stdout']
    source_hash = fingerprint()
    phase_checks = {}
    for phase, expected in [('main', 360), ('sensitivity', 1152), ('threshold', 408)]:
        path = ROOT / f'results/revision/analysis/{phase}_verification.json'
        record = strict_json(path)
        assert record['source_hash'] == source_hash
        assert record['canonical_runs'] == expected
        phase_checks[phase] = record
    assert (ROOT / 'paper.tex').read_bytes() == (ROOT / 'paper_revised.tex').read_bytes()
    word_qa = strict_json(ROOT / 'build/final_word/final_quality_report.json')
    assert word_qa['local_delivery_checks_passed']
    assert sha(ROOT / 'paper.tex') == word_qa['source']['sha256']
    for key in ['docx', 'pdf']:
        assert sha(Path(word_qa[key]['path'])) == word_qa[key]['sha256']
    guide_qa = strict_json(ROOT / 'docs/revision/explainer_delivery_verification.json')
    assert guide_qa['status'] == 'passed' and guide_qa['every_final_page_visually_reviewed']
    for key in ['source', 'pdf', 'docx']:
        assert sha(Path(guide_qa[key])) == guide_qa[key + '_sha256']
    response_qa = strict_json(ROOT / 'build/reviewer_compliance/closure_manifest.json')
    assert response_qa['all_technical_checks_passed']
    assert response_qa['visual_review']['all_pages_inspected']
    assert sha(OUT / 'Reviewer_Compliance.pdf') == response_qa['pdf_sha256']
    assert sha(OUT / 'Paper167_Manuscript.pdf') == response_qa['authoritative_manuscript_pdf_sha256']
    assert sha(ROOT / 'docs/revision/REVIEWER_RESPONSE.md') == response_qa['response_sha256']
    assert sha(ROOT / 'docs/revision/official_review_matrix.md') == response_qa['matrix_sha256']
    assert len(response_qa['official_actionable_sections']) == 21
    shutil.copyfile(ROOT / 'build/final_latex/paper.pdf', OUT / 'Paper167_LaTeX.pdf')
    latex_log = (ROOT / 'build/final_latex/paper.log').read_text(encoding='utf-8', errors='replace')
    assert not re.search(r'Overfull|undefined references|Missing character|Font Warning', latex_log)
    checks = ROOT / 'docs/revision/delivery_checks'
    checks.mkdir(exist_ok=True)
    for name in ['final_quality_report.json', 'FINAL_QA.md', 'independent_visual_review.md']:
        shutil.copyfile(ROOT / 'build/final_word' / name, checks / ('word_' + name))
    for name in ['closure_manifest.json', 'independent_visual_qa.md', 'render_submission/technical_qa.json']:
        shutil.copyfile(ROOT / 'build/reviewer_compliance' / name, checks / ('reviewer_' + Path(name).name))
    latex_qa = {
        'source_sha256': sha(ROOT / 'paper.tex'),
        'pdf_sha256': sha(OUT / 'Paper167_LaTeX.pdf'),
        **pdf_info(OUT / 'Paper167_LaTeX.pdf'),
        'visually_reviewed_pages': [1, 2, 3, 4, 5],
        'visual_review_status': 'passed',
        'overfull_boxes_unresolved_references_missing_glyphs_font_warnings': False,
        'nonblocking_underfull_box_warnings': True,
        'pdf_express_certified': False,
    }
    (checks / 'latex_quality_report.json').write_text(json.dumps(latex_qa, indent=2) + '\n', encoding='utf-8')
    for path in (ROOT / 'results/revision').rglob('*.json'):
        strict_json(path)

    manuscript = {ROOT / n for n in ['paper.tex', 'paper_revised.tex', 'paper_extended.tex',
                                     'abstract_new.tex', 'MANUSCRIPT_BUILD.md', '.gitattributes']}
    manuscript |= files_under('results/revision/manuscript', {'.tex', '.json'})
    manuscript |= {p for p in (ROOT / 'figures/revision').glob('fig*')
                   if p.suffix in {'.png', '.pdf', '.json'}}
    manuscript_zip = make_zip('Manuscript_Source.zip', manuscript)
    packaged_build = strict_json(ROOT / 'results/revision/verification/packaged_manuscript.json')
    assert packaged_build['passed'] and packaged_build['pixel_identical_pages'] == [1, 2, 3, 4, 5]
    assert packaged_build['source_archive_sha256'] == manuscript_zip['sha256']

    research = set(manuscript)
    for folder in ['qkdsim', 'revision', 'experiments', 'tests']:
        research |= files_under(folder, {'.py'})
    research |= files_under('results/revision', {'.json', '.csv'})
    research |= files_under('figures/revision', {'.png', '.pdf', '.json'})
    research |= {p for p in (ROOT / 'docs/revision').glob('*')
                 if p.is_file() and p.suffix in {'.md', '.json'}}
    research |= files_under('docs/revision/delivery_checks', {'.md', '.json'})
    research |= files_under('docs/revision/audit_tools', {'.py'})
    research |= {p for p in (ROOT / 'tools').glob('*.py')}
    research |= {p for p in ROOT.glob('*.md') if p.name != 'AGENTS.md'}
    research |= {ROOT / n for n in ['.gitignore', 'requirements.txt', 'requirements-documents.txt']}
    research |= {ROOT / 'archive/manuscripts_before_revision' / name
                 for name in ['paper.tex', 'paper_extended.tex', 'abstract_new.tex']}
    research.add(ROOT / 'archive/code_before_revision_0d1e2fa.zip')
    research |= {p for p in (ROOT / 'results').glob('*')
                 if p.is_file() and p.suffix in {'.csv', '.json'}}
    research |= {ROOT / 'build/reviewer_compliance' / name
                 for name in ['build_pdf.py', 'verify_pdf.py']}
    for name in ['tectonic', 'pandoc']:
        research.add(ROOT / f'tools/{name}/release_provenance.json')
    final_names = ['Paper167_Manuscript.docx', 'Paper167_Manuscript.pdf', 'Paper167_LaTeX.pdf',
                   'Reviewer_Compliance.pdf', 'Research_Explained.docx', 'Research_Explained.pdf',
                   'READ_ME.md', 'Manuscript_Source.zip']
    research |= {OUT / name for name in final_names}
    missing = [str(p) for p in research if not p.is_file()]
    assert not missing, missing
    research_zip = make_zip('Research_Revision_Source.zip', research)
    with zipfile.ZipFile(OUT / research_zip['file']) as archive, fitz.open(OUT / 'Research_Explained.pdf') as guide:
        members = set(archive.namelist())
        local_links = [link for page in guide for link in page.get_links() if link.get('file')]
        targets = {posixpath.normpath(posixpath.join('submission', link['file'].replace('\\', '/')))
                   for link in local_links}
        missing_targets = [t for t in targets if t not in members
                           and not any(n.startswith(t.rstrip('/') + '/') for n in members)]
        assert not missing_targets, missing_targets
    final_names += ['Research_Revision_Source.zip']
    artifacts = []
    for name in final_names:
        path = OUT / name
        info = {'file': name, 'sha256': sha(path), 'bytes': path.stat().st_size}
        if path.suffix == '.pdf':
            info.update(pdf_info(path))
            assert info['all_fonts_embedded']
        if path.suffix == '.docx':
            with zipfile.ZipFile(path) as docx:
                assert docx.testzip() is None
        artifacts.append(info)
    report = {
        'verified_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'local_revision_complete',
        'scientific_source_hash': source_hash,
        'regression_tests': 127, 'legacy_internal_checks': 43,
        'test_failures': 0, 'test_errors': 0, 'test_skips': 0,
        'phase_verification': phase_checks,
        'artifacts': artifacts, 'archives': [manuscript_zip, research_zip],
        'manuscript_pdf_pages': pdf_info(OUT / 'Paper167_Manuscript.pdf')['pages'],
        'reviewer_compliance_pages': pdf_info(OUT / 'Reviewer_Compliance.pdf')['pages'],
        'beginner_guide_pages': pdf_info(OUT / 'Research_Explained.pdf')['pages'],
        'official_actionable_review_points_addressed': 21,
        'packaged_latex_build_verified': packaged_build,
        'guide_evidence_links_in_archive': {'annotations': len(local_links),
                                          'unique_targets': len(targets), 'all_present': True},
        'historical_upload_identity': 'Exact CMT-upload binary not established; both supplied reviews addressed and source versions distinguished.',
        'external_actions': {
            'pdf_express_certified': False, 'cmt_submitted': False,
            'copyright_transfer_completed': False, 'registration_completed_by_agent': False,
            'author_details_final_check': 'reserved_by_author_for_submission',
            'conference_id': '69954X', 'deadline_from_author_email': '2026-09-30',
        },
        'archive_scope': 'Private author handoff; no automatic public release. Historical authored notes are audit evidence only.',
    }
    assert report['manuscript_pdf_pages'] == 5 and report['beginner_guide_pages'] == 19
    path = OUT / 'DELIVERY_MANIFEST.json'
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    checksum_paths = [OUT / n for n in final_names] + [path]
    (OUT / 'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in checksum_paths), encoding='utf-8')
    print(json.dumps({'archives': report['archives'], 'page_counts': {
        'manuscript': report['manuscript_pdf_pages'], 'reviewer': report['reviewer_compliance_pages'],
        'guide': report['beginner_guide_pages']}, 'status': report['status']}, indent=2))


if __name__ == '__main__':
    main()
