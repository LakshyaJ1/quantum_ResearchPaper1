# Manuscript build environment

Prepared and tested locally on 26 September 2026. The tests in this record are isolated toolchain fixtures, not verification of the final research manuscript or IEEE PDF eXpress approval.

## Working local paths

| Component | Verified status | Path and version |
|---|---|---|
| Python | Available; `docx`, `lxml`, `fitz`, `win32com` imported successfully. | `C:\Python312\python.exe`, Python 3.12.9 |
| Microsoft Word | Invisible isolated COM instance successfully opened an editable DOCX, repaginated it and exported PDF, then closed only that instance. | `C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE`, COM version 16.0 |
| Tectonic | Official portable binary downloaded, release digest checked, A4 IEEEtran fixture compiled successfully. | `tools/tectonic/tectonic.exe`, 0.17.0 |
| Tectonic resource cache | Kept within the workspace. First format initialization needed several minutes; cached builds then completed in seconds. | `tools/tectonic_cache`, selected with `TECTONIC_CACHE_DIR` |
| IEEEtran | Class and conference sample extracted from the CTAN package. | `docs/revision/sources/ieee_ctan_package.zip`; fixture class at `tools/manuscript_smoke/IEEEtran.cls` |
| Pandoc | Official portable binary downloaded, digest checked, native OMML math and editable tables tested. | `tools/pandoc/pandoc.exe`, 3.11 |
| PDF raster inspection | PDF opened successfully and every fixture page rendered to PNG. | PyMuPDF through `fitz` |
| Packaged document dependency loader | Not exposed in this session's tool list; no managed Python/Node runtime was located. | This task uses the authorized installed Python/Word fallback. |
| Packaged `render_docx.py` | Source inspected. On Windows it selects installed LibreOffice; the skill forbids using the user's desktop LibreOffice, so that route was not executed. | Native Word export followed by PyMuPDF page rendering supplied the visual verification loop. |

No system-wide package installation, account login, public upload, PDF eXpress submission or visible Word window was requested. The templates, test files, dependencies and build cache are local to this workspace; existing user Word documents were not opened or modified.

## Download provenance

| Artifact | Official distribution URL | Archive bytes | SHA-256 |
|---|---|---:|---|
| Tectonic 0.17.0 Windows MSVC | `https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip` | 21,060,223 | `f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f` |
| Pandoc 3.11 Windows x86_64 | `https://github.com/jgm/pandoc/releases/download/3.11/pandoc-3.11-windows-x86_64.zip` | 41,761,100 | `2ab72baf2399450e148ddf7a2a8689806c42e1bba71862b57e220fd9b8456d3d` |
| CTAN IEEEtran | `https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip` | 1,727,001 | `e0cd4f5afbd42c8076092280e72b3e0a5111efe501d35de9f715cfb8da313cb4` |

The two executable release manifests are saved beside their executables as `release_provenance.json`. Their combined compressed download is about 63 MB; Tectonic additionally fetches only needed bundle resources. Extracted executables, caches and fixtures occupy more disk space than the compressed download. No complete TeX Live installation was downloaded.

## A4 typography and geometry

The Tectonic-compatible IEEE preamble is:

```latex
\RequirePackage[T1]{fontenc}
\documentclass[conference,a4paper]{IEEEtran}
```

Placing T1 font encoding before the class prevents IEEEtran's legacy `ptm` font selection from falling back under Tectonic's default Unicode encoding. The first uncorrected fixture silently substituted Latin Modern and lost font shapes; the corrected fixture has zero LaTeX font warnings and embeds Nimbus Roman, a Times-compatible family, with the mathematical fonts. This is a build-compatibility change, not a manuscript-content change.

The class-reported A4 geometry was `paperwidth=597.50787pt`, `paperheight=845.04684pt`, `textwidth=516pt`, `textheight=672pt`, `columnsep=12pt`, `oddsidemargin=-31.51605pt`, `topmargin=-55.7659pt`, `headheight=12pt`, and `headsep=18.45703pt` (TeX points). The Word converter derives its text width, column gap and body height from these values; page size is 210 by 297 mm. TeX points use 72.27 points/inch, while PDF points use 72 points/inch; the small reported PDF rounding difference between renderers is expected.

The Word converter uses 10-point Times New Roman body text, a 24-point title, 9-point abstract/keywords, 8-point captions/references, and editable native Office Math. It removes inherited theme font references, paragraph borders and generic title decoration. Table grid and individual cell widths are both set; setting only grid widths leaves oversized default Word cells. Wide figures use explicit continuous section transitions, and a one-column title/author block precedes the two-column body.

