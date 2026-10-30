# Working Word preview verification

This is an early layout and conversion preview, not a camera-ready deliverable. The working source still awaits additional sensitivity and learning results. Nothing was copied into a submission package or uploaded.

The preview is `paper_revised.docx` with its actual Microsoft Word export `paper_revised.pdf` in this directory. The PDF is **four A4 pages**. All four pages were visually inspected; after the final nonbreaking numeric-sign adjustment, page 3 was inspected again and the other three page images were pixel-identical to the already-reviewed pages.

The source snapshot is `paper_revised.tex` SHA-256 `4ddee85d50b6741850981ab66c6b512aa7fa4e8bf0108c7007c42a11d357eef2`; AUX SHA-256 is `1849f735ee600b441a7aa6b50c01ddd449d5c913c870bdd06957551a789472c3`. The included numerical macros and class table each have a separate hash in `staging/conversion_manifest.json`. The source manuscript was not edited by the conversion.

The conversion preserves the full three-author block and affiliations, all 13 bibliography entries and citation numbers, one research figure with its caption, and the class table's nine mean/interval cells. There are **six** numbered display equations in this source/AUX snapshot, numbered 1-6, and 46 native Office Math objects including inline formulas and table-header symbols. The 46 mathematical objects are canonically identical before and after styling; the display equations remain editable and retain display-style fractions and summation limits.

The canonical Pandoc source-to-DOCX audit found **zero missing non-math prose or numeric tokens** among 3,282 expected tokens. The extra tokens are the intended abstract label and section/equation numbering. This count audit supplements, rather than replaces, visual inspection and mathematical review. Every font used in the Word PDF is embedded. Detailed records are in `preview_qa.json`, `staging/nonmath_token_parity.json`, and `staging/native_math_parity.json`.

The converter now expands generated `input` files recursively, resolves `graphicspath`, handles nested AUX section labels, preserves `shortstack` confidence-interval line breaks, and keeps negative values together. The initially narrow class-label column, inline-style display mathematics, table-border artifacts and blue URL styling were corrected. Numbered equations use borderless layout rows to keep the equation number inside the column; these six layout rows are counted separately from the single research-data table.

There is no remaining unsupported feature in this snapshot. The general converter still refuses numbered `align`, `gather` and `multline` environments rather than guessing their row numbers. New source constructs or additional figures must be checked on the next conversion.

Four pages leave two pages within the stated six-page maximum. Another roughly 600 words and two column-width figures of similar height to the existing figure are plausibly a five- to six-page Word manuscript. This is a layout estimate, not a measured result for the future content; actual final figure dimensions, captions, tables and equation wrapping determine the final count. No placeholder content was inserted to manufacture a fit estimate.

The final pass must rerun conversion from the completed LaTeX and fresh AUX, compare the final contents and numerical values, inspect every rendered page, and confirm 4-6 pages. Local Word PDF export and embedded-font checks are not PDF eXpress validation.
