"""Prepare and smoke-test local manuscript tools without changing the manuscript.

Uses an official Tectonic release and the separately fetched CTAN IEEEtran class.
The Word test uses an isolated invisible Microsoft Word COM instance, not LibreOffice.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
WORK = TOOLS / "manuscript_smoke"
TECTONIC = TOOLS / "tectonic" / "tectonic.exe"
TECTONIC_URL = "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip"
TECTONIC_SHA256 = "f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f"
PANDOC = TOOLS / "pandoc" / "pandoc.exe"
PANDOC_URL = "https://github.com/jgm/pandoc/releases/download/3.11/pandoc-3.11-windows-x86_64.zip"
PANDOC_SHA256 = "2ab72baf2399450e148ddf7a2a8689806c42e1bba71862b57e220fd9b8456d3d"
CTAN_ZIP = ROOT / "docs/revision/sources/ieee_ctan_package.zip"
MAX_DOWNLOAD = 300 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe() -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": {"os_name": os.name, "windows_version": list(sys.getwindowsversion())},
        "python": sys.executable,
        "commands": {x: shutil.which(x) for x in ["tectonic", "pdflatex", "xelatex", "latexmk", "pandoc"]},
        "python_packages": {x: bool(importlib.util.find_spec(x)) for x in ["docx", "fitz", "win32com", "lxml"]},
        "winword": str(Path(r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE")),
        "winword_exists": Path(r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE").is_file(),
        "free_bytes": shutil.disk_usage(ROOT).free,
        "tectonic_prepared": TECTONIC.is_file(),
    }


def download_tectonic() -> dict:
    import requests
    dest = TECTONIC.parent
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / "tectonic-0.17.0-windows-msvc.zip"
    if not archive.exists() or digest(archive) != TECTONIC_SHA256:
        total = 0
        with requests.get(TECTONIC_URL, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            with archive.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD:
                        raise RuntimeError("Download exceeded 300 MiB limit")
                    stream.write(chunk)
    actual = digest(archive)
    if actual != TECTONIC_SHA256:
        raise RuntimeError(f"Tectonic release digest mismatch: {actual}")
    with zipfile.ZipFile(archive) as bundle:
        entries = [x for x in bundle.namelist() if Path(x).name.lower() == "tectonic.exe"]
        if len(entries) != 1:
            raise RuntimeError(f"Expected one executable, found {entries}")
        TECTONIC.write_bytes(bundle.read(entries[0]))
    result = {"url": TECTONIC_URL, "archive_sha256": actual, "archive_bytes": archive.stat().st_size,
              "executable_sha256": digest(TECTONIC), "executable": str(TECTONIC)}
    (dest / "release_provenance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def tectonic_environment() -> dict:
    env = os.environ.copy()
    env["TECTONIC_CACHE_DIR"] = str(TOOLS / "tectonic_cache")
    return env


def download_pandoc() -> dict:
    import requests
    PANDOC.parent.mkdir(parents=True, exist_ok=True)
    archive = PANDOC.parent / "pandoc-3.11-windows-x86_64.zip"
    if not archive.is_file() or digest(archive) != PANDOC_SHA256:
        total = 0
        with requests.get(PANDOC_URL, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            with archive.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    total += len(chunk)
                    if total > 100 * 1024 * 1024:
                        raise RuntimeError("Pandoc download exceeded 100 MiB limit")
                    stream.write(chunk)
    if digest(archive) != PANDOC_SHA256:
        raise RuntimeError("Pandoc release digest mismatch")
    with zipfile.ZipFile(archive) as bundle:
        entries = [x for x in bundle.namelist() if Path(x).name.lower() == "pandoc.exe"]
        if len(entries) != 1:
            raise RuntimeError(f"Expected one Pandoc executable, found {entries}")
        PANDOC.write_bytes(bundle.read(entries[0]))
    result = {"url": PANDOC_URL, "archive_sha256": digest(archive), "archive_bytes": archive.stat().st_size,
              "executable_sha256": digest(PANDOC), "executable": str(PANDOC)}
    (PANDOC.parent / "release_provenance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def compile_tex(tex: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    command = [str(TECTONIC), "-X", "compile", "--keep-logs", "--keep-intermediates", "--outdir", str(outdir), str(tex)]
    log = outdir / "tectonic_command.log"
    try:
        run = subprocess.run(command, cwd=tex.parent, env=tectonic_environment(), text=True,
                             encoding="utf-8", errors="replace", capture_output=True, timeout=600)
    except subprocess.TimeoutExpired as error:
        partial = (error.stdout or b"") + (error.stderr or b"")
        log.write_text(partial.decode("utf-8", errors="replace") if isinstance(partial, bytes) else partial,
                       encoding="utf-8")
        raise RuntimeError(f"Tectonic exceeded 600 seconds; partial output saved to {log}") from error
    log.write_text(run.stdout + "\n" + run.stderr, encoding="utf-8")
    result = {"command": command, "exit_code": run.returncode, "log": str(log),
              "pdf": str(outdir / (tex.stem + ".pdf"))}
    if run.returncode != 0:
        raise RuntimeError(json.dumps(result) + "\n" + run.stdout[-3000:] + run.stderr[-3000:])
    return result


def render_word(docx_path: Path, pdf_path: Path) -> dict:
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    app = None
    doc = None
    try:
        app = win32com.client.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        app.AutomationSecurity = 3  # Disable document macros in this isolated instance.
        version = str(app.Version)
        doc = app.Documents.Open(str(docx_path.resolve()), ConfirmConversions=False,
                                 ReadOnly=True, AddToRecentFiles=False, Visible=False)
        doc.Repaginate()
        pages = int(doc.ComputeStatistics(2))
        doc.ExportAsFixedFormat(str(pdf_path.resolve()), 17, OpenAfterExport=False,
                                OptimizeFor=0, Range=0, Item=0, IncludeDocProps=False,
                                KeepIRM=False, CreateBookmarks=0, DocStructureTags=True,
                                BitmapMissingFonts=False, UseISO19005_1=False)
        return {"word_version": version, "pages_reported_by_word": pages, "pdf": str(pdf_path),
                "pdf_exists": pdf_path.is_file(), "pdf_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0}
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        if app is not None:
            app.Quit(SaveChanges=0)
        pythoncom.CoUninitialize()


def inspect_pdf(pdf: Path, stem: str) -> dict:
    import fitz
    doc = fitz.open(pdf)
    pages = []
    for i, page in enumerate(doc):
        png = WORK / f"{stem}_page_{i+1:02}.png"
        page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(png)
        pages.append({"page": i + 1, "width_pt": page.rect.width, "height_pt": page.rect.height,
                      "chars": len(page.get_text()), "image": str(png),
                      "fonts": [list(x) for x in page.get_fonts()]})
    return {"path": str(pdf), "sha256": digest(pdf), "pages": pages}


def make_smoke_files() -> dict:
    from docx import Document
    from docx.enum.section import WD_SECTION_START
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    WORK.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(CTAN_ZIP) as archive:
        (WORK / "IEEEtran.cls").write_bytes(archive.read("IEEEtran/IEEEtran.cls"))
        (WORK / "bare_conf_reference.tex").write_bytes(archive.read("IEEEtran/bare_conf.tex"))
    tex = r"""\RequirePackage[T1]{fontenc}