This is a class-derived Word layout, **not a downloaded official IEEE Word template**. The official IEEE page and standard direct Word-template paths returned empty HTTP 202 responses; a browser attempt failed with `Codex auth token is unavailable`. The user-supplied camera-ready email and IEEEtran class are the present format authority.

## Tested commands

Run the tool probe or isolated fixtures from the repository root:

```powershell
python -X utf8 -u tools/prepare_manuscript_tools.py
python -X utf8 -u tools/prepare_manuscript_tools.py --smoke
```

Compile a source while keeping AUX labels and logs, using the helper to set the workspace cache:

```powershell
python -X utf8 -u -c "from pathlib import Path; from tools.prepare_manuscript_tools import compile_tex; print(compile_tex(Path('paper.tex').resolve(), Path('build/latex').resolve()))"
```

The output directory must not be a directory named `latex` inside the source's working directory: the default Tectonic format name is `latex`, and a same-named local directory can shadow it and produce Windows access-denied. A separate `build/latex` directory under the repository is safe when the source itself is in the repository root; the isolated fixture uses `latex_output`.

Convert the compiled source into editable Word using the **fresh** AUX file:

```powershell
python -X utf8 -u tools/convert_manuscript_word.py paper.tex --aux build/latex/paper.aux --output output/paper.docx --stage build/word
```

Export that exact Word file through the hidden Word instance:

```powershell
python -X utf8 -u tools/prepare_manuscript_tools.py --render-word output/paper.docx --pdf-out output/paper_from_word.pdf
```

The Word-derived PDF is the relevant local candidate when the conference asks for a PDF corresponding to the Word manuscript. The separately compiled LaTeX PDF is a useful content/layout reference, not a substitute for checking the Word export.

## Conversion fidelity and limitations

`tools/convert_manuscript_word.py` creates a staging LaTeX representation without editing the manuscript. It resolves citations and references from the compiled AUX map, preserves author/affiliation macros, converts PDF figures to high-resolution PNG copies, retains editable Word tables and native equations, and records source/AUX/output hashes in `conversion_manifest.json`. Paragraph/figure order may differ from LaTeX's floated page positions, while the content and numbering remain tied to the same source.

Generated LaTeX input files are expanded recursively and hashed, declared graphic paths are resolved, and short stacked table cells preserve their internal line breaks. Ordinary numbered equations retain the original display-style OMML in borderless layout rows with separate equation-number cells. These layout rows are recorded separately from research-data tables; converting display mathematics to inline layout would change fraction size and summation-limit placement.

The complete isolated fixture successfully exercised author superscripts and affiliations, inline and numbered display equations, an editable table, numbered bibliography/citations, section/equation/table/figure cross-references, one column-width figure and one wide figure. The resulting Word PDF was one A4 page with all fonts embedded; its page was visually inspected and no clipping, missing glyphs, colored title rule or conversion-control markers remained. The fixture is under `tools/manuscript_smoke/full_parity_fixture*`, with its conversion record under `full_parity_stage/`.

Numbered `align`, `gather` and `multline` environments currently stop conversion with a clear error rather than guessing row numbering. Ordinary `equation`, unnumbered display math and inline math are supported. An unlabeled numbered equation uses its sequence position; any mixed numbered environment requires extending and checking that mapping. Final content parity must include every equation, table entry, figure, caption, bibliography item, and author line, not just matching counts. Footnotes and unusual custom commands require inspection if the actual source contains them.

## Diagnosed environment hazards

The root revision agent isolated native Python exit `0xe0000027` to `platform.platform()`/Windows version probing through WMI; it could terminate later during unrelated work. The tools here avoid that call and use `sys.getwindowsversion()` and `os.name`. Direct script execution worked after the change, including the full Pandoc download. A partially downloaded Tectonic archive was replaced with a complete official download and checked against the release digest before extraction/execution.

The first Tectonic cache initialization exceeded the initial 180-second subprocess limit while resource files were still arriving. The wrapper now allows 600 seconds and saves partial output on timeout; cached compilation succeeded. This is not evidence of a manuscript error, and the first-download cost should not be mistaken for steady-state compile time.

## Final delivery gates still required

The actual manuscript and Word export must each be rebuilt from the final source, have exactly six pages including references, within the conference's 4-6-page limit, preserve the existing author list, contain matching claims/results and all references, and pass complete page-by-page visual inspection. The reviewer-compliance PDF is a separate required artifact. PDF eXpress validation with conference ID 69954X is an external certification step that a local build, embedded-font check or Word export cannot claim to have completed.
