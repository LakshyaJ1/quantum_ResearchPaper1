# Research explainer final verification

The corrected guide was rebuilt on 26 September 2026 at 02:16:39 UTC and delivered as `submission/Research_Explained.pdf` and `submission/Research_Explained.docx`. The PDF has 19 A4 pages. Both final files pass technical verification and complete visual review. No internal-preview label or pending scientific work language remains. Author confirmation, PDF eXpress, copyright and conference submission remain clearly identified as separate external steps.

## Content corrections and evidence

The final source distinguishes initial usable fill at a fixed 50 Mibit capacity from changing reservoir capacity. It includes the verified three-path rate-shape counterexample: excess QBER 0.04 and abort threshold 0.075 produce zero entitled-arrival forced loss for gamma 1, versus 83.469 percent with a marginal 95 percent interval of 82.670 to 84.343 percent for illustrative gamma 3.4 across six seeds. It labels this model sensitivity rather than measured physics or independent calibration. The values were checked against `results/revision/analysis/threshold_summary.csv`.

The guide explains main, fallback, canonical sensitivity, threshold, frozen-policy learning, online-adversary, and disjoint-seed persistence evidence. Counts distinguish requested, cached, canonical and unique rollout records. It does not treat all paired runs as independent subjects. The learned-score, entitled-payload and ISR trade-off is explicit, together with metric denominators, runtime commitment caps and contractual exposure versus actual compromise. A separate read-only content review checked the numerical and protocol summaries against their completed reports and paired CSVs.

The final manuscript link points to `paper.tex`; the original source is linked separately through `archive/manuscripts_before_revision/paper.tex`. Both existing plots are included. The guide contains no claim of hardware validation or completed external submission.

## Final full page inspection

The fresh reviewer `/root/explainer_finalize/guide_content_check` opened every final page PNG from 1 through 19 at original resolution. Its record confirms clear equations, complete plots and captions, repeated table headers, intact rows, correct page numbers, and no observed layout defects. Page 14 clearly renders both gamma values, F_N and the rate-shape interval. The review used the exact final manifest and verified submission file and page-image identities. No old contact sheet or preview page was substituted for final-page inspection.

The final Word file retains 54 native OMML equations, three editable tables and two embedded plots. The embedded PNG bytes match the verified source plots. All PDF fonts are embedded. Text-bound checks found no spans outside any page. The DOCX archive CRC check passed. All 23 internal contents links have valid destinations; all 49 local DOCX relationships and 77 PDF file annotations resolve to existing targets from the actual `submission` directory. No local path was converted into a web URL.

## Exact final artifacts

| Artifact | SHA-256 |
|---|---|
| Markdown source | `7c8a4e4aac35ff2a3f95091fa9972831318ed1b17cd4681d746764513ec56acd` |
| Builder | `70cd383e74429a61765375e348711f0b0f8730edb79bfe7fb87c72735896b08e` |
| Final PDF | `45db3625ff23e6ae6a58e2ff7ba7c2ab22643410cc8add6571a5003b6209c10f` |
| Final editable DOCX | `72be7b801fd6ad8032ef289e5af42ec573feb3ed2213eaeded25851c609f7fa4` |

The durable technical record is `docs/revision/explainer_delivery_verification.json`; the independent visual record is `docs/revision/explainer_final_visual_review.json`. The active build manifest and page images remain under `tools/explainer_preview`, despite that directory's historical name. Its manifest explicitly records `internal_preview: false`, final submission paths and completed visual review. Earlier preview-only records are superseded.

## Rebuild and scope

The final rebuild command was `C:/Python312/python.exe -X utf8 -u tools/build_explainer.py --final`. The documented fallback uses portable Pandoc and an isolated hidden Word instance. The builder stages the files under `tools/explainer_preview`; exact copies were placed into `submission` and checked there. Scientific implementation and result files were not edited. Future source changes require another final build and visual review of every changed page, with unchanged pages checked against previously reviewed renders. The guide is independent of the manuscript's four-to-six-page limit.

## Final consistency rebuild

The guide now reports 127 regression tests, matching the current research gate. The repository inventory describes abstract_new.tex as the exact expanded revised abstract and paper_extended.tex as the compatibility entry point that inputs paper.tex; superseded originals remain in archive/manuscripts_before_revision. Existing link destinations and the guide design were preserved.

Every page was rerendered and compared by raw pixel SHA256 with the prior full review. Pages 16, 18 and 19 changed and were inspected in full at original resolution. Page 16 shows the corrected test count; page 18 shows both current file descriptions; page 19 retains its repeated table header, complete rows and clean ending. The other 16 pages are pixel-identical to the previously reviewed final pages. No clipping, overlap, broken row or missing glyph was found. The guide remains 19 A4 pages, with all fonts embedded and no out-of-page text. All 23 internal links, 77 PDF file annotations and 49 DOCX local relationships were checked again, and all local targets exist from submission. Both embedded plot byte sequences are unchanged.

The refreshed JSON records and active build manifest hold the current source, PDF, DOCX and page-image hashes. The previous review is retained only as the explicit basis for unchanged-page pixel identity; its old artifact hashes are not presented as the current approval. Main manuscript and scientific result files were unchanged.