\documentclass[conference,a4paper]{IEEEtran}
\usepackage{amsmath,amssymb,graphicx,booktabs,cite}
\usepackage[hidelinks]{hyperref}
\begin{document}
\typeout{SMOKE DIMENSIONS: paperwidth=\the\paperwidth;paperheight=\the\paperheight;textwidth=\the\textwidth;textheight=\the\textheight;columnsep=\the\columnsep;oddsidemargin=\the\oddsidemargin;topmargin=\the\topmargin;headheight=\the\headheight;headsep=\the\headsep}
\title{Manuscript Toolchain Verification}
\author{\IEEEauthorblockN{Isolated Test Document}\IEEEauthorblockA{Not a research manuscript}}
\maketitle
\begin{abstract}This isolated document verifies two-column rendering, mathematical glyphs and an embedded table. It contains no research findings.\end{abstract}
\begin{IEEEkeywords}Document preparation, verification\end{IEEEkeywords}
\section{Rendering Check}
An editable manuscript needs consistent text and equations. The capability variable is $\Delta e$, and the illustrative expression is
\begin{equation} e_i(t)=e_0+\Delta e.\end{equation}
\begin{table}[h]\centering\caption{Isolated check}\begin{tabular}{lr}\toprule Item&Value\\\midrule Columns&2\\Fonts&Embedded\\\bottomrule\end{tabular}\end{table}
\section{Interpretation}
Passing this check establishes only that the local renderer can produce a PDF from a small IEEE-style source. Final page count, content agreement and visual quality must still be checked on the finished manuscript.
\end{document}
"""
    tex_path = WORK / "ieee_smoke.tex"
    tex_path.write_text(tex, encoding="utf-8")
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(210 / 25.4)
    section.page_height = Inches(297 / 25.4)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(0.625)
    section.right_margin = Inches(0.625)
    for style_name in ["Normal", "Title", "Heading 1", "Caption"]:
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_after = Pt(0)
        font_element = style.element.get_or_add_rPr().find(qn("w:rFonts"))
        if font_element is not None:
            for key in list(font_element.attrib):
                if "theme" in key.lower():
                    del font_element.attrib[key]
            for key in ["ascii", "hAnsi", "cs", "eastAsia"]:
                font_element.set(qn("w:" + key), "Times New Roman")
    for element in list(doc.styles.element.iter(qn("w:pBdr"))):
        element.getparent().remove(element)
    doc.styles["Normal"].font.size = Pt(10)
    doc.styles["Normal"].paragraph_format.first_line_indent = Inches(0.14)
    doc.styles["Normal"].paragraph_format.line_spacing = 1
    doc.styles["Title"].font.size = Pt(24)
    doc.styles["Title"].paragraph_format.first_line_indent = Inches(0)
    doc.styles["Heading 1"].font.size = Pt(10)
    doc.styles["Heading 1"].font.small_caps = True
    doc.styles["Heading 1"].font.bold = False
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(10)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(4)
    doc.styles["Caption"].font.size = Pt(8)
    p = doc.add_paragraph("Manuscript Toolchain Verification", style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("Isolated Test Document\nNot a research manuscript")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Inches(0)
    cols_section = doc.add_section(WD_SECTION_START.CONTINUOUS)
    cols = cols_section._sectPr.find(qn("w:cols"))
    cols.set(qn("w:num"), "2")
    cols.set(qn("w:space"), "360")
    p = doc.add_paragraph("Abstract - This isolated document verifies two-column rendering, editable mathematical glyphs and an embedded table. It contains no research findings.")
    p.runs[0].font.size = Pt(9)
    p.runs[0].bold = True
    p = doc.add_paragraph("I. Rendering Check", style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("An editable manuscript needs consistent text and equations. The capability variable is shown below using native Word equation markup.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    math = OxmlElement("m:oMath")
    run = OxmlElement("m:r")
    text = OxmlElement("m:t")
    text.text = "eᵢ(t) = e₀ + Δe"
    run.append(text)
    math.append(run)
    p._p.append(math)
    p = doc.add_paragraph("TABLE I\nISOLATED CHECK", style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2)
    table.columns[1].width = Inches(1.5)
    for cell, value in zip(table.rows[0].cells, ["Item", "Value"]):
        cell.text = value
    for a, b in [("Columns", "2"), ("Equation", "Editable")]:
        cells = table.add_row().cells
        cells[0].text, cells[1].text = a, b
    for row in table.rows:
        for column_index, cell in enumerate(row.cells):
            cell.width = Inches([2, 1.5][column_index])
            for para in cell.paragraphs:
                para.paragraph_format.first_line_indent = Inches(0)
                for run in para.runs:
                    run.font.size = Pt(8)
    p = doc.add_paragraph("II. Interpretation", style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Passing this check establishes only that the local renderer can produce a PDF from an editable Word source. Final page count, content agreement and visual quality must still be checked on the finished manuscript.")
    doc.core_properties.title = "Manuscript Toolchain Verification"
    doc.core_properties.author = ""
    docx_path = WORK / "ieee_style_smoke.docx"
    doc.save(docx_path)
    return {"tex": tex_path, "docx": docx_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--download-pandoc", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--render-word", type=Path)
    parser.add_argument("--pdf-out", type=Path)
    args = parser.parse_args()
    TOOLS.mkdir(exist_ok=True)
    report = probe()
    if args.download:
        report["download"] = download_tectonic()
    if args.download_pandoc:
        report["pandoc_download"] = download_pandoc()
    if args.render_word:
        if not args.pdf_out:
            raise SystemExit("--pdf-out is required with --render-word")
        args.pdf_out.parent.mkdir(parents=True, exist_ok=True)
        report["word_export"] = render_word(args.render_word, args.pdf_out)
    if args.smoke:
        files = make_smoke_files()
        print("Compiling isolated IEEEtran smoke document", flush=True)
        report["latex"] = compile_tex(files["tex"], WORK / "latex_output")
        report["latex_pdf"] = inspect_pdf(WORK / "latex_output/ieee_smoke.pdf", "latex")
        print("Rendering isolated editable Word smoke document", flush=True)
        report["word"] = render_word(files["docx"], WORK / "ieee_style_smoke.pdf")
        report["word_pdf"] = inspect_pdf(WORK / "ieee_style_smoke.pdf", "word")
    (TOOLS / "manuscript_tool_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
