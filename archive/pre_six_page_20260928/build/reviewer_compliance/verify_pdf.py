"""Read, render and verify the exact final reviewer-compliance artifact."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata
import fitz

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
PDF = ROOT/'submission/Reviewer_Compliance.pdf'
OUTPUT = STAGE/'render_submission'
OUTPUT.mkdir(exist_ok=True)
doc = fitz.open(PDF)
pages, fonts, bounds, texts = [], {}, [], []
colors = set()
for number, page in enumerate(doc, 1):
    text = page.get_text()
    texts.append(text)
    for font in page.get_fonts(full=True):
        if font[0] not in fonts:
            name, extension, kind, data = doc.extract_font(font[0])
            fonts[font[0]] = dict(name=name, extension=extension, kind=kind,
                                  embedded_bytes=len(data))
    for block in page.get_text('dict')['blocks']:
        if block.get('type') != 0:
            continue
        for line in block['lines']:
            for span in line['spans']:
                colors.add(span['color'])
                x0, y0, x1, y1 = span['bbox']
                if x0 < 34 or x1 > page.rect.width-34 or y0 < 20 or y1 > page.rect.height-25:
                    bounds.append(dict(page=number,text=span['text'],bbox=span['bbox']))
    image = OUTPUT/f'page-{number:03d}.png'
    page.get_pixmap(dpi=150).save(image)
    pages.append(dict(page=number,words=len(text.split()),image=str(image.relative_to(ROOT)),
                      sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                      width=page.rect.width,height=page.rect.height))
combined = '\n\f\n'.join(texts)
normalized_text = re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', combined))
(OUTPUT/'text.txt').write_text(combined,encoding='utf-8')
ids = sorted(set(re.findall(r'R1-(?:\d\d|m\d\d[a-b]?|Q[1-4])',combined)))
expected = {f'R1-{n:02}' for n in range(1,10)}
expected |= {'R1-m01','R1-m02','R1-m03a','R1-m03b','R1-m04','R1-m05','R1-m06','R1-m07'}
expected |= {f'R1-Q{n}' for n in range(1,5)}
checks = dict(all_official_ids=set(ids)==expected,
              all_fonts_embedded=all(f['embedded_bytes']>0 for f in fonts.values()),
              no_page_overflow=not bounds, all_text_black=colors=={0},
              no_replacement_glyphs='\ufffd' not in combined,
              no_broken_file_links=not any(page.get_links() for page in doc),
              all_pages_a4=all(abs(p.rect.width-595.28)<.1 and abs(p.rect.height-841.89)<.1 for p in doc),
              no_working_labels=not re.search(r'Pending|TODO|sec:|fig:|tab:',combined),
              correct_reference_basis='authoritative five-page manuscript PDF' in normalized_text)
log = (STAGE/'pdf_build/Reviewer_Compliance.log').read_text(errors='replace')
checks['no_latex_overfull_or_missing_glyphs'] = not re.search(r'^Overfull|Missing character',log,re.M)
manifest = json.loads((STAGE/'build_manifest.json').read_text())
checks['source_matches_manifest'] = hashlib.sha256((ROOT/manifest['source']).read_bytes()).hexdigest()==manifest['source_sha256']
checks['primary_manuscript_matches_manifest'] = hashlib.sha256((ROOT/manifest['authoritative_manuscript_pdf']).read_bytes()).hexdigest()==manifest['authoritative_manuscript_pdf_sha256']
gate = json.loads((ROOT/'results/revision/verification/research_gate.json').read_text())
checks['regression_count_matches_current_gate'] = (
    gate['passed'] and f"{gate['regression_tests_run']} regression tests" in normalized_text)
result = dict(pdf=str(PDF.relative_to(ROOT)),pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
              page_count=len(doc),pages=pages,fonts=list(fonts.values()),text_colors=sorted(colors),
              official_ids=ids,bounds=bounds,checks=checks,all_technical_checks_passed=all(checks.values()))
(OUTPUT/'technical_qa.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('pages','fonts','bounds','official_ids')}))
raise SystemExit(0 if all(checks.values()) else 1)
