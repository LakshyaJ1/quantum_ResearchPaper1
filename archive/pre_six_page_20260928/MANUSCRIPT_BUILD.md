# Building the revised manuscript

The primary source is `paper.tex`. `paper_revised.tex` is an identical convenience copy; `paper_extended.tex` includes the primary source. `abstract_new.tex` contains the expanded revised abstract. Numerical macros and the class table live under `results/revision/manuscript/`; the three manuscript figures are under `figures/revision/`.

Compile `paper.tex` with a TeX distribution that supplies IEEEtran 1.8b and the standard amsmath, amssymb, booktabs, graphicx, cite, url and hyperref packages. Tectonic 0.17.0 was used for the delivered five-page A4 PDF. Keep `\RequirePackage[T1]{fontenc}` before `\documentclass` as supplied. With an installed Tectonic executable, run `tectonic -X compile --keep-logs --keep-intermediates paper.tex`. With a conventional TeX installation, run `pdflatex paper.tex` twice. The latter command is a conventional alternative, not the renderer used for the delivered PDF.

The source ZIP preserves the relative directories needed by the manuscript and includes SHA-256 hashes for every member. Standard TeX packages and executable tools are dependencies, not bundled third-party source. An online editor can use `paper.tex` as its main document after importing the ZIP.

The full workspace documents the tested Windows Word conversion in `docs/revision/build_environment.md`. It uses Pandoc 3.11 and a hidden Microsoft Word 16 export. The delivered Word manuscript contains native editable equations and tables. The PDF exported from that Word file, `submission/Paper167_Manuscript.pdf`, is the authoritative local submission manuscript. `submission/Paper167_LaTeX.pdf` is the corresponding LaTeX rendering; its pagination differs slightly, so reviewer response page references use the Word export.

Local rendering and font checks do not confer IEEE PDF eXpress certification. The author must process the final manuscript through PDF eXpress with conference ID 69954X, then use the certified output for the conference upload. Changing the manuscript or author block after certification requires a fresh export and certification.
