"""Pin the final response and matrix to the inspected six-page Word PDF."""
from pathlib import Path
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
SOURCE_SHA = '65d3966f91dd1fdae8f115fb963c938fabb5a092501eabad829304035b7920a8'
PDF_SHA = '70e9aadb16a4140658eb919ca9ae7dd1a46cfb32895d82cbde6ffa56d42a60de'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/'paper_revised.tex') == SOURCE_SHA
assert sha(ROOT/'submission/Paper167_Manuscript.pdf') == PDF_SHA
assert len(fitz.open(ROOT/'submission/Paper167_Manuscript.pdf')) == 6

locators = {
'R1-01': 'Sections III-D (p. 2), IV-B (p. 3) and V-A-B (pp. 4-5); Figs. 1-2 and Tables I-II (p. 4).',
'R1-02': 'Abstract (p. 1), Section III-C (p. 2), Section V-A (p. 4), Table I and Fig. 1 (p. 4).',
'R1-03': "Section IV-C (p. 4), Section VI (pp. 5-6), and this response's Appendix C.",
'R1-04': 'Section III-B (p. 2), Sections IV-B-C (pp. 3-4) and Section V-B (pp. 4-5).',
'R1-05': 'Section IV-B (p. 3), Section V-C and Table III (p. 5).',
'R1-06': 'Section III-C (p. 2), Section IV-B (p. 3) and Section V-B (pp. 4-5).',
'R1-07': 'Section III-C (p. 2), Table I (p. 4), Section V-D and Fig. 3 (p. 5).',
'R1-08': 'Section III-B (p. 2), Sections IV-A-B (pp. 2-3), Section V-B (pp. 4-5), and Tables I-II (p. 4).',
'R1-09': 'Section IV-A (pp. 2-3), Section V-D and Fig. 3 (p. 5), and Section VI (pp. 5-6).',
'R1-m01': 'Section III-A, Eq. (2) (p. 2), and Section V-B (pp. 4-5).',
'R1-m02': 'Section IV-B (p. 3), Sections V-C and V-E (p. 5).',
'R1-m03a': 'Section IV-B (p. 3), Tables I-II and Figs. 1-2 (p. 4), and Table III and Fig. 3 (p. 5).',
'R1-m03b': 'Table I (p. 4), Section V-D (p. 5), and the complete per-class artifact tables.',
'R1-m04': 'Section II (p. 1).',
'R1-m05': 'Section III-A (pp. 1-2), Section V-E (p. 5), and replacement result Figs. 1-3 (pp. 4-5).',
'R1-m06': 'Sections I-VII and references, within the six-page revised manuscript.',
'R1-m07': 'Section I (p. 1) and reference [3] (p. 6).',
'R1-Q1': 'Section III-B (p. 2), Section V-B and Table II (pp. 4-5; table on p. 4), plus the matched load table in this response.',
'R1-Q2': 'Section III-A, Eq. (2) (p. 2), Section III-D (p. 2), and Section V-B (pp. 4-5).',
'R1-Q3': 'Section V-C (p. 5) and Section VI (pp. 5-6).',
'R1-Q4': 'Section III-A (pp. 1-2), Section IV-B (p. 3), and Section V-E (p. 5).',
}

