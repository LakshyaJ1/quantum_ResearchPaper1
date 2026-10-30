from pathlib import Path
from collections import Counter
from zipfile import ZipFile
import hashlib
import json
import re
import subprocess
import unicodedata
from lxml import etree
from docx import Document
import fitz

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
DOCX = ROOT / "submission/Paper167_Manuscript.docx"
PDF = ROOT / "submission/Paper167_Manuscript.pdf"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def document_xml(path):
    with ZipFile(path) as package:
        return etree.fromstring(package.read("word/document.xml"))


def math_hashes(path):
    return Counter(hashlib.sha256(etree.tostring(node, method="c14n", exclusive=True)).hexdigest()
                   for node in document_xml(path).findall(".//m:oMath", NS))


def pieces(node):
    if isinstance(node, dict):
        kind = node.get("t")
        if kind in ("Math", "Image"):
            return []
        if kind == "Str":
            return [node["c"]]
        if kind == "Code":
            return [node["c"][1]]
        if kind:
            return pieces(node.get("c", []))
        return sum((pieces(value) for value in node.values()), [])
    if isinstance(node, list):
        return sum((pieces(item) for item in node), [])
    return []


def stringify(node):
    if isinstance(node, list):
        return "".join(map(stringify, node))
    if isinstance(node, dict):
        kind, content = node.get("t"), node.get("c", [])
        if kind == "Str":
            return content
        if kind in ("Space", "SoftBreak"):
            return " "
        if kind == "LineBreak":
            return "\n"
        return stringify(content)
    return ""


def tokens(text):
    text = unicodedata.normalize("NFKC", text).replace("’", "'").replace("–", "-").replace("—", "-")
    return Counter(re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?", text.lower()))


manifest = json.loads((STAGE / "conversion_manifest.json").read_text(encoding="utf-8"))
for fmt, filename in (("json", "source_ast.json"), ("docx", "pandoc_raw.docx")):
    subprocess.run([str(ROOT / "tools/pandoc/pandoc.exe"), manifest["staged"], "-f", "latex",
                    "-t", fmt, "-o", str(STAGE / filename)], check=True)
ast = json.loads((STAGE / "source_ast.json").read_text(encoding="utf-8"))
expected = re.sub(r"WORD-EQUATION-NUMBER:\d+", "", " ".join(pieces(ast)))
actual = " ".join(document_xml(DOCX).xpath("//w:t/text()", namespaces=NS))
missing = tokens(expected) - tokens(actual)
extra = tokens(actual) - tokens(expected)
expected_author = stringify(ast["meta"]["author"])
actual_author = "\n".join(p.text for p in Document(DOCX).paragraphs if p.style.name == "Author")
raw_math, final_math = math_hashes(STAGE / "pandoc_raw.docx"), math_hashes(DOCX)
pdf = fitz.open(PDF)
font_refs = {font[0]: font[3] for page in pdf for font in page.get_fonts()}
fonts = [{"name": name, "embedded_bytes": len(pdf.extract_font(ref)[3])} for ref, name in font_refs.items()]
with ZipFile(DOCX) as package:
    media = {name: hashlib.sha256(package.read(name)).hexdigest()
             for name in package.namelist() if name.startswith("word/media/")}

report = {
    "source": {"path": manifest["source"], "sha256": manifest["source_sha256"],
               "unchanged": sha(manifest["source"]) == manifest["source_sha256"]},
    "aux": {"path": manifest["aux"], "sha256": manifest["aux_sha256"],
            "unchanged": sha(manifest["aux"]) == manifest["aux_sha256"]},
    "inputs": [{**record, "unchanged": sha(record["path"]) == record["sha256"]} for record in manifest["inputs"]],
    "docx": {"path": str(DOCX), "sha256": sha(DOCX), "bytes": DOCX.stat().st_size},
    "pdf": {"path": str(PDF), "sha256": sha(PDF), "bytes": PDF.stat().st_size, "pages": len(pdf),
            "a4_all_pages": all(abs(p.rect.width - 595.276) < .1 and abs(p.rect.height - 841.89) < .1 for p in pdf),
            "page_details": [{"page": i + 1, "width_pt": p.rect.width, "height_pt": p.rect.height,
                              "text_chars": len(p.get_text()), "images": len(p.get_images())} for i, p in enumerate(pdf)]},
    "author_block_matches_source": " ".join(expected_author.split()) == " ".join(actual_author.split()),
    "author_block": actual_author,
    "prose_and_numeric_token_parity": {"expected_tokens": sum(tokens(expected).values()), "missing": dict(missing),
                                      "added_numbering_and_labels": dict(extra)},
    "native_math": {"count": sum(final_math.values()), "identical_to_pandoc_math": raw_math == final_math},
    "numbered_equations": manifest["equations"], "citation_map": manifest["citations"], "label_map": manifest["labels"],
    "figures": [{"source": image["source"], "source_sha256": image["source_sha256"],
                 "raster_sha256": sha(image["raster"]), "embedded_identically": sha(image["raster"]) in media.values()}
                for image in manifest["images"]],
    "font_embedding": {"all_embedded": all(font["embedded_bytes"] for font in fonts), "fonts": fonts},
    "structure": manifest["word_structure"],
    "unresolved_markers": re.findall(r"WORD-(?:WIDE|EQUATION)[A-Z:-]*|\[\[[^]]+\]\]|\\Main[A-Za-z]+|\?\?", actual),
    "visual_review": "Independent visual review pending for this exact output hash.",
    "pdf_express_certified": False,
}
(STAGE / "final_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(STAGE / "extracted_final_pdf.txt").write_text("\n\n".join(f"PAGE {i+1}\n" + p.get_text(sort=True)
                                                          for i, p in enumerate(pdf)), encoding="utf-8")
assert not missing and raw_math == final_math
assert report["author_block_matches_source"] and report["font_embedding"]["all_embedded"]
assert report["source"]["unchanged"] and report["aux"]["unchanged"] and all(x["unchanged"] for x in report["inputs"])
assert report["pdf"]["a4_all_pages"] and 4 <= report["pdf"]["pages"] <= 6
assert all(image["embedded_identically"] for image in report["figures"]) and not report["unresolved_markers"]
print(json.dumps({"pages": len(pdf), "source_sha256": report["source"]["sha256"],
                  "docx_sha256": sha(DOCX), "pdf_sha256": sha(PDF),
                  "expected_nonmath_tokens": report["prose_and_numeric_token_parity"]["expected_tokens"],
                  "missing_tokens": dict(missing), "native_math": report["native_math"],
                  "fonts_embedded": True, "authors_match": True}, indent=2))
