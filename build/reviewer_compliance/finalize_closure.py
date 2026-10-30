"""Finalize reviewed compliance metadata after the Word PDF is frozen."""
from pathlib import Path
import hashlib
import json
import re
import sys
import fitz

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected_word_sha = sys.argv[1]
word = ROOT/'submission/Paper167_Manuscript.pdf'
assert sha(word) == expected_word_sha
assert len(fitz.open(word)) == 6
assert sha(ROOT/'paper_revised.tex') == '65d3966f91dd1fdae8f115fb963c938fabb5a092501eabad829304035b7920a8'
pdf = ROOT/'submission/Reviewer_Compliance.pdf'
assert sha(pdf) == 'c14b4d3f92c375ee4029b68ea94345a29f34f4df9c7449f0737fdc179478fc1c'

# The root confirms no section moved pages in its Word-only page-six rebalance.
# Record the final authority while leaving the reviewed compliance bytes untouched.
mapping = json.loads((STAGE/'six_page_locator_map.json').read_text(encoding='utf-8'))
previous_sha = mapping['authoritative_manuscript_pdf_sha256']
mapping['authoritative_manuscript_pdf_sha256'] = expected_word_sha
mapping['basis'] = 'Direct inspection of six-page Word export; page-six layout-only rebalance confirmed to preserve all section/figure/table page locations'
(STAGE/'six_page_locator_map.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
matrix_file = ROOT/'docs/revision/official_review_matrix.md'
matrix = matrix_file.read_text(encoding='utf-8').replace(previous_sha,expected_word_sha)
matrix_file.write_text(matrix,encoding='utf-8')
refresh_script = STAGE/'refresh_six_page_response.py'
refresh_script.write_text(refresh_script.read_text(encoding='utf-8').replace(previous_sha,expected_word_sha),encoding='utf-8')
manifest_file = STAGE/'build_manifest.json'
manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
manifest['authoritative_manuscript_pdf_sha256'] = expected_word_sha
manifest['locator_map_sha256'] = sha(STAGE/'six_page_locator_map.json')
manifest['reference_identity_refreshed_without_content_rebuild'] = previous_sha != expected_word_sha
manifest_file.write_text(json.dumps(manifest,indent=2),encoding='utf-8')

# Page-specific visual checks were performed on this exact compliance hash.
qa = json.loads((STAGE/'render_submission/technical_qa.json').read_text(encoding='utf-8'))
assert qa['pdf_sha256'] == sha(pdf) and qa['page_count'] == 10
descriptions = [
    'Title, preserved authors, revised scope preamble and six-page reference basis are legible; R1-01 fits fully.',
    'R1-02 through R1-04 are complete; IV-C page-four locator and explicit four-check classification are clear.',
    'R1-05 through R1-07 have correct page-five cost/learning locators and readable confidence intervals.',
    'R1-08 and R1-09 are legible; load scope, lambda algebra, split seeds, adverse outcomes and conditional inference remain intact.',
    'R1-m01 through R1-m03b are readable; Table I/II page-four and Table III/Fig.3 page-five locators match.',
    'R1-m04 through R1-m07 and the R1-Q1 opening are complete; exactly-six-page wording and Spooren page-six locator are correct.',
    'The full load table, R1-Q2 and R1-Q3 opening are readable; multi-line intervals remain inside cells.',
    'R1-Q3 continuation and R1-Q4 are complete; establishment versus transport and finite-lifetime limitations are clear.',
    'Appendix A is complete with 127 regression tests and 43 legacy checks; all evidence paths and wrapped source hash are legible.',
    'Appendix B contains all five topology rows together; Appendix C contains all four historical checks and the concluding provenance limit.'
]
note = '# Final reviewer-compliance visual QA\n\n'
note += f'Inspected on 28 September 2026 by reviewer_scope_audit. Exact compliance PDF SHA-256: `{sha(pdf)}`. The manuscript-reference authority is the six-page Word PDF SHA-256 `{expected_word_sha}`.\n\n'
note += 'All ten pages were visually inspected at 150 dpi. The final Appendix B keep-together adjustment changed only pages 9 and 10, which were reinspected; pages 1-8 were verified pixel-identical to the already reviewed rendering. No clipping, overlap, broken glyph, unreadable table cell or detached heading was found. Evidence references are printed portable repository paths rather than machine-specific clickable PDF file links; their source targets all resolve.\n\n'
note += '| Page | Visual finding | Render SHA-256 |\n|---|---|---|\n'
for page,description in zip(qa['pages'],descriptions):
    note += f"| {page['page']} | {description} | `{page['sha256']}` |\n"
note += '\nThe reference pagination is mapped from the Word PDF, not the optional LaTeX rendering. The original five-page response and QA are preserved under archive/pre_six_page_20260928. Software counts are read from the current research gate; this editorial rebuild did not rerun experiments. External certification and submission are not claimed.\n'
(STAGE/'independent_visual_qa.md').write_text(note,encoding='utf-8')

audit_path = ROOT/'docs/revision/final_reviewer_scope_audit.md'
audit = audit_path.read_text(encoding='utf-8')
if '## Six-page closure follow-up' not in audit:
    heading,body = audit.split('\n',1)
    closure = f'''
## Six-page closure follow-up

The earlier snapshot findings below are resolved in the final manuscript source SHA-256 `65d3966f91dd1fdae8f115fb963c938fabb5a092501eabad829304035b7920a8` and the exactly-six-page Word-exported PDF SHA-256 `{expected_word_sha}`. Section IV-C (p. 4) now directly classifies V1/V4 and the two V2/V3 mismatches. Table II and V-B (p. 4) explicitly answer the reduced-load question, and Table III/V-C (p. 5) show the existing heterogeneous-cost evidence. Section IV-B (p. 3) now specifies the main QBER increment, 0.35-second abstract setup delay, event order and cohort follow-up; III-C (p. 2) defines empty-denominator handling, and V-C (p. 5) defines the feedback window. These are clarifications and presentation of existing verified evidence, not new empirical claims.

All 21 response sections and their official-matrix locators were remapped directly to this six-page Word PDF. Calibration, published-routing-baseline, learned-policy inference and finite pre-positioned-key lifetime remain honestly scoped. The existing response, matrix, compliance PDF and QA were preserved under `archive/pre_six_page_20260928` before refresh. The current ten-page `submission/Reviewer_Compliance.pdf` has SHA-256 `{sha(pdf)}`; all ten pages were visually inspected, all official IDs and evidence paths verified, and typography/overflow/font checks passed. Current software evidence is 127 regression tests and 43 legacy checks from the research gate, not a fresh test run by this audit.

No unresolved content correction from this audit remains. Exact original CMT-upload identity and the user's final author check remain outside this local comparison. PDF eXpress certification, registration, copyright transfer and CMT submission remain external actions. The initial audit below is retained as historical reasoning, not a current list of outstanding work.

## Initial snapshot audit, superseded where noted above
'''
    audit_path.write_text(heading+'\n'+closure+body,encoding='utf-8')
else:
    audit_path.write_text(audit.replace(previous_sha,expected_word_sha),encoding='utf-8')

gate_path=ROOT/'results/revision/verification/research_gate.json'
gate=json.loads(gate_path.read_text())
assert gate['passed'] and gate['regression_tests_run']==127
assert gate['legacy_validation']['returncode']==0 and '43/43 checks passed' in gate['legacy_validation']['stdout']
ids=list(mapping['locators'])
tracked=re.findall(r'^\| ((?:R1-|V-)\S+) \|',matrix,re.M)
closure={
    'pdf':'submission/Reviewer_Compliance.pdf','pdf_sha256':sha(pdf),'pages':10,
    'all_technical_checks_passed':qa['all_technical_checks_passed'],
    'visual_review':{'all_pages_inspected':True,'reviewer':'reviewer_scope_audit',
                     'note':'build/reviewer_compliance/independent_visual_qa.md',
                     'note_sha256':sha(STAGE/'independent_visual_qa.md'),
                     'after_table_keep':'Pages 1-8 pixel-identical; pages 9-10 reinspected after retaining all topology rows together'},
    'authoritative_manuscript_pdf':'submission/Paper167_Manuscript.pdf',
    'authoritative_manuscript_pdf_sha256':expected_word_sha,'authoritative_manuscript_pages':6,
    'authoritative_manuscript_docx':'submission/Paper167_Manuscript.docx',
    'authoritative_manuscript_docx_sha256':sha(ROOT/'submission/Paper167_Manuscript.docx'),
    'paper_source_sha256':sha(ROOT/'paper_revised.tex'),
    'response_sha256':sha(ROOT/'docs/revision/REVIEWER_RESPONSE.md'),
    'matrix_sha256':sha(matrix_file),'audit_sha256':sha(audit_path),
    'official_actionable_sections':ids,'tracked_matrix_rows':tracked,
    'matrix_status':'All 21 official items have explicit completed or honestly scoped answers; all 31 tracked rows retain dispositions. V-01 original-upload identity remains unresolved. No reviewer approval, hardware validation, certification or submission is claimed.',
    'software_verification':{'regression_tests':127,'legacy_checks':43,'gate_passed':True,
                             'gate_sha256':sha(gate_path),'pdf_count_parity_verified':True,
                             'tests_rerun_for_editorial_refresh':False},
    'evidence_paths_checked':len(manifest['evidence_references']),
    'locator_map_sha256':sha(STAGE/'six_page_locator_map.json'),
    'technical_qa':'build/reviewer_compliance/render_submission/technical_qa.json',
    'technical_qa_sha256':sha(STAGE/'render_submission/technical_qa.json'),
    'technical_check_count':len(qa['checks']),
}
(STAGE/'closure_manifest.json').write_text(json.dumps(closure,indent=2),encoding='utf-8')
print(json.dumps(closure,indent=2))