for rel in ['docs/revision/REVIEWER_RESPONSE.md','docs/revision/official_review_matrix.md']:
    original = ROOT/rel
    archived = ROOT/'archive/pre_six_page_20260928'/rel
    assert archived.exists(), f'Missing preserved predecessor: {archived}'
    # Rebuild from the preserved predecessor, making this refresh deterministic.
    text = archived.read_text(encoding='utf-8')
    if original.name == 'REVIEWER_RESPONSE.md':
        def section(m):
            block = m.group(0)
            item = re.match(r'## (R1-[^:]+):',block).group(1)
            return re.sub(r'Revised manuscript: [^\n]+', 'Revised manuscript: '+locators[item],block,count=1)
        text = re.sub(r'^## R1-.*?(?=^## |\Z)',section,text,flags=re.M|re.S)
        text = text.replace('authoritative five-page manuscript PDF','authoritative six-page manuscript PDF')
        text = text.replace('The revised manuscript contains five pages, including references.',
                            'The revised manuscript contains exactly six pages, including references. Tables II and III bring the existing load and heterogeneous-cost comparisons into the paper; no new experiment is implied by this presentation change.')
        text = text.replace('The revision addresses the nine main concerns, eight separately tracked minor comments, and four explicit questions in the official attachment.',
                            'The revision responds to the nine main concerns, eight separately tracked minor comments, and four explicit questions in the official attachment through implemented corrections, completed comparisons, and explicit limits where broader calibration or deployment claims are unsupported.')
        text = text.replace('Appendix C preserves their historical numbers',
                            'Section IV-C of the manuscript states these four dispositions directly. Appendix C preserves their historical numbers')
        text = text.replace('The class table now shows', 'The manuscript class table (Table I) now shows')
        text = text.replace('The main class table, revised figures and this response report seed-bootstrap intervals.',
                            'The main class table, new load/cost tables, revised figures and this response report seed-bootstrap intervals. Table II displays the paired availability-gap interval; Table III displays an interval for every loss mean.')
    else:
        lines = []
        for line in text.splitlines():
            m = re.match(r'\| (R1-[^ |]+) \|',line)
            if m:
                item = m.group(1)
                assert 'Final locator: ' in line
                line = re.sub(r'Final locator: .*? \|$', 'Final locator: '+locators[item]+' |',line)
                if item == 'R1-03':
                    line = line.replace('Response Appendix C and literature_verified.md.', 'The paper now states V1/V4 limits and V2/V3 mismatches directly in IV-C; response Appendix C and literature_verified.md preserve provenance.')
                if item == 'R1-09':
                    line = line.replace('| Addressed. Crossing', '| Addressed through reframing and bounded learning evidence. Crossing')
                if item == 'R1-m06':
                    line = line.replace('contain five pages','contain exactly six pages')
                if item == 'R1-Q1':
                    line = line.replace('Response R1-Q1.', 'The matched trend now appears in manuscript Table II and V-B; response R1-Q1 preserves complete values.')
                if item == 'R1-05':
                    line = line.replace('Response R1-05/Q3.', 'Manuscript Table III shows the static/residual/cut comparison; response R1-05/Q3.')
            lines.append(line)
        text = '\n'.join(lines)+'\n'
        text = text.replace('These requirements supersede the earlier unverified local six-page assumptions.',
                            'The latest explicit user instruction selects exactly six pages within that permitted range; earlier local assumptions are not the authority for either requirement.')
        text = text.replace('six equations, three figures, thirteen references', 'six equations, three figures, three result tables, thirteen references')
        text = text.replace('The final Word manuscript and its matching PDF have five pages and passed content/visual verification.',
                            'The final Word-exported PDF has exactly six pages. Its page-specific reviewer locators are remapped to the hash-identified final file below; document parity and visual verification remain recorded by the separate document-delivery workflow.')
        start = text.index('Section, equation, figure and table identities were verified')
        end = text.index('The 1,264-record sensitivity batch',start)
        text = text[:start]+f'''Section, equation, figure and table identities were checked against the final source. Page locators were mapped directly from the authoritative six-page `submission/Paper167_Manuscript.pdf`, exported from the final Word file (SHA-256 `{PDF_SHA}`). The corresponding `paper_revised.tex` SHA-256 is `{SOURCE_SHA}`. The optional LaTeX PDF is not the page-reference basis.

| Object | Final locator |
|---|---|
| Abstract, introduction and related work | Page 1 |
| Model and stored-key failure surfaces | Section III, pp. 1-2; III-A, pp. 1-2; Eq. (1), p. 1; Eq. (2), p. 2 |
| Grades and debits | Section III-B, p. 2; Eq. (3), p. 2 |
| Common-denominator outcomes | Section III-C and Eq. (4), p. 2 |
| Finite cut-budget check | Section III-D and Eq. (5), p. 2 |
| Policies and experimental protocol | Section IV, pp. 2-4; IV-A, pp. 2-3; Eq. (6), p. 3 |
| Scenario and uncertainty protocol | Section IV-B, p. 3 |
| Historical and implementation verification scope | Section IV-C, p. 4 |
| Main service comparison | Section V-A, p. 4; Table I, p. 4; Fig. 1, p. 4 |
| Reserve and operating envelope | Section V-B, pp. 4-5; Table II and Fig. 2, p. 4 |
| Target persistence and attack cost | Section V-C and Table III, p. 5 |
| Learning and exposure trade-off | Section V-D and Fig. 3, p. 5 |
| Key establishment versus transport | Section V-E, p. 5 |
| Discussion and conclusion | Section VI, pp. 5-6; Section VII, p. 6 |
| Reproducibility and acknowledgement | Page 6 |
| References, including Spooren | References [1]-[13], p. 6; Spooren is [3] |

'''+text[end:]
    assert not re.search(r'five[- ]page|five pages',text)
    original.write_text(text,encoding='utf-8')

(STAGE/'six_page_locator_map.json').write_text(json.dumps({
    'authoritative_manuscript_pdf':'submission/Paper167_Manuscript.pdf',
    'authoritative_manuscript_pdf_sha256':PDF_SHA,
    'paper_source_sha256':SOURCE_SHA,'pages':6,'basis':'Direct page text inspection of final Word export',
    'locators':locators},indent=2),encoding='utf-8')
print(json.dumps({'updated_response_sha256':sha(ROOT/'docs/revision/REVIEWER_RESPONSE.md'),
                  'updated_matrix_sha256':sha(ROOT/'docs/revision/official_review_matrix.md')}))
