# Current compliance build

The current required deliverable is `submission/Reviewer_Compliance.pdf`. Its identity, final six-page Word-manuscript authority, response/matrix hashes and software-count evidence are recorded in `closure_manifest.json`.

`render_submission/technical_qa.json` and `independent_visual_qa.md` are the current technical and complete visual review records. All ten compliance pages were inspected. The older `render/` and `render_final/` directories are historical intermediate renderings and must not be used as current QA. The complete predecessor is preserved under `archive/pre_six_page_20260928/build/reviewer_compliance/`.

`six_page_locator_map.json` maps all 21 official response sections directly to the final Word-exported manuscript PDF. The optional LaTeX PDF is not its pagination authority. Evidence paths in the compliance PDF are portable printed paths; the builder verifies their source targets exist rather than emitting machine-specific file hyperlinks.

`build_pdf.py` generates the PDF from `docs/revision/REVIEWER_RESPONSE.md`; `verify_pdf.py` checks the exact output and renders every page. `refresh_six_page_response.py` reconstructs the six-page response/matrix from preserved predecessors and a fixed locator map. `finalize_closure.py` binds the reviewed response to the explicit final Word-PDF hash. A future content or pagination change requires renewed mapping, build and visual review, not merely replacement of hashes.

The final editorial refresh reads 127 regression tests and 43 legacy checks from the current research gate; it does not rerun scientific experiments. PDF eXpress certification and CMT submission remain external actions.
