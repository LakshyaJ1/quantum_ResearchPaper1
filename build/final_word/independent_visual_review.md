# Independent visual review of the six-page Word export

Reviewed on 28 September 2026. This review concerns the exact Microsoft Word export `submission/Paper167_Manuscript.pdf` and its editable source `submission/Paper167_Manuscript.docx`. Every page image at `build/final_word/visual/page-1.png` through `page-6.png` was opened at its original 1191 x 1684 pixel resolution. Each final PNG was compared byte for byte at the pixel level with a fresh 144 dpi PyMuPDF render of the corresponding current PDF page; all six matched. No Word or LibreOffice export was performed in this independent review.

The reviewed version is fixed by these SHA-256 hashes:

| File | SHA-256 |
|---|---|
| `paper.tex` | `65d3966f91dd1fdae8f115fb963c938fabb5a092501eabad829304035b7920a8` |
| `submission/Paper167_Manuscript.docx` | `66c060ff88465ada5b6c263cc0e1d07ce83c28db4c94477ea7e332ea131833ad` |
| `submission/Paper167_Manuscript.pdf` | `70e9aadb16a4140658eb919ca9ae7dd1a46cfb32895d82cbde6ffa56d42a60de` |

The final rendered PNG SHA-256 values are page 1 `8abcd4b18f941b5056784b6bf068ec22dc25c255428f62767a1b8ac739d63372`, page 2 `56c3c88e5b5b07454a83216b4382b08668432f00e4596147c0ec9e69b790566a`, page 3 `354e737413bcca207df533ac43f91ddeb3291f8ceb4d6af519a9f5184111e03d`, page 4 `2b0eeab73df88b9d70f30c34002e09ba8d5264b30578ba26335e8aad5b99a023`, page 5 `732943b173737e94ba8d4f749a0c1421d19b763aafd1c2cc140bc6c0d218e343`, and page 6 `f7a4773939f9f5d1628c8c10c20d4841820c1b3f7b39aa2e4bfce37564725538`. Pages 1-5 are pixel-identical to the first six-page export that was fully inspected. Page 6 changed after its final-column balancing and was inspected again in full.

Page 1: The title, three named authors, superscripts, affiliations, emails, abstract, index terms, Introduction, Related Work, first model heading, and equation (1) are visible. Both columns flow within the page. The abstract is dense but readable.

Page 2: Equations (2) through (5), including fractions, subscripts, summation limits and inequality signs, are legible. The grade/debit, common-denominator and cut-bound text continues without clipping or column collision. The inline payload-exposure formula wraps within the right column while remaining readable.

Page 3: Equation (6), its floor notation, policy details, scenario assumptions and verification method render clearly. Section IV continues across both columns with no missing visible paragraph or overlap.

Page 4: Figure 1, Table I, Table II and Figure 2 appear with complete captions. Legends, interval bars, data rows and confidence intervals are readable at the inspected resolution. Each table has three unsplit data rows. Text flows from the bottom left into the top right without a visible break.

Page 5: Table III has three complete data rows and a readable caption; Figure 3's axes, error bars, labels and caption are visible. Target-persistence, learning, key-establishment and discussion text remain within both columns. No figure overlays surrounding prose.

Page 6: The discussion continues into the Conclusion and Reproducibility and Acknowledgement in the left column. References [1] through [13] are now grouped in the right column. The columns finish at comparable heights, resolving the conspicuous imbalance in the first six-page export. Reference [13]'s URL stays inside the column. All visible text remains readable and no content appears lost.

Across all six pages, extracted text spans remain inside a conservative 30-point side and 25-point top/bottom page box; text color is black and every referenced font has embedded data. The page images show no clipped text, overlapping objects, broken table continuation, unreadable figure label, or replacement glyph. These checks support visual legibility; the separate conversion audit establishes source/content parity.

**Outcome: passed for the exact source, DOCX, PDF and page-image hashes above.** The earlier page-6 imbalance is resolved. This local visual review does not claim IEEE PDF eXpress certification or conference submission. Any further document edit or export requires a new hash check and review of changed pages.
