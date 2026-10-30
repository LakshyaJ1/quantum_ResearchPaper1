# WiCOMM-2026 camera-ready, paper 167

Microsoft CMT asks for three files. Which file in this folder goes where:

| CMT upload | File | Status |
|---|---|---|
| 1. Reviewer compliance file (normal PDF) | `Reviewer_Compliance.pdf` | Ready |
| 2. Word file, or zip of LaTeX and supplementary files | `Paper167_LaTeX_Source.zip` (recommended) or `Paper167_Manuscript.docx` | Ready |
| 3. PDF eXpress file of the final manuscript | produced by IEEE PDF eXpress from `Paper167_LaTeX.pdf` | To do |

`Paper167_LaTeX.pdf` is the final manuscript: six A4 pages typeset from `paper.tex` with IEEEtran, all fonts embedded, no Type 3 fonts, not encrypted. `Paper167_LaTeX_Source.zip` holds `paper.tex`, its three generated tables and three figures, and compiles on its own to the same six pages. `Paper167_Manuscript.docx` (and its Word export, `Paper167_Manuscript.pdf`) carries the same text on the IEEE A4 Word template; upload it only if a Word file is preferred.

PDF eXpress (item 3):

1. Go to https://ieee-pdf-express.org, create an account with conference ID 69954X, and log in.
2. Choose "Create New Title", enter the paper title, and upload `Paper167_LaTeX.pdf` for checking.
3. PDF eXpress emails the result. If it passes, the approved PDF is the file for CMT item 3. If it fails, send the error report and the fix is usually a quick rebuild; uploading the zip for conversion is the fallback.

`SHA256SUMS.txt` and `DELIVERY_MANIFEST.json` record each file's hash, page count and font embedding. `tools/package_submission.py` rebuilds this folder; `MANUSCRIPT_BUILD.md` gives the full rebuild steps.
