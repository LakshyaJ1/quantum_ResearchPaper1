"""Camera-ready Word build: paper.tex -> IEEE A4 Word template .docx -> Word-exported PDF.

Pipeline (re-runnable, idempotent):
  1. tectonic compiles paper.tex into build/camera_ready/latex/ (AUX = numbering authority);
  2. the LaTeX source is parsed into blocks; prose/tables/captions are converted directly,
     math goes through pandoc only to obtain native OMML;
  3. the DOCX is written on tools/ieee_template/conference-template-a4.docx, using its styles,
     numbering and page setup (placeholder content removed);
  4. a hidden Word COM instance exports the PDF; a small fitting loop adjusts only layout
     parameters (float gaps/anchors, caption and equation spacing) until the Word PDF has the
     target page count (default: the LaTeX page count);
  5. build/camera_ready/word/word_report.json records page counts, fonts, text parity and
     object counts; every Word PDF page is rendered to build/camera_ready/word/pages/.

Usage:  python tools/build_word_cr.py [--target-pages N] [--no-fit] [--skip-latex]
The source files are never modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import dataclasses
from dataclasses import dataclass, field, replace
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import zipfile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
TECTONIC = ROOT / "tools/tectonic/tectonic.exe"
PANDOC = ROOT / "tools/pandoc/pandoc.exe"
TEMPLATE = ROOT / "tools/ieee_template/conference-template-a4.docx"
BUILD = ROOT / "build/camera_ready"
LATEX_DIR = BUILD / "latex"
WORD_DIR = BUILD / "word"
WORK = WORD_DIR / "_work"
PAGES = WORD_DIR / "pages"
STEM = "Paper167_Manuscript"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSMAP = {"w": W_NS, "m": M_NS, "r": R_NS}

# Template page geometry (twips), read from the template's body section.
PAGE_W = 11906
BODY_MARGIN_LR = 907
COL_SPACE = 360
TEXT_W = PAGE_W - 2 * BODY_MARGIN_LR          # 10092
COL_W = (TEXT_W - COL_SPACE) // 2             # 4866
TWIP_PER_IN = 1440
EMU_PER_TWIP = 635

SIZE_HALFPT = {"tiny": 10, "scriptsize": 14, "footnotesize": 16, "small": 18, "normalsize": 20,
               "large": 24, "Large": 28}
REFMARKS = {"1": "\u2217", "2": "\u2020", "3": "\u2021", "4": "\u00a7", "5": "\u00b6", "6": "\u2016"}


def w(tag):
    return "{%s}%s" % (W_NS, tag)


def m(tag):
    return "{%s}%s" % (M_NS, tag)


def E(tag, attrs=None, *children):
    """Build a w:/m: element; attrs keys are local names in the same namespace."""
    ns = M_NS if tag.startswith("m:") else W_NS
    el = etree.Element("{%s}%s" % (ns, tag.split(":", 1)[1]), nsmap=NSMAP)
    for k, v in (attrs or {}).items():
        if ":" in k:
            p, local = k.split(":", 1)
            el.set("{%s}%s" % (NSMAP[p], local), str(v))
        else:
            el.set("{%s}%s" % (ns, k), str(v))
    for c in children:
        if c is not None:
            el.append(c)
    return el


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------------------------
# 1. LaTeX compilation and AUX
# ----------------------------------------------------------------------------------------------

PLACEHOLDER_DIR = LATEX_DIR / "placeholders"


def make_placeholders(tex: Path) -> list[str]:
    """Preview aid only: create labelled stand-ins for figures that do not exist yet."""
    import fitz
    text = strip_comments(tex.read_text(encoding="utf-8"))
    gp = re.search(r"\\graphicspath\s*\{((?:\{[^}]*\})+)\}", text)
    dirs = [ROOT] + [ROOT / d for d in re.findall(r"\{([^{}]+)\}", gp.group(1))] if gp else [ROOT]
    made = []
    if PLACEHOLDER_DIR.exists():
        shutil.rmtree(PLACEHOLDER_DIR)
    for name in re.findall(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", text):
        stem = Path(name).stem
        if any((d / (stem + ext)).is_file() for d in dirs for ext in (".pdf", ".png")):
            continue
        PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)
        w_pt, h_pt = 3.45 * 72, 1.62 * 72
        doc = fitz.open()
        page = doc.new_page(width=w_pt, height=h_pt)
        page.draw_rect(page.rect + (2, 2, -2, -2), color=(0.5, 0.5, 0.5), width=0.8, dashes="[3] 0")
        fontfile = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "times.ttf"
        page.insert_textbox(page.rect + (10, h_pt / 2 - 12, -10, 0), "PLACEHOLDER: %s (figure not generated yet)" % stem,
                            fontsize=8, align=1, fontname="phtimes", fontfile=str(fontfile))
        doc.save(PLACEHOLDER_DIR / (stem + ".pdf"))
        page.get_pixmap(dpi=300, alpha=False).save(PLACEHOLDER_DIR / (stem + ".png"))
        doc.close()
        made.append(stem)
    return made


def compile_latex(tex: Path, extra_search: Path | None = None) -> Path:
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TECTONIC_CACHE_DIR=str(ROOT / "tools/tectonic_cache"))
    cmd = [str(TECTONIC), "-X", "compile", "--keep-logs", "--keep-intermediates",
           "--outdir", str(LATEX_DIR)]
    if extra_search is not None:
        cmd += ["-Z", "search-path=%s" % extra_search]
    cmd.append(str(tex.relative_to(ROOT)))
    run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=900)
    (LATEX_DIR / "tectonic_command.log").write_text(" ".join(cmd) + "\n\n" + run.stdout + run.stderr,
                                                    encoding="utf-8")
    if run.returncode:
        raise RuntimeError("tectonic failed:\n" + run.stderr[-3000:])
    log = (LATEX_DIR / (tex.stem + ".log")).read_text(encoding="utf-8", errors="replace")
    bad = re.findall(r"LaTeX Warning: (?:Reference|Citation) [^\n]* undefined", log)
    if bad:
        raise RuntimeError("Undefined references/citations in LaTeX build: " + "; ".join(bad[:10]))
    return LATEX_DIR / (tex.stem + ".pdf")


def balanced(text: str, start: int) -> tuple[str, int]:
    """Return content of the {...} group starting at text[start] and the index after it."""
    if text[start] != "{":
        raise ValueError("Expected '{' at %d: %r" % (start, text[start:start + 40]))
    depth, i = 1, start + 1
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError("Unbalanced braces near: %r" % text[start:start + 80])


def bracket_opt(text: str, i: int) -> tuple[str | None, int]:
    j = i
    while j < len(text) and text[j] in " \t\n":
        j += 1
    if j < len(text) and text[j] == "[":
        depth, k = 0, j
        while k < len(text):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
            elif text[k] == "]" and depth == 0:
                return text[j + 1:k], k + 1
            k += 1
        raise ValueError("Unclosed [ near %r" % text[j:j + 40])
    return None, i


def read_aux(aux: Path) -> dict:
    text = aux.read_text(encoding="utf-8", errors="strict")
    labels, pages = {}, {}
    for mm in re.finditer(r"\\newlabel\{([^}]+)\}\s*\{", text):
        outer, _ = balanced(text, mm.end() - 1)
        value, rest = balanced(outer, 0)
        page = re.match(r"\s*\{([^}]*)\}", outer[rest:])
        value = re.sub(r"\\mbox\s*\{([^}]*)\}", r"\1", value).strip()
        labels[mm.group(1)] = value
        pages[mm.group(1)] = page.group(1) if page else None
    cites = dict(re.findall(r"\\bibcite\{([^}]+)\}\{([^}]*)\}", text))
    toc = []
    for mm in re.finditer(r"\\contentsline \{(section|subsection|subsubsection)\}\{(.*?)\}\{(\d+)\}\{", text):
        num = re.search(r"\\numberline \{(?:\\mbox \{)?([^{}]*)\}?\}", mm.group(2))
        toc.append({"level": mm.group(1), "number": num.group(1).strip() if num else None,
                    "page": int(mm.group(3))})
    floats = []
    for mm in re.finditer(r"\\contentsline \{(table|figure)\}\{\\numberline \{([^}]*)\}.*?\}\{(\d+)\}\{(?:table|figure)\.", text):
        floats.append({"kind": mm.group(1), "number": mm.group(2), "page": int(mm.group(3))})
    last = re.search(r"\\gdef \\@abspage@last\{(\d+)\}", text)
    return {"labels": labels, "label_pages": pages, "cites": cites, "toc": toc, "floats": floats,
            "pages": int(last.group(1)) if last else None}


# ----------------------------------------------------------------------------------------------
# 2. LaTeX source reading
# ----------------------------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    # TeX semantics: '%' removes the rest of the line, the newline and the next line's indentation.
    return re.sub(r"(?<!\\)%[^\n]*(?:\n[ \t]*)?", "", text)


def expand_inputs(path: Path, records: list, depth=0) -> str:
    if depth > 10:
        raise ValueError("\\input nesting too deep")
    records.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    text = strip_comments(path.read_text(encoding="utf-8"))

    def include(mm):
        name = mm.group(1).strip()
        cands = [ROOT / name, path.parent / name]
        cands += [c.with_name(c.name + ".tex") for c in cands if c.suffix != ".tex"]
        target = next((c for c in cands if c.is_file()), None)
        if target is None:
            raise FileNotFoundError("Cannot resolve \\input{%s}" % name)
        return expand_inputs(target, records, depth + 1)

    return re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", include, text)


def parse_macros(preamble: str) -> dict:
    macros = {}
    for mm in re.finditer(r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\s*(?:\[(\d)\])?\s*(?=\{)", preamble):
        body, _ = balanced(preamble, mm.end())
        macros[mm.group(1)] = (int(mm.group(2) or 0), body)
    return macros


def expand_macros(text: str, macros: dict) -> str:
    if not macros:
        return text
    names = sorted(macros, key=len, reverse=True)
    pat = re.compile(r"\\(" + "|".join(map(re.escape, names)) + r")(?![A-Za-z])")
    for _ in range(20):
        out, pos, changed = [], 0, False
        for mm in pat.finditer(text):
            if mm.start() < pos:
                continue
            nargs, body = macros[mm.group(1)]
            j = mm.end()
            if nargs == 0:
                while j < len(text) and text[j] in " \t\n":   # a control word swallows spaces
                    j += 1
                rep = body
            else:
                args = []
                for _k in range(nargs):
                    while text[j] in " \t\n":
                        j += 1
                    if text[j] == "{":
                        a, j = balanced(text, j)
                    else:
                        a, j = text[j], j + 1
                    args.append(a)
                rep = body
                for k, a in enumerate(args, 1):
                    rep = rep.replace("#%d" % k, a)
            out.append(text[pos:mm.start()])
            out.append(rep)
            pos = j
            changed = True
        out.append(text[pos:])
        text = "".join(out)
        if not changed:
            return text
    raise ValueError("Macro expansion did not terminate")


def env_body(text: str, name: str) -> tuple[str | None, int, int]:
    b = re.search(r"\\begin\{" + re.escape(name) + r"\}", text)
    if not b:
        return None, -1, -1
    e = text.find("\\end{" + name + "}", b.end())
    if e < 0:
        raise ValueError("Unclosed environment " + name)
    return text[b.end():e], b.start(), e + len("\\end{" + name + "}")


# ----------------------------------------------------------------------------------------------
# 3. Inline LaTeX -> run items
# ----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Fmt:
    i: bool = False
    b: bool = False
    sc: bool = False
    tt: bool = False
    vert: str | None = None
    size: int | None = None
    font: str | None = None


ACCENTS = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303", "=": "\u0304",
           ".": "\u0307", "u": "\u0306", "v": "\u030c", "H": "\u030b", "c": "\u0327", "k": "\u0328",
           "r": "\u030a"}
SYMBOLS = {"S": "\u00a7", "P": "\u00b6", "dagger": "\u2020", "ddagger": "\u2021", "ldots": "\u2026",
           "dots": "\u2026", "textendash": "\u2013", "textemdash": "\u2014", "copyright": "\u00a9",
           "textregistered": "\u00ae", "texttrademark": "\u2122", "textdegree": "\u00b0",
           "textpm": "\u00b1", "texttimes": "\u00d7", "textbackslash": "\\", "textbar": "|",
           "textless": "<", "textgreater": ">", "textasciitilde": "~", "textunderscore": "_",
           "textquoteright": "\u2019", "textquoteleft": "\u2018", "textquotedblleft": "\u201c",
           "textquotedblright": "\u201d", "i": "\u0131", "ss": "\u00df", "o": "\u00f8", "O": "\u00d8",
           "ae": "\u00e6", "AE": "\u00c6", "aa": "\u00e5", "AA": "\u00c5", "l": "\u0142", "L": "\u0141",
           "oe": "\u0153", "OE": "\u0152", "LaTeX": "LaTeX", "TeX": "TeX", "textbullet": "\u2022",
           "nobreakspace": "\u00a0", "quad": "\u2003", "qquad": "\u2003\u2003", "enspace": "\u2002",
           "thinspace": "\u202f", "textsection": "\u00a7"}
IGNORED = {"protect", "relax", "ignorespaces", "nobreak", "allowbreak", "xspace", "centering",
           "raggedright", "raggedleft", "leavevmode", "label", "normalfont", "sloppy", "strut",
           "unskip", "hfil", "null", "noindent", "vfill", "bigskip", "medskip", "smallskip"}
DECL = {"bfseries": ("b", True), "bf": ("b", True), "mdseries": ("b", False), "itshape": ("i", True),
        "it": ("i", True), "upshape": ("i", False), "slshape": ("i", True), "scshape": ("sc", True),
        "sc": ("sc", True), "ttfamily": ("tt", True), "tt": ("tt", True), "rmfamily": ("tt", False),
        "sffamily": ("tt", False)}


class Inline:
    """Strict converter for the inline LaTeX subset used by the manuscript."""

    def __init__(self, labels: dict, cites: dict, allow_breaks=False):
        self.labels, self.cites = labels, cites
        self.allow_breaks = allow_breaks
        self.maths: list[str] = []

    # -- helpers --
    @staticmethod
    def _skip_ws(s, i):
        while i < len(s) and s[i] in " \t\n":
            i += 1
        return i

    def _arg(self, s, i):
        i = self._skip_ws(s, i)
        if i >= len(s):
            raise ValueError("Missing argument at end of %r" % s[-60:])
        if s[i] == "{":
            return balanced(s, i)
        if s[i] == "\\":
            mm = re.match(r"\\([A-Za-z]+|.)", s[i:])
            return mm.group(0), i + len(mm.group(0))
        return s[i], i + 1

    def cite_text(self, keys: str, note: str | None) -> str:
        key_list = [k.strip() for k in keys.split(",") if k.strip()]
        missing = [k for k in key_list if k not in self.cites]
        if missing:
            raise ValueError("Unresolved citation keys: %s" % missing)
        nums = sorted({int(self.cites[k]) for k in key_list})
        groups, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            if j - i >= 2:
                groups.append("[%d]\u2013[%d]" % (nums[i], nums[j]))
            else:
                groups.extend("[%d]" % n for n in nums[i:j + 1])
            i = j + 1
        text = ", ".join(groups)
        if note:
            text = text[:-1] + ", " + note + "]"
        return text

    def ref_items(self, key, fmt, paren=False):
        if key not in self.labels:
            raise ValueError("Unresolved \\ref{%s}" % key)
        val = self.labels[key]
        if re.search(r"[\\{}]", val):
            raise ValueError("Unexpected markup in label %s: %r" % (key, val))
        items = []
        if paren:
            items.append(("t", "(", fmt))
        for k, part in enumerate(val.split("-")):
            if k:
                items.append(("nbh", fmt))
            if part:
                items.append(("t", part, fmt))
        if paren:
            items.append(("t", ")", fmt))
        return items

    # -- main --
    def parse(self, s: str, fmt: Fmt = Fmt()) -> list:
        out = []
        i, n = 0, len(s)

        def text(t, f=None):
            out.append(("t", t, f or fmt))

        while i < n:
            c = s[i]
            if c == "\\":
                mm = re.match(r"\\([A-Za-z@]+)(\*?)", s[i:])
                if not mm:
                    sym = s[i + 1] if i + 1 < n else ""
                    i += 2
                    if sym in "%&#_${}":
                        text(sym)
                    elif sym == ",":
                        text("\u202f")
                    elif sym in " \n\t":
                        text(" ")
                    elif sym in "!/@-":
                        pass
                    elif sym == "\\":
                        _opt, i = bracket_opt(s, i)
                        if not self.allow_breaks:
                            raise ValueError("Forced line break \\\\ in running text: %r" % s[max(0, i - 60):i])
                        out.append(("br",))
                    elif sym in ACCENTS:
                        arg, i = self._arg(s, i)
                        base = arg if len(arg) == 1 else ("\u0131" if arg == "\\i" else arg)
                        text(unicodedata.normalize("NFC", base + ACCENTS[sym]))
                    elif sym in ";:":
                        text(" ")
                    else:
                        raise ValueError("Unsupported control symbol \\%s near %r" % (sym, s[max(0, i - 40):i + 20]))
                    continue
                name = mm.group(1)
                i += len(mm.group(0))
                if name in ACCENTS and len(name) == 1:           # \v{c}, \H{o}, \c{c}, \u{a}
                    arg, i = self._arg(s, i)
                    text(unicodedata.normalize("NFC", arg + ACCENTS[name]))
                    continue
                # TeX: a control word swallows the spaces that follow it
                swallowed = self._skip_ws(s, i)
                if name in ("emph",):
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, i=not fmt.i))
                elif name in ("textit", "textsl"):
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, i=True))
                elif name == "textbf":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, b=True))
                elif name == "textsc":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, sc=True))
                elif name == "textup":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, i=False))
                elif name in ("textrm", "textnormal"):
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, tt=False))
                elif name == "texttt":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, tt=True))
                elif name == "textsubscript":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, vert="subscript"))
                elif name == "textsuperscript":
                    arg, i = self._arg(s, i)
                    out += self.parse(arg, replace(fmt, vert="superscript"))
                elif name == "mbox" or name == "hbox" or name == "text":
                    arg, i = self._arg(s, i)
                    for it in self.parse(arg, fmt):
                        if it[0] == "t":
                            parts = it[1].replace(" ", "\u00a0").split("-")
                            for k, part in enumerate(parts):
                                if k:
                                    out.append(("nbh", it[2]))
                                if part:
                                    out.append(("t", part, it[2]))
                        else:
                            out.append(it)
                elif name == "url":
                    arg, i = self._arg(s, i)
                    url = arg.replace("\\%", "%").replace("\\#", "#").replace("\\_", "_").replace("\\&", "&")
                    out.append(("link", url, [("t", url, fmt)]))
                elif name == "href":
                    url, i = self._arg(s, i)
                    arg, i = self._arg(s, i)
                    out.append(("link", url.replace("\\%", "%").replace("\\#", "#"), self.parse(arg, fmt)))
                elif name == "ref" or name == "autoref":
                    key, i = self._arg(s, i)
                    out += self.ref_items(key.strip(), fmt)
                elif name == "eqref":
                    key, i = self._arg(s, i)
                    out += self.ref_items(key.strip(), fmt, paren=True)
                elif name == "cite":
                    note, i = bracket_opt(s, i)
                    keys, i = self._arg(s, i)
                    text(self.cite_text(keys, note))
                elif name == "label":
                    _key, i = self._arg(s, i)
                elif name == "checkmark":
                    text("\u2713", replace(fmt, font="Segoe UI Symbol"))
                    i = swallowed
                elif name == "IEEEauthorrefmark":
                    arg, i = self._arg(s, i)
                    sym = REFMARKS.get(arg.strip())
                    if sym is None:
                        raise ValueError("Unsupported \\IEEEauthorrefmark{%s}" % arg)
                    text(sym, replace(fmt, vert="superscript", font="Cambria Math" if sym == "\u2217" else None))
                elif name in SYMBOLS:
                    text(SYMBOLS[name])
                    i = swallowed
                elif name in SIZE_HALFPT:
                    fmt = replace(fmt, size=SIZE_HALFPT[name])
                    i = swallowed
                elif name in DECL:
                    attr, val = DECL[name]
                    fmt = replace(fmt, **{attr: val})
                    i = swallowed
                elif name == "em":
                    fmt = replace(fmt, i=not fmt.i)
                    i = swallowed
                elif name in ("hspace", "hskip"):
                    if s[i:i + 1] == "*":
                        i += 1
                    _arg, i = self._arg(s, i)
                    text(" ")
                elif name in ("vspace", "addvspace"):
                    if s[i:i + 1] == "*":
                        i += 1
                    _arg, i = self._arg(s, i)
                elif name == "ensuremath":
                    arg, i = self._arg(s, i)
                    self.maths.append(arg)
                    out.append(("m", arg, fmt))
                elif name in ("newline", "linebreak"):
                    if not self.allow_breaks:
                        raise ValueError("Forced line break in running text")
                    out.append(("br",))
                elif name == "IEEEtriggeratref":
                    # LaTeX column balance only; the Word build balances its own last page.
                    _arg, i = self._arg(s, i)
                elif name in IGNORED:
                    i = swallowed
                elif name == "footnote":
                    raise ValueError("Footnotes are not supported by the Word converter")
                else:
                    raise ValueError("Unsupported LaTeX command \\%s near %r" % (name, s[max(0, i - 50):i + 30]))
                continue
            if c == "{":
                body, i = balanced(s, i)
                out += self.parse(body, fmt)
                continue
            if c == "}":
                raise ValueError("Unbalanced '}' near %r" % s[max(0, i - 40):i + 10])
            if c == "$":
                if s.startswith("$$", i):
                    raise ValueError("$$ display math inside running text")
                j = i + 1
                while j < n and not (s[j] == "$" and s[j - 1] != "\\"):
                    j += 1
                if j >= n:
                    raise ValueError("Unclosed $ near %r" % s[i:i + 40])
                math = s[i + 1:j].strip()
                self.maths.append(math)
                out.append(("m", math, fmt))
                i = j + 1
                continue
            if c == "~":
                text("\u00a0")
                i += 1
                continue
            if c in " \t\n":
                j = i
                while j < n and s[j] in " \t\n":
                    j += 1
                text(" ")
                i = j
                continue
            if c == "-":
                if s.startswith("---", i):
                    text("\u2014"); i += 3
                elif s.startswith("--", i):
                    text("\u2013"); i += 2
                else:
                    text("-"); i += 1
                continue
            if c == "`":
                if s.startswith("``", i):
                    text("\u201c"); i += 2
                else:
                    text("\u2018"); i += 1
                continue
            if c == "'":
                if s.startswith("''", i):
                    text("\u201d"); i += 2
                else:
                    text("\u2019"); i += 1
                continue
            if c in "&#^_":
                raise ValueError("Unescaped %r in text near %r" % (c, s[max(0, i - 40):i + 10]))
            text(c)
            i += 1
        return merge_items(out)


def merge_items(items):
    out = []
    for it in items:
        if it[0] == "t" and out and out[-1][0] == "t" and out[-1][2] == it[2]:
            out[-1] = ("t", out[-1][1] + it[1], it[2])
        else:
            out.append(it)
    # collapse runs of spaces across items
    res = []
    for it in out:
        if it[0] == "t":
            t = re.sub(r" {2,}", " ", it[1])
            if res and res[-1][0] == "t" and res[-1][1].endswith(" ") and t.startswith(" "):
                t = t[1:]
            if t:
                res.append(("t", t, it[2]))
        else:
            res.append(it)
    return res


def strip_items(items):
    items = list(items)
    while items and items[0][0] == "t" and not items[0][1].strip(" "):
        items.pop(0)
    while items and items[-1][0] == "t" and not items[-1][1].strip(" "):
        items.pop()
    if items and items[0][0] == "t":
        items[0] = ("t", items[0][1].lstrip(" "), items[0][2])
    if items and items[-1][0] == "t":
        items[-1] = ("t", items[-1][1].rstrip(" "), items[-1][2])
    return [x for x in items if not (x[0] == "t" and x[1] == "")]


def items_plain(items) -> str:
    out = []
    for it in items:
        if it[0] == "t":
            out.append(it[1])
        elif it[0] == "m":
            out.append(it[1])
        elif it[0] == "nbh":
            out.append("-")
        elif it[0] == "br":
            out.append(" ")
        elif it[0] == "link":
            out.append(items_plain(it[2]))
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 4. Document model
# ----------------------------------------------------------------------------------------------

@dataclass
class Block:
    kind: str
    data: dict = field(default_factory=dict)


@dataclass
class Cell:
    items: list
    span: int = 1
    align: str = "l"


@dataclass
class Row:
    cells: list
    rules_above: list = field(default_factory=list)     # "top"/"mid"/"bottom"/("cmid", a, b)
    rules_below: list = field(default_factory=list)
    space_above_pt: float = 0.0
    header: bool = False


def parse_colspec(spec: str) -> tuple[list, bool, bool]:
    cols, i = [], 0
    at_start = at_end = False
    spec = spec.strip()
    while i < len(spec):
        c = spec[i]
        if c in "lcr":
            cols.append(c)
            i += 1
        elif c in "pmb" and i + 1 < len(spec) and spec[i + 1] == "{":
            _w, i = balanced(spec, i + 1)
            cols.append("l")
        elif c == "@":
            body, j = balanced(spec, i + 1)
            if body.strip():
                raise ValueError("Non-empty @{} column separator unsupported: " + body)
            if not cols:
                at_start = True
            elif j >= len(spec.rstrip()):
                at_end = True
            i = j
        elif c == "*":
            cnt, j = balanced(spec, i + 1)
            sub, j = balanced(spec, j)
            spec = spec[:i] + sub * int(cnt) + spec[j:]
        elif c in "| \t\n":
            i += 1
        elif c in "<>":
            _b, i = balanced(spec, i + 1)
        else:
            raise ValueError("Unsupported tabular column spec %r" % spec)
    return cols, at_start, at_end


def split_top(s: str, sep: str) -> list[str]:
    parts, depth, cur, i = [], 0, [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            if s.startswith(sep, i) and sep == "\\\\":
                parts.append("".join(cur))
                cur = []
                i += 2
                opt = re.match(r"\s*\[[^\]]*\]", s[i:])
                if opt:
                    i += len(opt.group(0))
                continue
            cur.append(s[i:i + 2])
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == sep and depth == 0 and sep == "&":
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    parts.append("".join(cur))
    return parts


RULE_RE = re.compile(r"\s*\\(toprule|midrule|bottomrule|hline|cmidrule|cline|addlinespace)\b")


def parse_tabular(spec: str, body: str, inline: Inline, fmt: Fmt) -> dict:
    cols, at_start, at_end = parse_colspec(spec)
    rows: list[Row] = []
    pending_rules, pending_space = [], 0.0
    seen_mid = False
    for chunk in split_top(body, "\\\\"):
        s = chunk
        while True:
            mm = RULE_RE.match(s)
            if not mm:
                break
            kind = mm.group(1)
            s = s[mm.end():]
            if kind in ("toprule", "hline"):
                pending_rules.append("top" if not rows else "mid")
                opt, k = bracket_opt(s, 0)
                s = s[k:]
            elif kind == "midrule":
                pending_rules.append("mid")
                opt, k = bracket_opt(s, 0)
                s = s[k:]
                if rows and not seen_mid:
                    for r in rows:
                        r.header = True
                seen_mid = True
            elif kind == "bottomrule":
                pending_rules.append("bottom")
                opt, k = bracket_opt(s, 0)
                s = s[k:]
            elif kind in ("cmidrule", "cline"):
                s2 = re.match(r"\s*(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*\{(\d+)-(\d+)\}", s)
                if not s2:
                    raise ValueError("Bad cmidrule: %r" % s[:40])
                pending_rules.append(("cmid", int(s2.group(1)), int(s2.group(2))))
                s = s[s2.end():]
            elif kind == "addlinespace":
                opt, k = bracket_opt(s, 0)
                s = s[k:]
                pending_space += parse_len_pt(opt) if opt else 5.0
        if not s.strip():
            if rows and pending_rules:
                rows[-1].rules_below += pending_rules
                pending_rules = []
            continue
        cells, ci = [], 0
        for raw in split_top(s, "&"):
            raw_s = raw.strip()
            mm = re.match(r"\\multicolumn\s*\{(\d+)\}\s*\{([^}]*)\}\s*", raw_s)
            if mm:
                content, _ = balanced(raw_s, mm.end())
                span = int(mm.group(1))
                al = re.sub(r"[^lcr]", "", mm.group(2)) or "c"
                cells.append(Cell(strip_items(inline.parse(content, fmt)), span, al[0]))
                ci += span
            else:
                al = cols[ci] if ci < len(cols) else "l"
                cells.append(Cell(strip_items(inline.parse(raw_s, fmt)), 1, al))
                ci += 1
        if ci != len(cols):
            raise ValueError("Row has %d columns, spec has %d: %r" % (ci, len(cols), s[:80]))
        rows.append(Row(cells, rules_above=pending_rules, space_above_pt=pending_space))
        pending_rules, pending_space = [], 0.0
    if pending_rules and rows:
        rows[-1].rules_below += pending_rules
    # normalise: a rule above row k equals a rule below row k-1
    for k in range(1, len(rows)):
        if rows[k].rules_above:
            rows[k - 1].rules_below += rows[k].rules_above
            rows[k].rules_above = []
    return {"cols": cols, "at_start": at_start, "at_end": at_end, "rows": rows}


def parse_len_pt(txt: str) -> float:
    mm = re.match(r"\s*([0-9.]+)\s*(pt|mm|cm|in|em|ex|bp)\s*$", txt or "")
    if not mm:
        raise ValueError("Unsupported length %r" % txt)
    v = float(mm.group(1))
    return v * {"pt": 1, "bp": 72.27 / 72, "mm": 2.845, "cm": 28.45, "in": 72.27, "em": 10, "ex": 4.3}[mm.group(2)]


class SourceModel:
    def __init__(self, tex: Path, aux: dict, extra_dirs=()):
        self.tex = tex
        self.aux = aux
        self.inputs = []
        raw = expand_inputs(tex, self.inputs)
        head, _, rest = raw.partition("\\begin{document}")
        body, _, _ = rest.partition("\\end{document}")
        self.macros = parse_macros(head)
        gp = re.search(r"\\graphicspath\s*\{((?:\{[^}]*\})+)\}", head)
        self.graphicspath = [ROOT] + [ROOT / p for p in re.findall(r"\{([^{}]+)\}", gp.group(1) if gp else "")]
        self.graphicspath += list(extra_dirs)      # placeholder stand-ins last: never shadow real figures
        body = expand_macros(body, self.macros)
        self.inline = Inline(aux["labels"], aux["cites"])
        self.blocks: list[Block] = []
        self.eq_counter = 0
        self._parse_front(body)

    # -- front matter --
    def _parse_front(self, body: str):
        br = Inline(self.aux["labels"], self.aux["cites"], allow_breaks=True)
        br.maths = self.inline.maths
        mm = re.search(r"\\title\s*(?=\{)", body)
        title, end_title = balanced(body, mm.end())
        self.blocks.append(Block("title", {"items": strip_items(br.parse(title))}))
        am = re.search(r"\\author\s*(?=\{)", body)
        author, _ = balanced(body, am.end())
        names, affils = [], []
        for bm in re.finditer(r"\\IEEEauthorblock([NA])\s*(?=\{)", author):
            content, _ = balanced(author, bm.end())
            (names if bm.group(1) == "N" else affils).append(content)
        if not names:
            raise ValueError("No \\IEEEauthorblockN in \\author")
        groups = []
        for k, n in enumerate(names):
            a = affils[k] if k < len(affils) else ""
            groups.append({"name": strip_items(br.parse(n)),
                           "affil_lines": [strip_items(br.parse(x)) for x in re.split(r"\\\\", a) if x.strip()]})
        separate = bool(re.search(r"\\and\b", author)) and len(groups) > 1
        self.blocks.append(Block("authors", {"groups": groups, "columns": separate}))
        abstract, a0, a1 = env_body(body, "abstract")
        keywords, k0, k1 = env_body(body, "IEEEkeywords")
        if abstract is not None:
            self.blocks.append(Block("abstract", {"items": strip_items(self.inline.parse(abstract))}))
        if keywords is not None:
            self.blocks.append(Block("keywords", {"items": strip_items(self.inline.parse(keywords))}))
        mt = body.find("\\maketitle")
        start = max(mt + len("\\maketitle"), a1, k1)
        self._parse_body(body[start:])

    # -- body --
    STRUCT = re.compile(
        r"\\(section|subsection|subsubsection)(\*?)\s*(?=[\[{])"
        r"|\\begin\{(figure\*?|table\*?|equation\*?|thebibliography|itemize|enumerate|align\*?|eqnarray\*?|gather\*?|multline\*?|center|flushleft|quote|displaymath)\}"
        r"|\n[ \t]*\n\s*|\\\[|\\par\b|\\noindent\b|\\IEEEPARstart|\\appendix\b|\\bibliography\{|\\newpage\b|\\clearpage\b")

    def _parse_body(self, text: str):
        buf, pos = [], 0
        state = {"noindent": False, "continuation": False}
        pending_floats: list[Block] = []

        def flush(before_eq=False):
            src = "".join(buf).strip()
            buf.clear()
            if src:
                items = strip_items(self.inline.parse(src))
                if items:
                    self.blocks.extend(pending_floats)
                    pending_floats.clear()
                    self.blocks.append(Block("para", {"items": items, "indent": not (state["noindent"] or state["continuation"]),
                                                      "continuation": state["continuation"], "before_eq": before_eq}))
            state["noindent"] = False
            state["continuation"] = False

        while True:
            mm = self.STRUCT.search(text, pos)
            if not mm:
                buf.append(text[pos:])
                break
            buf.append(text[pos:mm.start()])
            tok = mm.group(0)
            if mm.group(1):                                   # sectioning
                flush()
                self.blocks.extend(pending_floats)
                pending_floats.clear()
                _opt, j = bracket_opt(text, mm.end())
                title, j = balanced(text, j)
                level = {"section": 1, "subsection": 2, "subsubsection": 3}[mm.group(1)]
                self.blocks.append(Block("heading", {"level": level, "numbered": not mm.group(2),
                                                     "items": strip_items(self.inline.parse(title)),
                                                     "plain": items_plain(self.inline.parse(title))}))
                pos = j
            elif mm.group(3):
                env = mm.group(3)
                end = text.find("\\end{" + env + "}", mm.end())
                if end < 0:
                    raise ValueError("Unclosed " + env)
                inner = text[mm.end():end]
                pos = end + len("\\end{" + env + "}")
                if env.rstrip("*") in ("figure", "table"):
                    blk = self._float(env, inner)
                    if "".join(buf).strip():
                        pending_floats.append(blk)            # float inside a paragraph: anchor to it
                    else:
                        self.blocks.append(blk)
                elif env in ("equation", "equation*", "displaymath"):
                    flush(before_eq=True)
                    self._equation(inner, numbered=(env == "equation"))
                    after = text[pos:pos + 200]
                    state["continuation"] = not re.match(r"[ \t]*\n[ \t]*\n", after)
                elif env == "thebibliography":
                    flush()
                    self.blocks.extend(pending_floats)
                    pending_floats.clear()
                    self._bibliography(inner)
                elif env == "itemize":
                    flush()
                    for item in re.split(r"\\item\b", inner)[1:]:
                        self.blocks.append(Block("bullet", {"items": strip_items(self.inline.parse(item))}))
                else:
                    raise ValueError("Unsupported environment in body: " + env)
            elif tok.startswith("\\["):
                end = text.find("\\]", mm.end())
                flush(before_eq=True)
                self._equation(text[mm.end():end], numbered=False)
                pos = end + 2
                state["continuation"] = not re.match(r"[ \t]*\n[ \t]*\n", text[pos:pos + 200])
            elif tok.startswith("\\noindent"):
                flush()
                state["noindent"] = True
                pos = mm.end()
            elif tok.startswith("\\par") or not tok.strip():
                flush()
                pos = mm.end()
            elif tok.startswith("\\newpage") or tok.startswith("\\clearpage"):
                flush()
                pos = mm.end()
            else:
                raise ValueError("Unsupported structural command %r" % tok)
        flush()
        self.blocks.extend(pending_floats)

    def _equation(self, inner: str, numbered: bool):
        keys = re.findall(r"\\label\{([^}]+)\}", inner)
        latex = re.sub(r"\\label\{[^}]+\}", "", inner).strip()
        if re.search(r"\\\\|&", latex):
            raise ValueError("Multi-line display math is not supported: %r" % latex[:60])
        number = None
        if numbered and not re.search(r"\\nonumber|\\notag", latex):
            self.eq_counter += 1
            number = str(self.eq_counter)
            if keys and self.aux["labels"].get(keys[0]) != number:
                raise ValueError("Equation numbering mismatch for %s: AUX %s, counted %s"
                                 % (keys[0], self.aux["labels"].get(keys[0]), number))
        self.inline.maths.append(latex)
        self.blocks.append(Block("equation", {"latex": latex, "number": number, "label": keys[0] if keys else None,
                                              "display": True}))

    def _bibliography(self, inner: str):
        items = list(re.finditer(r"\\bibitem\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", inner))
        entries = []
        for k, it in enumerate(items):
            end = items[k + 1].start() if k + 1 < len(items) else len(inner)
            key = it.group(1)
            num = self.aux["cites"].get(key)
            if num is None:
                raise ValueError("Bibitem %s missing from AUX" % key)
            if int(num) != k + 1:
                raise ValueError("Bibliography numbering is not sequential at %s" % key)
            entries.append({"key": key, "number": int(num),
                            "items": strip_items(self.inline.parse(inner[it.end():end].strip()))})
        self.blocks.append(Block("heading", {"level": 1, "numbered": False, "items": [("t", "References", Fmt())],
                                             "plain": "References", "component": True}))
        self.blocks.append(Block("references", {"entries": entries}))

    def _find_graphic(self, name: str) -> tuple[Path, Path | None]:
        cands = []
        for d in self.graphicspath:
            base = d / name
            if base.suffix:
                cands.append(base)
            else:
                cands += [base.with_suffix(x) for x in (".pdf", ".png", ".jpg", ".eps")]
        src = next((c for c in cands if c.is_file()), None)
        if src is None:
            raise FileNotFoundError("Figure not found: " + name)
        png = src.with_suffix(".png")
        return src, (png if png.is_file() else None)

    def _float(self, env: str, inner: str) -> Block:
        kind = env.rstrip("*")
        wide = env.endswith("*")
        _opt, k = bracket_opt(inner, 0)
        inner = inner[k:]
        labels = re.findall(r"\\label\{([^}]+)\}", inner)
        number = None
        for key in labels:
            if key in self.aux["labels"]:
                number = self.aux["labels"][key]
        cap = re.search(r"\\caption\s*(?:\[[^\]]*\])?\s*(?=\{)", inner)
        caption_items = []
        if cap:
            ctext, cend = balanced(inner, cap.end())
            caption_items = strip_items(self.inline.parse(ctext))
            inner = inner[:cap.start()] + inner[cend:]
        inner = re.sub(r"\\label\{[^}]+\}", "", inner)
        size = None
        for mm in re.finditer(r"\\(tiny|scriptsize|footnotesize|small|normalsize)\b", inner.split("\\begin{tabular}")[0]):
            size = SIZE_HALFPT[mm.group(1)]
        tabcolsep = 6.0
        mm = re.search(r"\\setlength\s*\{?\\tabcolsep\}?\s*\{([^}]*)\}", inner)
        if mm:
            tabcolsep = parse_len_pt(mm.group(1))
        stretch = 1.0
        mm = re.search(r"\\renewcommand\s*\{?\\arraystretch\}?\s*\{([^}]*)\}", inner)
        if mm:
            stretch = float(mm.group(1))
        data = {"kind": kind, "wide": wide, "number": number, "labels": labels, "caption": caption_items,
                "size": size, "tabcolsep": tabcolsep, "stretch": stretch, "images": [], "tables": [], "notes": []}
        base_fmt = Fmt(size=size) if size else Fmt()
        # images
        for gm in re.finditer(r"\\includegraphics\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}", inner):
            opts, name = gm.group(1) or "", gm.group(2).strip()
            src, png = self._find_graphic(name)
            frac, rel = 1.0, ("text" if wide else "column")
            fm = re.search(r"width\s*=\s*([0-9.]*)\s*\\(textwidth|columnwidth|linewidth)", opts)
            if fm:
                frac = float(fm.group(1) or 1)
                rel = "text" if fm.group(2) == "textwidth" else rel
            abs_in = None
            am = re.search(r"width\s*=\s*([0-9.]+)\s*(in|cm|mm|pt)\b", opts)
            if am:
                abs_in = float(am.group(1)) / {"in": 1, "cm": 2.54, "mm": 25.4, "pt": 72.27}[am.group(2)]
            data["images"].append({"source": src, "png": png, "frac": frac, "rel": rel, "abs_in": abs_in})
        # tables
        for tm in re.finditer(r"\\begin\{tabular\}\s*(?=\{)", inner):
            spec, j = balanced(inner, tm.end())
            end = inner.find("\\end{tabular}", j)
            data["tables"].append(parse_tabular(spec, inner[j:end], self.inline, base_fmt))
        # notes: flushleft/center blocks or loose text after the tabular
        rest = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "", inner, flags=re.S)
        rest = re.sub(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^}]+\}", "", rest)
        rest = re.sub(r"\\setlength\s*\{?\\tabcolsep\}?\s*\{[^}]*\}|\\renewcommand\s*\{?\\arraystretch\}?\s*\{[^}]*\}", "", rest)
        for nm in re.finditer(r"\\begin\{(flushleft|center|flushright)\}(.*?)\\end\{\1\}", rest, flags=re.S):
            nsize = size
            sm = re.search(r"\\(tiny|scriptsize|footnotesize|small)\b", nm.group(2))
            if sm:
                nsize = SIZE_HALFPT[sm.group(1)]
            data["notes"].append({"align": {"flushleft": "left", "center": "center", "flushright": "right"}[nm.group(1)],
                                  "items": strip_items(self.inline.parse(nm.group(2), Fmt(size=nsize) if nsize else Fmt())),
                                  "size": nsize})
        leftover = re.sub(r"\\begin\{(flushleft|center|flushright)\}.*?\\end\{\1\}", "", rest, flags=re.S)
        leftover = re.sub(r"\\(centering|tiny|scriptsize|footnotesize|small|normalsize|vspace\*?\{[^}]*\}|hfill)", "", leftover)
        if leftover.strip():
            raise ValueError("Unhandled float content: %r" % leftover.strip()[:120])
        if kind == "figure" and not data["images"]:
            raise ValueError("Figure without \\includegraphics")
        if kind == "table" and not data["tables"]:
            raise ValueError("Table float without tabular")
        return Block("float", data)


# ----------------------------------------------------------------------------------------------
# 5. Math via pandoc
# ----------------------------------------------------------------------------------------------

def prep_math(latex: str) -> str:
    s = latex
    for old, new in (("rm", "mathrm"), ("bf", "mathbf"), ("it", "mathit"), ("cal", "mathcal"), ("sf", "mathsf"), ("tt", "mathtt")):
        s = re.sub(r"\{\\" + old + r"(?![A-Za-z])\s*([^{}]*)\}", lambda mm, new=new: "{\\" + new + "{" + mm.group(1) + "}}", s)
    if re.search(r"\\(rm|bf|it|cal)\b", s):
        raise ValueError("Unsupported old-style font switch in math: " + latex)
    return s


def convert_math(snippets: list[str], work: Path) -> dict:
    uniq = list(dict.fromkeys(snippets))
    work.mkdir(parents=True, exist_ok=True)
    lines = ["\\documentclass{article}", "\\usepackage{amsmath,amssymb}", "\\begin{document}"]
    for k, s in enumerate(uniq):
        lines += ["", "MATHSNIP%d" % k, "", "\\[" + prep_math(s) + "\\]", ""]
    lines.append("\\end{document}")
    src = work / "math_snippets.tex"
    src.write_text("\n".join(lines), encoding="utf-8")
    out = work / "math_snippets.docx"
    run = subprocess.run([str(PANDOC), str(src), "--from=latex", "--to=docx", "-o", str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if run.returncode:
        raise RuntimeError("pandoc failed: " + run.stderr)
    if "Could not convert TeX math" in run.stderr:
        raise RuntimeError("pandoc could not convert some math:\n" + run.stderr[:2000])
    xml = zipfile.ZipFile(out).read("word/document.xml")
    root = etree.fromstring(xml)
    paras = root.findall(".//" + w("p"))
    result, k = {}, 0
    for idx, p in enumerate(paras):
        txt = "".join(t.text or "" for t in p.iter(w("t")))
        mm = re.fullmatch(r"MATHSNIP(\d+)", txt.strip())
        if not mm:
            continue
        k = int(mm.group(1))
        nxt = paras[idx + 1] if idx + 1 < len(paras) else None
        om = nxt.find(".//" + m("oMath")) if nxt is not None else None
        if om is None:
            raise RuntimeError("No OMML produced for math: " + uniq[k])
        result[uniq[k]] = om
    missing = [s for s in uniq if s not in result]
    if missing:
        raise RuntimeError("Math snippets lost in pandoc conversion: %s" % missing[:5])
    for s, om in result.items():
        if s.lstrip().startswith("\\textstyle"):
            for lim in om.iter(m("limLoc")):
                lim.set(m("val"), "subSup")
    return result


# ----------------------------------------------------------------------------------------------
# 6. DOCX writer on the IEEE template
# ----------------------------------------------------------------------------------------------

@dataclass
class Layout:
    float_gap_pt: float = 8.0          # space between a top float and the text below (LaTeX: 7pt +-2)
    eq_space_pt: float = 12.0          # template 'equation' style: 12pt before/after
    tab_cap_after_pt: float = 6.0      # template 'table head': 6pt after
    fig_cap_before_pt: float = 4.0     # template 'figure caption': 4pt before
    widow_control: bool = True
    balance: bool = True
    shifts: dict = field(default_factory=dict)   # float index -> anchor block index override
    parked: tuple = ()                           # floats omitted in a measuring trial only

    def key(self):
        return json.dumps(dataclasses.asdict(self), sort_keys=True)


def twips(pt: float) -> int:
    return int(round(pt * 20))


def float_anchors(seq: list, L) -> list[int]:
    """Anchor block index for every float (in source order).

    Default: the float's source position; a float directly after headings is anchored before the
    first of them (heading keep-with-next stays intact). Layout.shifts overrides (LaTeX-like deferral
    to a later column). Anchors are kept monotonic so Word's automatic TABLE/Fig. numbering follows
    the LaTeX source order."""
    out, last = [], -1
    n = 0
    for k, b in enumerate(seq):
        if b.kind != "float":
            continue
        j = k
        while j > 0 and seq[j - 1].kind in ("heading", "float"):
            j -= 1
        a = L.shifts.get(n, j)
        a = max(a, last)
        out.append(a)
        last = a
        n += 1
    return out


class DocxWriter:
    def __init__(self, model: SourceModel, maths: dict, layout: Layout, bookmarks=True):
        from docx import Document
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        self.RT = RT
        self.model, self.maths, self.layout = model, maths, layout
        self.bookmarks = bookmarks
        self.doc = Document(str(TEMPLATE))
        self.body = self.doc.element.body
        self.styles = {}
        for st in self.doc.styles.element.findall(w("style")):
            nm = st.find(w("name"))
            if nm is not None:
                self.styles[nm.get(w("val"))] = st.get(w("styleId"))
        need = ["Normal", "heading 1", "heading 2", "heading 3", "heading 5", "Body Text", "paper title",
                "Author", "Abstract", "Keywords", "equation", "figure caption", "table head", "table copy",
                "table col head", "references", "bullet list"]
        miss = [n for n in need if n not in self.styles]
        if miss:
            raise ValueError("Template lacks styles: %s" % miss)
        self.bm_id = 1000
        self.float_count = 0
        self.stats = Counter()

    def sid(self, name):
        return self.styles[name]

    # -- template preparation --
    def prepare(self):
        sect_final = self.body.find(w("sectPr"))
        for el in list(self.body):
            if el is not sect_final:
                self.body.remove(el)
        for tag in ("footerReference", "headerReference", "titlePg"):
            for el in sect_final.findall(w(tag)):
                sect_final.remove(el)
        self.sect_template = deepcopy(sect_final)
        self._fix_numbering()
        settings = self.doc.settings.element
        for el in settings.findall(w("attachedTemplate")):
            settings.remove(el)
        cp = self.doc.core_properties
        cp.title = items_plain(self.model.blocks[0].data["items"]).strip()
        cp.author = ", ".join(items_plain(g["name"]).translate({ord(c): None for c in "\u2217\u2020\u2021"}).strip()
                              for g in self.model.blocks[1].data["groups"])
        cp.last_modified_by = ""
        cp.subject = "WiCOMM-2026 camera-ready manuscript (paper 167)"
        cp.keywords = ""
        cp.comments = "Generated by tools/build_word_cr.py from paper.tex"
        cp.revision = 1
        stamp = time.gmtime(self.model.tex.stat().st_mtime)
        import datetime
        dt = datetime.datetime(*stamp[:6])
        cp.created = dt
        cp.modified = dt

    def _fix_numbering(self):
        num = self.doc.part.numbering_part.element
        abstract_of = {n.get(w("numId")): n.find(w("abstractNumId")).get(w("val")) for n in num.findall(w("num"))}
        style_num = {}
        for st in self.doc.styles.element.findall(w("style")):
            np_ = st.find(w("pPr") + "/" + w("numPr") + "/" + w("numId"))
            if np_ is not None:
                style_num[st.get(w("styleId"))] = np_.get(w("val"))

        def lvl(style_name, ilvl):
            nid = style_num[self.sid(style_name)]
            aid = abstract_of[nid]
            an = num.find("%s[@%s='%s']" % (w("abstractNum"), w("abstractNumId"), aid))
            return an.find("%s[@%s='%s']" % (w("lvl"), w("ilvl"), ilvl))

        def set_suff(lv, val):
            old = lv.find(w("suff"))
            if old is not None:
                lv.remove(old)
            el = E("w:suff", {"val": val})
            lv.find(w("lvlText")).addprevious(el)

        def tnr(lv):
            rpr = lv.find(w("rPr"))
            if rpr is None:
                rpr = E("w:rPr")
                lv.append(rpr)
            for ch in list(rpr):                 # template carries w14 text effects on the numbers
                if not ch.tag.startswith("{%s}" % W_NS):
                    rpr.remove(ch)
            f = rpr.find(w("rFonts"))
            if f is None:
                f = E("w:rFonts")
                rpr.insert(0, f)
            for k in list(f.attrib):
                del f.attrib[k]
            for k in ("ascii", "hAnsi", "eastAsia", "cs"):
                f.set(w(k), "Times New Roman")

        # Numbered heads and captions follow the LaTeX rendering: "I. Intro", "A. Sub", "Fig. 1. ",
        # "TABLE I" on its own line. The separator space lives inside the number text: Word renders a
        # list suffix character with a fallback font (Arial) otherwise. References keep the template's
        # hanging-indent tab.
        for name, ilvl, text in (("heading 1", "0", "%1. "), ("heading 1", "1", "%2. "),
                                 ("figure caption", "0", "Fig. %1. ")):
            lv = lvl(name, ilvl)
            lv.find(w("lvlText")).set(w("val"), text)
            set_suff(lv, "nothing")
            tnr(lv)
        lv = lvl("table head", "0")
        lv.find(w("lvlText")).set(w("val"), "TABLE %1")
        set_suff(lv, "nothing")
        tnr(lv)
        lv = lvl("references", "0")      # "[n]" + an explicit Times tab run in each entry (hanging indent)
        set_suff(lv, "nothing")
        tnr(lv)

    # -- run building --
    def rpr(self, f: Fmt):
        rp = E("w:rPr")
        font = f.font or ("Courier New" if f.tt else None)
        if font:
            rp.append(E("w:rFonts", {"ascii": font, "hAnsi": font, "cs": font, "eastAsia": font}))
        if f.b:
            rp.append(E("w:b"))
            rp.append(E("w:bCs"))
        if f.i:
            rp.append(E("w:i"))
            rp.append(E("w:iCs"))
        if f.sc:
            rp.append(E("w:smallCaps"))
        if f.size:
            rp.append(E("w:sz", {"val": f.size}))
            rp.append(E("w:szCs", {"val": f.size}))
        if f.vert:
            rp.append(E("w:vertAlign", {"val": f.vert}))
        return rp if len(rp) else None

    def math_el(self, latex, f: Fmt):
        om = deepcopy(self.maths[latex])
        self.stats["omml_inline"] += 1
        for r in om.iter(m("r")):
            if f.size or f.b:
                mrpr = r.find(m("rPr"))
                if f.b:
                    if mrpr is None:
                        mrpr = E("m:rPr")
                        r.insert(0, mrpr)
                    sty = mrpr.find(m("sty"))
                    val = sty.get(m("val")) if sty is not None else "i"
                    if sty is None:
                        sty = E("m:sty")
                        mrpr.append(sty)
                    sty.set(m("val"), {"p": "b", "i": "bi", "b": "b", "bi": "bi"}.get(val, "b"))
                if f.size:
                    wr = E("w:rPr", None, E("w:sz", {"val": f.size}), E("w:szCs", {"val": f.size}))
                    if mrpr is not None:
                        mrpr.addnext(wr)
                    else:
                        r.insert(0, wr)
        return om

    def runs(self, items, base: Fmt | None = None) -> list:
        out = []
        for it in items:
            kind = it[0]
            if kind == "t":
                r = E("w:r")
                rp = self.rpr(it[2])
                if rp is not None:
                    r.append(rp)
                t = E("w:t")
                t.text = it[1]
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                r.append(t)
                out.append(r)
            elif kind == "nbh":
                r = E("w:r")
                rp = self.rpr(it[1])
                if rp is not None:
                    r.append(rp)
                r.append(E("w:noBreakHyphen"))
                out.append(r)
            elif kind == "br":
                out.append(E("w:r", None, E("w:br")))
            elif kind == "m":
                out.append(self.math_el(it[1], it[2]))
            elif kind == "link":
                rid = self.doc.part.relate_to(it[1], self.RT.HYPERLINK, is_external=True)
                hl = E("w:hyperlink", {"r:id": rid})
                for r in self.runs(it[2]):
                    hl.append(r)
                out.append(hl)
            else:
                raise ValueError(kind)
        return out

    def para(self, style, children=(), *, jc=None, first=None, left=None, hanging=None, before=None, after=None,
             keep_next=None, keep_lines=None, widow=None, numid=None, line=None, line_rule=None, mark_rpr=None,
             sect=None):
        p = E("w:p")
        ppr = E("w:pPr")
        ppr.append(E("w:pStyle", {"val": self.sid(style)}))
        if keep_next is not None:
            ppr.append(E("w:keepNext", {"val": "1" if keep_next else "0"}))
        if keep_lines:
            ppr.append(E("w:keepLines"))
        if widow is not None:
            ppr.append(E("w:widowControl", {"val": "1" if widow else "0"}))
        if numid is not None:
            ppr.append(E("w:numPr", None, E("w:ilvl", {"val": 0}), E("w:numId", {"val": numid})))
        if before is not None or after is not None or line is not None:
            sp = E("w:spacing")
            if before is not None:
                sp.set(w("before"), str(before))
            if after is not None:
                sp.set(w("after"), str(after))
            if line is not None:
                sp.set(w("line"), str(line))
                sp.set(w("lineRule"), line_rule or "auto")
            ppr.append(sp)
        if first is not None or left is not None or hanging is not None:
            ind = E("w:ind")
            if left is not None:
                ind.set(w("left"), str(left))
            if hanging is not None:
                ind.set(w("hanging"), str(hanging))
            elif first is not None:
                ind.set(w("firstLine"), str(first))
            ppr.append(ind)
        if jc:
            ppr.append(E("w:jc", {"val": jc}))
        if mark_rpr is not None:
            ppr.append(mark_rpr)
        if sect is not None:
            ppr.append(sect)
        p.append(ppr)
        for c in children:
            p.append(c)
        return p

    def section(self, cols: int, space: int, top: int, lr: int, first=False) -> etree._Element:
        s = deepcopy(self.sect_template)
        for el in s.findall(w("type")):
            s.remove(el)
        if not first:
            s.insert(0, E("w:type", {"val": "continuous"}))
        pm = s.find(w("pgMar"))
        pm.set(w("top"), str(top))
        pm.set(w("left"), str(lr))
        pm.set(w("right"), str(lr))
        c = s.find(w("cols"))
        c.set(w("num"), str(cols))
        c.set(w("space"), str(space))
        for ch in list(c):
            c.remove(ch)
        return s

    def add(self, el):
        self.body.find(w("sectPr")).addprevious(el)

    def bookmark(self, p, name):
        if not self.bookmarks:
            return
        self.bm_id += 1
        ppr = p.find(w("pPr"))
        bs = E("w:bookmarkStart", {"id": self.bm_id, "name": name})
        be = E("w:bookmarkEnd", {"id": self.bm_id})
        ppr.addnext(bs)
        bs.addnext(be)

    # -- floats --
    def float_wrapper(self, fdata, idx) -> etree._Element:
        L = self.layout
        wide = fdata["wide"]
        width = TEXT_W if wide else COL_W
        tbl = E("w:tbl")
        tpr = E("w:tblPr")
        tpr.append(E("w:tblpPr", {"leftFromText": 0, "rightFromText": 0, "topFromText": 0,
                                  "bottomFromText": twips(L.float_gap_pt), "vertAnchor": "margin",
                                  "horzAnchor": "margin" if wide else "text", "tblpXSpec": "center",
                                  "tblpYSpec": "top"}))
        tpr.append(E("w:tblOverlap", {"val": "never"}))
        tpr.append(E("w:tblW", {"w": width, "type": "dxa"}))
        tpr.append(E("w:jc", {"val": "center"}))
        tpr.append(E("w:tblLayout", {"type": "fixed"}))
        tpr.append(E("w:tblCellMar", None, E("w:top", {"w": 0, "type": "dxa"}), E("w:left", {"w": 0, "type": "dxa"}),
                     E("w:bottom", {"w": 0, "type": "dxa"}), E("w:right", {"w": 0, "type": "dxa"})))
        tpr.append(E("w:tblLook", {"val": "0000", "firstRow": 0, "lastRow": 0, "firstColumn": 0, "lastColumn": 0,
                                   "noHBand": 0, "noVBand": 0}))
        tpr.append(E("w:tblCaption", {"val": "float:%s:%s:%d" % (fdata["kind"], fdata["number"], idx)}))
        tbl.append(tpr)
        tbl.append(E("w:tblGrid", None, E("w:gridCol", {"w": width})))
        tr = E("w:tr", None, E("w:trPr", None, E("w:cantSplit")))
        tc = E("w:tc", None, E("w:tcPr", None, E("w:tcW", {"w": width, "type": "dxa"})))
        tr.append(tc)
        tbl.append(tr)
        content = self.figure_content(fdata, width) if fdata["kind"] == "figure" else self.table_content(fdata, width)
        for el in content:
            tc.append(el)
        if tc[-1].tag != w("p"):
            tc.append(self.para("Normal", [], before=0, after=0, line=20, line_rule="exact",
                                mark_rpr=E("w:rPr", None, E("w:sz", {"val": 2}), E("w:szCs", {"val": 2}))))
        return tbl

    def figure_content(self, fdata, width) -> list:
        from docx.shared import Emu
        els = []
        pic_runs = []
        for img in fdata["images"]:
            if img["abs_in"]:
                w_tw = int(img["abs_in"] * TWIP_PER_IN)
            else:
                w_tw = int((TEXT_W if img["rel"] == "text" else COL_W) * img["frac"])
            w_tw = min(w_tw, width)
            png = img["png"]
            if png is None:
                import fitz
                png = WORK / (img["source"].stem + "_300dpi.png")
                d = fitz.open(img["source"])
                d[0].get_pixmap(dpi=300, alpha=False).save(png)
                d.close()
            from PIL import Image
            with Image.open(png) as im:
                pw, ph = im.size
            w_emu = w_tw * EMU_PER_TWIP
            h_emu = int(w_emu * ph / pw)
            inline = self.doc.part.new_pic_inline(str(png), Emu(w_emu), Emu(h_emu))
            r = E("w:r", None, E("w:drawing"))
            r[0].append(inline)
            pic_runs.append(r)
            img["used_png"] = str(png)
            img["width_in"] = w_tw / TWIP_PER_IN
            self.stats["images"] += 1
        els.append(self.para("Normal", pic_runs, jc="center", first=0, before=0, after=0, keep_next=True))
        cap = self.para("figure caption", self.runs(fdata["caption"]),
                        before=twips(self.layout.fig_cap_before_pt), after=0, widow=True)
        els.append(cap)
        return els

    def table_content(self, fdata, width) -> list:
        els = []
        cap_children = [E("w:r", None, E("w:br"))] + self.runs(fdata["caption"])
        els.append(self.para("table head", cap_children, before=0, after=twips(self.layout.tab_cap_after_pt),
                             keep_next=True))
        for tab in fdata["tables"]:
            els.append(self.data_table(tab, fdata, width))
        for note in fdata["notes"]:
            els.append(self.para("table copy", self.runs(note["items"]), jc=note["align"], before=40, after=0,
                                 mark_rpr=E("w:rPr", None, E("w:sz", {"val": note["size"]}), E("w:szCs", {"val": note["size"]})) if note["size"] else None))
        return els

    def data_table(self, tab, fdata, avail) -> etree._Element:
        size = fdata["size"] or 16
        pad = twips(fdata["tabcolsep"])
        rows = tab["rows"]
        ncols = len(tab["cols"])
        widths = measure_columns(tab, size, self.maths)
        # natural width = content + 2*tabcolsep (minus @{} at the table edges)
        col_w = [int(x * 20) + 2 * pad for x in widths]
        if tab["at_start"]:
            col_w[0] -= pad
        if tab["at_end"]:
            col_w[-1] -= pad
        total = sum(col_w)
        self.stats["table_natural_width_twips_max"] = max(self.stats["table_natural_width_twips_max"], total)
        if total > avail:
            scale = avail / total
            col_w = [int(x * scale) for x in col_w]
            self.stats["tables_scaled"] += 1
        tbl = E("w:tbl")
        tpr = E("w:tblPr")
        tpr.append(E("w:tblW", {"w": sum(col_w), "type": "dxa"}))
        tpr.append(E("w:jc", {"val": "center"}))
        tpr.append(E("w:tblLayout", {"type": "fixed"}))
        tpr.append(E("w:tblCellMar", None, E("w:top", {"w": 0, "type": "dxa"}), E("w:left", {"w": pad, "type": "dxa"}),
                     E("w:bottom", {"w": 0, "type": "dxa"}), E("w:right", {"w": pad, "type": "dxa"})))
        tpr.append(E("w:tblLook", {"val": "0000", "firstRow": 0, "lastRow": 0, "firstColumn": 0, "lastColumn": 0,
                                   "noHBand": 0, "noVBand": 0}))
        tbl.append(tpr)
        tbl.append(E("w:tblGrid", None, *[E("w:gridCol", {"w": x}) for x in col_w]))
        heavy, light, cmid = 6, 4, 3
        above_sep, below_sep = 1.5, 2.5         # booktabs \aboverulesep / \belowrulesep (pt)
        for ri, row in enumerate(rows):
            tr = E("w:tr", None, E("w:trPr", None, E("w:cantSplit"), *( [E("w:tblHeader")] if row.header else [])))
            prev_below = rows[ri - 1].rules_below if ri else []
            ci = 0
            for cell in row.cells:
                cw = sum(col_w[ci:ci + cell.span])
                tcpr = E("w:tcPr", None, E("w:tcW", {"w": cw, "type": "dxa"}))
                if cell.span > 1:
                    tcpr.append(E("w:gridSpan", {"val": cell.span}))
                borders = E("w:tcBorders")
                if ri == 0 and "top" in row.rules_above:
                    borders.append(E("w:top", {"val": "single", "sz": heavy, "space": 0, "color": "000000"}))
                bot = None
                for rule in row.rules_below:
                    if rule == "bottom":
                        bot = heavy
                    elif rule in ("mid", "top"):
                        bot = max(bot or 0, light)
                    elif isinstance(rule, tuple):
                        a, b = rule[1] - 1, rule[2] - 1
                        if ci <= b and ci + cell.span - 1 >= a:
                            bot = max(bot or 0, cmid)
                if bot:
                    borders.append(E("w:bottom", {"val": "single", "sz": bot, "space": 0, "color": "000000"}))
                if len(borders):
                    tcpr.append(borders)
                mar = E("w:tcMar")
                if ci == 0 and tab["at_start"]:
                    mar.append(E("w:left", {"w": 0, "type": "dxa"}))
                if ci + cell.span == ncols and tab["at_end"]:
                    mar.append(E("w:right", {"w": 0, "type": "dxa"}))
                tcpr.append(E("w:noWrap"))
                if len(mar):
                    tcpr.append(mar)
                tcpr.append(E("w:vAlign", {"val": "center"}))
                before = 0.0
                if (ri == 0 and row.rules_above) or prev_below:
                    before += below_sep
                before += row.space_above_pt
                after = above_sep if row.rules_below else 0.0
                style = "table col head" if row.header else "table copy"
                items = cell.items
                fmt_b = row.header
                if fmt_b:
                    items = [(x[0], x[1], replace(x[2], b=True)) if x[0] in ("t", "m") else x for x in items]
                size_items = [(x[0], x[1], replace(x[2], size=x[2].size or (size if size != 16 else None)))
                              if x[0] in ("t", "m") else x for x in items]
                mark = E("w:rPr", None, E("w:sz", {"val": size}), E("w:szCs", {"val": size})) if size != 16 else None
                p = self.para(style, self.runs(size_items), jc={"l": "left", "c": "center", "r": "right"}[cell.align],
                              first=0, before=twips(before), after=twips(after), mark_rpr=mark,
                              line=int(240 * fdata["stretch"]) if fdata["stretch"] != 1 else None)
                tr.append(E("w:tc", None, tcpr, p))
                ci += cell.span
            tbl.append(tr)
        self.stats["data_tables"] += 1
        return tbl

    # -- main build --
    def build(self) -> Counter:
        self.prepare()
        L = self.layout
        blocks = self.model.blocks
        body_style = "Body Text"
        # section 1: title and author block (template: top 540, left/right 893, 1 column)
        title = blocks[0]
        title_para = self.para("paper title", self.runs(title.data["items"]))
        self.add(title_para)
        authors = blocks[1].data
        auth_paras = []
        if authors["columns"]:
            # IEEE template layout: the title closes a one-column section, then each author is
            # one "Author" paragraph (name, then affiliation lines) in a balanced continuous
            # section with one column per author.
            title_para.find(w("pPr")).append(self.section(1, 720, 540, 893, first=True))
            for g in authors["groups"]:
                runs = list(self.runs(g["name"]))
                for ln in g["affil_lines"]:
                    runs.append(E("w:r", None, E("w:br")))
                    runs += self.runs(ln)
                auth_paras.append(self.para("Author", runs, before=120, after=120))
            for p in auth_paras:
                self.add(p)
            auth_sect = self.section(len(authors["groups"]), 720, 450, 893)
            auth_paras[-1].find(w("pPr")).append(auth_sect)
        else:
            for g in authors["groups"]:
                auth_paras.append(self.para("Author", self.runs(g["name"]), before=120, after=40))
                lines = []
                for k, ln in enumerate(g["affil_lines"]):
                    if k:
                        lines.append(E("w:r", None, E("w:br")))
                    lines += self.runs(ln)
                if lines:
                    auth_paras.append(self.para("Author", lines, before=0, after=120))
            for p in auth_paras:
                self.add(p)
            sect1 = self.section(1, 720, 540, 893, first=True)
            auth_paras[-1].find(w("pPr")).append(sect1)
        # body
        seq = list(blocks[2:])
        self.anchors = float_anchors(seq, L)
        fidx = {id(b): n for n, b in enumerate([x for x in seq if x.kind == "float"])}
        by_anchor = {}
        for b in seq:
            if b.kind == "float" and fidx[id(b)] not in L.parked:
                by_anchor.setdefault(self.anchors[fidx[id(b)]], []).append(b)
        emitted_floats = 0
        last_body_para = None
        for k, b in enumerate(seq):
            for fb in by_anchor.get(k, []):
                self.add(self.float_wrapper(fb.data, fidx[id(fb)]))
                emitted_floats += 1
            if b.kind == "float":
                continue
            els = self.block_xml(b, body_style)
            for el in els:
                self.add(el)
                if el.tag == w("p"):
                    last_body_para = el
            if els and els[0].tag == w("p"):
                self.bookmark(els[0], "_blk%d" % k)
        for kk in sorted(a for a in by_anchor if a >= len(seq)):
            for fb in by_anchor[kk]:
                self.add(self.float_wrapper(fb.data, fidx[id(fb)]))
                emitted_floats += 1
        if emitted_floats != len(fidx) - len(L.parked):
            raise ValueError("Float emission count mismatch")
        # end of the two-column body
        final = self.body.find(w("sectPr"))
        body_sect = self.section(2, COL_SPACE, 1080, BODY_MARGIN_LR)
        if L.balance:
            last_body_para.find(w("pPr")).append(body_sect)
            closing = self.para("Normal", [], before=0, after=0, line=20, line_rule="exact",
                                mark_rpr=E("w:rPr", None, E("w:sz", {"val": 2}), E("w:szCs", {"val": 2})))
            self.add(closing)
            new_final = self.section(1, 720, 1080, BODY_MARGIN_LR)
        else:
            new_final = body_sect
        final.getparent().replace(final, new_final)
        return self.stats

    def block_xml(self, b: Block, body_style) -> list:
        L = self.layout
        d = b.data
        if b.kind == "abstract":
            items = [("t", "Abstract", Fmt(i=True)), ("t", "\u2014", Fmt())] + d["items"]
            return [self.para("Abstract", self.runs(items))]
        if b.kind == "keywords":
            items = [("t", "Index Terms\u2014", Fmt())] + d["items"]
            return [self.para("Keywords", self.runs(items))]
        if b.kind == "heading":
            if not d["numbered"]:
                return [self.para("heading 5", self.runs(d["items"]), keep_next=True)]
            style = {1: "heading 1", 2: "heading 2", 3: "heading 3"}[d["level"]]
            return [self.para(style, self.runs(d["items"]))]
        if b.kind == "para":
            first = None if d["indent"] else 0
            before = 0 if d["continuation"] else None
            after = 0 if d["before_eq"] else None
            return [self.para(body_style, self.runs(d["items"]), first=first, before=before, after=after,
                              widow=L.widow_control, keep_next=True if d["before_eq"] else None)]
        if b.kind == "bullet":
            return [self.para("bullet list", self.runs(d["items"]), widow=L.widow_control)]
        if b.kind == "equation":
            om = deepcopy(self.maths[d["latex"]])
            content = list(om)
            omath = E("m:oMath")
            if d["number"]:
                arr = E("m:eqArr", None, E("m:eqArrPr", None, E("m:maxDist", {"val": 1}), E("m:ctrlPr")))
                e = E("m:e")
                for c in content:
                    e.append(c)
                hash_r = E("m:r", None, E("m:t"))
                hash_r[0].text = "#"
                e.append(hash_r)
                num_r = E("m:r", None, E("m:rPr", None, E("m:sty", {"val": "p"})), E("m:t"))
                num_r[-1].text = d["number"]
                e.append(E("m:d", None, E("m:dPr", None, E("m:ctrlPr")), E("m:e", None, num_r)))
                arr.append(e)
                omath.append(arr)
                self.stats["numbered_equations"] += 1
            else:
                for c in content:
                    omath.append(c)
            omp = E("m:oMathPara", None, E("m:oMathParaPr", None, E("m:jc", {"val": "center"})), omath)
            self.stats["display_equations"] += 1
            mark = E("w:rPr", None, E("w:rFonts", {"ascii": "Times New Roman", "hAnsi": "Times New Roman",
                                                   "cs": "Times New Roman", "eastAsia": "Times New Roman"}))
            return [self.para("equation", [omp], before=twips(L.eq_space_pt), after=twips(L.eq_space_pt),
                              keep_lines=True, mark_rpr=mark, jc="center")]
        if b.kind == "references":
            out = []
            for ent in d["entries"]:
                out.append(self.para("references", [E("w:r", None, E("w:tab"))] + self.runs(ent["items"]),
                                     widow=True))
                self.stats["references"] += 1
            return out
        raise ValueError("Unknown block kind " + b.kind)

    def save(self, path: Path):
        self.doc.save(str(path))


# -- table column measurement (Times New Roman / Cambria Math metrics) --
_FONTS = {}


def _font(bold, italic, halfpt, math=False, sym=False):
    from PIL import ImageFont
    key = (bold, italic, halfpt, math, sym)
    if key not in _FONTS:
        fdir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        size = halfpt / 2 * 10   # measure at 10x for precision (points*10 -> px)
        if sym:
            _FONTS[key] = ImageFont.truetype(str(fdir / "seguisym.ttf"), int(size))
        elif math:
            _FONTS[key] = ImageFont.truetype(str(fdir / "cambria.ttc"), int(size), index=1)
        else:
            name = {(False, False): "times.ttf", (True, False): "timesbd.ttf", (False, True): "timesi.ttf",
                    (True, True): "timesbi.ttf"}[(bold, italic)]
            _FONTS[key] = ImageFont.truetype(str(fdir / name), int(size))
    return _FONTS[key]


def omml_text_width(om, halfpt) -> float:
    total = 0.0
    for r in om.iter(m("r")):
        t = "".join(x.text or "" for x in r.iter(m("t")))
        scale = 1.0
        anc = r.getparent()
        while anc is not None:
            if anc.tag in (m("sub"), m("sup")):
                scale *= 0.72
            anc = anc.getparent()
        total += _font(False, False, halfpt, math=True).getlength(t) / 10 * scale
    total += 1.0 * len(list(om.iter(m("d"))))
    return total


def measure_items(items, halfpt, maths) -> float:
    total = 0.0
    for it in items:
        if it[0] == "t":
            f = it[2]
            hp = f.size or halfpt
            if f.vert:
                hp = hp * 0.65
            if f.font == "Segoe UI Symbol":
                total += _font(False, False, hp, sym=True).getlength(it[1]) / 10
                continue
            txt = it[1].upper() if f.sc else it[1]
            hpx = hp * (0.8 if f.sc else 1)
            total += _font(f.b, f.i, hpx).getlength(txt) / 10
        elif it[0] == "m":
            total += omml_text_width(maths[it[1]], it[2].size or halfpt)
        elif it[0] == "nbh":
            total += halfpt / 2 * 0.333
    return total


def measure_columns(tab, halfpt, maths) -> list:
    ncols = len(tab["cols"])
    widths = [0.0] * ncols
    spans = []
    for row in tab["rows"]:
        ci = 0
        for cell in row.cells:
            items = cell.items
            if row.header:     # header rows are set in the template's bold 'table col head' style
                items = [(x[0], x[1], replace(x[2], b=True)) if x[0] == "t" else x for x in items]
            wpt = measure_items(items, halfpt, maths) * (1.08 if row.header else 1.04) + 0.8
            if cell.span == 1:
                widths[ci] = max(widths[ci], wpt)
            else:
                spans.append((ci, cell.span, wpt))
            ci += cell.span
    for ci, span, wpt in spans:
        cur = sum(widths[ci:ci + span])
        if wpt > cur:
            extra = (wpt - cur) / span
            for k in range(ci, ci + span):
                widths[k] += extra
    return widths


# ----------------------------------------------------------------------------------------------
# 7. Word COM export
# ----------------------------------------------------------------------------------------------

def word_export(docx: Path, pdf: Path, attempts: int = 3) -> dict:
    """Export via Word, retrying: in a synced folder the previous PDF can be briefly locked."""
    for attempt in range(1, attempts + 1):
        try:
            return _word_export_once(docx, pdf)
        except RuntimeError:
            if attempt == attempts:
                raise
            print("  Word export did not write the PDF; retrying (%d/%d)" % (attempt + 1, attempts))
            time.sleep(5)


def _word_export_once(docx: Path, pdf: Path) -> dict:
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    word = None
    info = {"floats": [], "bookmarks": {}}
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            word.AutomationSecurity = 3      # msoAutomationSecurityForceDisable: no macros
        except Exception:
            pass
        doc = word.Documents.Open(str(docx), False, True, False)   # FileName, ConfirmConversions, ReadOnly, AddToRecent
        try:
            doc.Repaginate()
            info["pages_word"] = int(doc.ComputeStatistics(2))
            for k in range(1, doc.Tables.Count + 1):
                t = doc.Tables(k)
                title = t.Title or ""
                if title.startswith("float:"):
                    r = t.Range
                    info["floats"].append({"title": title, "page": int(r.Information(3)),
                                           "x_pt": float(r.Information(5)), "y_pt": float(r.Information(6))})
            doc.Bookmarks.ShowHidden = True
            for k in range(1, doc.Bookmarks.Count + 1):
                bm = doc.Bookmarks(k)
                if bm.Name.startswith("_blk"):
                    r = bm.Range
                    info["bookmarks"][bm.Name] = (int(r.Information(3)), float(r.Information(5)),
                                                  float(r.Information(6)))
            if pdf.exists():
                pdf.unlink()
            # ExportAsFixedFormat(Output, 17=PDF, OpenAfter, OptimizeFor=print, Range=all, From, To,
            #   Item=content, IncludeDocProps, KeepIRM, CreateBookmarks=none, DocStructureTags,
            #   BitmapMissingFonts, UseISO19005_1)
            doc.ExportAsFixedFormat(str(pdf), 17, False, 0, 0, 1, 1, 0, True, True, 0, True, True, False)
        finally:
            doc.Close(0)
    finally:
        if word is not None:
            try:
                word.Quit(0)
            except Exception:
                pass
        pythoncom.CoUninitialize()
    for junk in list(docx.parent.glob("~$*")) + list(docx.parent.glob("~WRL*.tmp")):
        try:
            junk.unlink()
        except OSError:
            pass
    if not pdf.exists():
        raise RuntimeError("Word did not write the PDF")
    return info


# ----------------------------------------------------------------------------------------------
# 8. Verification
# ----------------------------------------------------------------------------------------------

TRANS = {ord("\u2206"): "\u0394", ord("\u2212"): "-", ord("\u2010"): "-", ord("\u2011"): "-", ord("\u2012"): "-",
         ord("\u00ad"): "-", ord("\u200b"): None, ord("\u2217"): "*", ord("\u2019"): "'", ord("\u2018"): "'",
         ord("\u201c"): '"', ord("\u201d"): '"', ord("\ufb01"): "fi", ord("\ufb02"): "fl", ord("\u2013"): "-",
         ord("\u2014"): "-", ord("\u03f5"): "\u03b5", ord("\u2032"): "'", ord("\u00a0"): " ", ord("\u202f"): " ",
         ord("\u2009"): " ", ord("\u2003"): " ", ord("\u2002"): " ", ord("\u2016"): "||", ord("\u2215"): "/"}


SPACING_ACCENTS = dict.fromkeys(map(ord, "ˇ¨´˘˙˚˝¸˛ˆ˜¯"))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(TRANS).lower()
    # accents: LaTeX may emit a separate spacing accent glyph (e.g. "Graˇcanin")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn")
    s = s.translate(SPACING_ACCENTS)
    # join words hyphenated across line/column ends (LaTeX) or wrapped after a hyphen/dash (Word)
    return re.sub(r"-\s+(?=[a-z0-9α-ω])", "-", s)


def skeleton(s: str) -> str:
    return re.sub(r"[^0-9a-z\u03b1-\u03c9\u0394\u03b4\u2713]", "", norm(s))


def pdf_blocks(path: Path) -> list[tuple[int, str]]:
    import fitz
    out = []
    with fitz.open(path) as d:
        for p in d:
            for b in p.get_text("blocks", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES):
                if b[6] == 0 and b[4].strip():
                    out.append((p.number + 1, b[4]))
    return out


def items_text(items, maths) -> str:
    out = []
    for it in items:
        if it[0] == "m":
            out.append("".join(t.text or "" for t in maths[it[1]].iter(m("t"))))
        elif it[0] == "link":
            out.append(items_text(it[2], maths))
        else:
            out.append(items_plain([it]))
    return "".join(out)


def float_text(model: SourceModel, maths) -> str:
    parts = []
    for b in model.blocks:
        if b.kind != "float":
            continue
        d = b.data
        parts.append(items_text(d["caption"], maths))
        for tab in d["tables"]:
            for row in tab["rows"]:
                for c in row.cells:
                    parts.append(items_text(c.items, maths))
        for n in d["notes"]:
            parts.append(items_text(n["items"], maths))
        for img in d["images"]:
            if img["source"].suffix.lower() == ".pdf":
                import fitz
                with fitz.open(img["source"]) as fd:
                    parts.append(fd[0].get_text())
    return " ".join(parts)


def classify(blocks, ftext: str):
    """Split PDF text blocks into prose and float material (captions, table cells, figure text)."""
    fskel = skeleton(ftext)
    ftok = set(tokens(ftext))
    prose, flt = [], []
    for page, txt in blocks:
        sk = skeleton(txt)
        tk = tokens(txt)
        caption = re.match(r"\s*(TABLE [IVXL]+\b|Fig\. \d+\.)", txt)
        frac = sum(t in ftok for t in tk) / len(tk) if tk else 1.0
        if caption or (sk and sk in fskel) or (frac >= 0.9 and len(txt) < 400):
            flt.append((page, txt))
        else:
            prose.append((page, txt))
    return prose, flt


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\u0394(\[])", text)
    out = []
    for p in parts:
        sk = skeleton(p)
        letters = sum(c.isalpha() for c in sk)
        if len(sk) >= 15 and letters >= 0.5 * len(sk):
            out.append(p.strip())
    return out


def find_fuzzy(sk: str, hay: str) -> float:
    if sk in hay:
        return 1.0
    best = 0.0
    L = len(sk)
    probes = {sk[:12], sk[L // 2 - 6:L // 2 + 6], sk[-12:], sk[L // 4:L // 4 + 12], sk[3 * L // 4 - 12:3 * L // 4]}
    for pr in probes:
        if len(pr) < 8:
            continue
        start = 0
        while True:
            pos = hay.find(pr, start)
            if pos < 0:
                break
            off = sk.find(pr)
            lo = max(0, pos - off - L // 8)
            win = hay[lo:lo + L + L // 4]
            ratio = difflib.SequenceMatcher(None, sk, win, autojunk=False).ratio() * (L + len(win)) / (2 * L)
            best = max(best, min(1.0, ratio))
            start = pos + 1
    return best


def tokens(text: str) -> list[str]:
    t = norm(text).replace("-", "")
    out = []
    for x in re.split(r"[^0-9a-z\u03b1-\u03c9\u0394\u03b4\u2713\.%]+", t):
        x = x.strip(".")
        if x:
            out.append(x)
    return out


def pdf_fonts(path: Path) -> list[dict]:
    import fitz
    fonts = {}
    with fitz.open(path) as d:
        for p in d:
            for f in p.get_fonts(full=True):
                xref, ext, typ, base = f[0], f[1], f[2], f[3]
                name = base.split("+", 1)[-1]
                rec = fonts.setdefault((name, typ), {"font": name, "type": typ, "embedded": ext != "n/a",
                                                     "pages": set()})
                rec["embedded"] = rec["embedded"] and ext != "n/a"
                rec["pages"].add(p.number + 1)
    return [dict(v, pages=sorted(v["pages"])) for v in fonts.values()]


def object_counts_pdf(path: Path) -> dict:
    import fitz
    lines = []
    with fitz.open(path) as d:
        n = len(d)
        for p in d:
            lines += [l.strip() for l in p.get_text().splitlines()]
    joined = "\n".join(lines)
    eqs = sorted({int(x) for x in re.findall(r"\((\d+)\)$", joined, flags=re.M)})
    tables = re.findall(r"^TABLE ([IVXL]+)\b", joined, flags=re.M)
    figs = re.findall(r"^Fig\. (\d+)\.", joined, flags=re.M)
    heads = list(re.finditer(r"^\s*R\s?EFERENCES\s*$", joined, flags=re.M | re.I))
    ref_start = heads[-1].end() if heads else -1
    refs = sorted({int(x) for x in re.findall(r"^\[(\d+)\]", joined[ref_start:], flags=re.M)}) if ref_start > 0 else []
    return {"pages": n, "equation_numbers": eqs, "tables": tables, "figures": [int(x) for x in figs],
            "references": len(refs), "reference_numbers_contiguous": refs == list(range(1, len(refs) + 1))}


def render_pages(pdf: Path, outdir: Path, dpi=70) -> list[str]:
    import fitz
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("page-*.png"):
        old.unlink()
    names = []
    with fitz.open(pdf) as d:
        for p in d:
            name = outdir / ("page-%d.png" % (p.number + 1))
            p.get_pixmap(dpi=dpi, alpha=False).save(name)
            names.append(str(name.relative_to(ROOT)))
    return names


def column_fill(pdf: Path) -> dict:
    """Bottom y of text in each column on the last page (balance check)."""
    import fitz
    with fitz.open(pdf) as d:
        p = d[-1]
        mid = p.rect.width / 2
        left = [b[3] for b in p.get_text("blocks") if b[4].strip() and b[2] <= mid + 5]
        right = [b[3] for b in p.get_text("blocks") if b[4].strip() and b[0] >= mid - 5]
        return {"left_bottom_pt": round(max(left), 1) if left else None,
                "right_bottom_pt": round(max(right), 1) if right else None,
                "page_height_pt": round(p.rect.height, 1)}


def verify(model: SourceModel, maths: dict, latex_pdf: Path, word_pdf: Path, docx: Path, stats: dict,
           layout: Layout, word_info: dict, trials: list, target: int) -> dict:
    ftext = float_text(model, maths)
    lb, wb = pdf_blocks(latex_pdf), pdf_blocks(word_pdf)
    lprose, _lf = classify(lb, ftext)
    wprose, _wf = classify(wb, ftext)
    ltext_all = " ".join(t for _, t in lb)
    wtext_all = " ".join(t for _, t in wb)
    ltext = " ".join(t for _, t in lprose)
    wtext = " ".join(t for _, t in wprose)
    lt, wt = tokens(ltext), tokens(wtext)
    sm = difflib.SequenceMatcher(None, lt, wt, autojunk=False)
    lt_all, wt_all = tokens(ltext_all), tokens(wtext_all)
    # vector text inside the LaTeX figure PDFs has no counterpart in Word (figures are 300-dpi PNGs)
    fig_tok = Counter()
    for b in model.blocks:
        if b.kind == "float":
            for img in b.data["images"]:
                if img["source"].suffix.lower() == ".pdf":
                    import fitz
                    with fitz.open(img["source"]) as fd:
                        fig_tok += Counter(tokens(fd[0].get_text()))
    miss_words = (Counter(lt_all) - fig_tok) - Counter(wt_all)
    extra_words = Counter(wt_all) - Counter(lt_all)
    wsk, wsk_all = skeleton(wtext), skeleton(wtext_all)
    lsk, lsk_all = skeleton(ltext), skeleton(ltext_all)

    def score_in(sk, prose, full):
        sc = find_fuzzy(sk, prose)
        return sc if sc >= 1.0 else max(sc, find_fuzzy(sk, full))

    missing, minor = [], []
    lsents = sentences(ltext)
    for s in lsents:
        score = score_in(skeleton(s), wsk, wsk_all)
        if score < 0.9:
            missing.append({"sentence": s[:300], "score": round(score, 3)})
        elif score < 1.0:
            minor.append({"sentence": s[:160], "score": round(score, 3)})
    extra = []
    wsents = sentences(wtext)
    for s in wsents:
        score = score_in(skeleton(s), lsk, lsk_all)
        if score < 0.9:
            extra.append({"sentence": s[:300], "score": round(score, 3)})
    dup = []
    lcount = Counter(skeleton(s) for s in lsents)
    for s, c in Counter(skeleton(s) for s in wsents).items():
        if c > lcount.get(s, 0) and lcount.get(s, 0) > 0:
            dup.append({"skeleton": s[:120], "word": c, "latex": lcount[s]})
    with zipfile.ZipFile(docx) as z:
        dx = etree.fromstring(z.read("word/document.xml"))
    docx_counts = {
        "display_equations": len(dx.findall(".//" + m("oMathPara"))),
        "numbered_equations": len(dx.findall(".//" + m("eqArr"))),
        "omml_objects_total": len(dx.findall(".//" + m("oMath"))),
        "float_boxes": len([t for t in dx.iter(w("tblCaption")) if t.get(w("val"), "").startswith("float:")]),
        "data_tables": stats.get("data_tables", 0),
        "figures_images": len(dx.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline")),
        "reference_paragraphs": stats.get("references", 0),
    }
    src_counts = {
        "numbered_equations": sum(1 for b in model.blocks if b.kind == "equation" and b.data["number"]),
        "tables": sum(1 for b in model.blocks if b.kind == "float" and b.data["kind"] == "table"),
        "figures": sum(1 for b in model.blocks if b.kind == "float" and b.data["kind"] == "figure"),
        "references": sum(len(b.data["entries"]) for b in model.blocks if b.kind == "references"),
    }
    lfonts, wfonts = pdf_fonts(latex_pdf), pdf_fonts(word_pdf)
    expected = ("TimesNewRoman", "CambriaMath", "SegoeUISymbol")
    unexpected = [f["font"] for f in wfonts if not f["font"].replace("-", "").replace(",", "").startswith(expected)]
    bad_glyphs = sorted({hex(ord(c)) for c in wtext_all if unicodedata.category(c) in ("Co", "Cn") or c == "\ufffd"})
    lat_counts, word_counts = object_counts_pdf(latex_pdf), object_counts_pdf(word_pdf)
    float_pages = []
    lf = model.aux["floats"]
    for k, f in enumerate(word_info.get("floats", [])):
        _, kind, num, _i = f["title"].split(":")
        lp = next((x["page"] for x in lf if x["kind"] == kind and x["number"] == num), None)
        float_pages.append({"float": "%s %s" % (kind, num), "latex_page": lp, "word_page": f["page"],
                            "word_column": 1 if f["x_pt"] < 297 else 2})
    report = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": {"tex": str(model.tex.relative_to(ROOT)), "sha256": sha(model.tex), "inputs": model.inputs},
        "template": {"path": str(TEMPLATE.relative_to(ROOT)), "sha256": sha(TEMPLATE)},
        "outputs": {"latex_pdf": str(latex_pdf.relative_to(ROOT)), "docx": str(docx.relative_to(ROOT)),
                    "word_pdf": str(word_pdf.relative_to(ROOT)), "docx_sha256": sha(docx), "word_pdf_sha256": sha(word_pdf)},
        "page_counts": {"latex_pdf": lat_counts["pages"], "word_pdf": word_counts["pages"], "target": target,
                        "word_matches_target": word_counts["pages"] == target,
                        "latex_is_six_pages": lat_counts["pages"] == 6, "word_is_six_pages": word_counts["pages"] == 6},
        "fonts": {"latex_pdf": lfonts, "word_pdf": wfonts,
                  "latex_all_embedded": all(f["embedded"] for f in lfonts),
                  "word_all_embedded": all(f["embedded"] for f in wfonts),
                  "word_unexpected_fonts": unexpected, "word_private_or_missing_glyphs": bad_glyphs},
        "text_parity": {
            "prose_tokens_latex": len(lt), "prose_tokens_word": len(wt),
            "prose_sequence_ratio": round(sm.ratio(), 5),
            "prose_diff_ratio": round(1 - sm.ratio(), 5),
            "all_tokens_latex": len(lt_all), "all_tokens_word": len(wt_all),
            "tokens_missing_in_word": dict(miss_words.most_common(40)),
            "tokens_extra_in_word": dict(extra_words.most_common(40)),
            "latex_sentences_checked": len(lsents),
            "missing_sentences": missing,
            "sentences_with_minor_differences": minor,
            "word_sentences_not_in_latex": extra,
            "duplicated_sentences": dup,
            "method": ("PyMuPDF text (dehyphenated); float captions/cells/figure text separated from prose; "
                       "NFKC + symbol normalisation; sentences matched on alphanumeric skeletons (>=0.9 fuzzy)"),
        },
        "counts": {"source_model": src_counts, "latex_pdf": {k: lat_counts[k] for k in lat_counts if k != "pages"},
                   "word_pdf": {k: word_counts[k] for k in word_counts if k != "pages"}, "docx": docx_counts,
                   "inline_and_display_omml_written": stats.get("omml_inline", 0) + stats.get("display_equations", 0)},
        "floats": float_pages,
        "column_gaps_before_last_page": word_info.get("gaps", []),
        "last_page_columns": column_fill(word_pdf),
        "layout": dataclasses.asdict(layout),
        "fit_trials": trials,
        "tables": {"max_natural_width_twips": stats.get("table_natural_width_twips_max"), "column_width_twips": COL_W,
                   "tables_scaled_to_fit": stats.get("tables_scaled", 0)},
        "page_images": render_pages(word_pdf, PAGES),
    }
    checks = {
        "pages_match_target": report["page_counts"]["word_matches_target"],
        "fonts_embedded": report["fonts"]["word_all_embedded"] and report["fonts"]["latex_all_embedded"],
        "no_unexpected_fonts": not unexpected,
        "no_missing_sentences": not missing,
        "no_duplicated_sentences": not dup,
        "equations_match": src_counts["numbered_equations"] == docx_counts["numbered_equations"]
                           == len(word_counts["equation_numbers"]) == len(lat_counts["equation_numbers"]),
        "tables_match": src_counts["tables"] == len(word_counts["tables"]) == len(lat_counts["tables"]),
        "figures_match": src_counts["figures"] == len(word_counts["figures"]) == len(lat_counts["figures"]),
        "references_match": src_counts["references"] == word_counts["references"] == lat_counts["references"],
        "table_numbers_match": word_counts["tables"] == lat_counts["tables"],
        "figure_numbers_match": word_counts["figures"] == lat_counts["figures"],
        "no_float_on_page_1": all(f["word_page"] > 1 for f in float_pages),
        "no_column_gaps": not word_info.get("gaps"),
    }
    report["checks"] = checks
    return report


# ----------------------------------------------------------------------------------------------
# 9. Driver and page fitting
# ----------------------------------------------------------------------------------------------

def build_once(model, maths, layout, docx: Path, pdf: Path, bookmarks=True):
    writer = DocxWriter(model, maths, layout, bookmarks=bookmarks)
    stats = writer.build()
    writer.save(docx)
    info = word_export(docx, pdf)
    info["anchors"] = writer.anchors
    info["gaps"] = column_gaps(pdf)
    import fitz
    with fitz.open(pdf) as d:
        info["pages_pdf"] = len(d)
    return stats, info


# Text area of the template body section (points): top 1080 twips, bottom margin 1440 twips.
MID_X_PT = PAGE_W / 20 / 2
TEXT_BOTTOM_PT = 16838 / 20 - 1440 / 20
GAP_PT = 30.0            # > ~2.5 body lines of unused space at a column foot counts as a gap


def column_gaps(pdf: Path) -> list[dict]:
    """Unused space at the foot of each column, except on the last page (which is balanced)."""
    import fitz
    gaps = []
    with fitz.open(pdf) as d:
        for p in d:
            if p.number == len(d) - 1:
                continue
            bottoms = {1: 0.0, 2: 0.0}
            for b in p.get_text("dict")["blocks"]:
                x0, y0, x1, y1 = b["bbox"]
                if b["type"] == 0 and not "".join(s["text"] for l in b["lines"] for s in l["spans"]).strip():
                    continue
                cols = [1, 2] if (x0 < MID_X_PT - 20 and x1 > MID_X_PT + 20) else ([1] if x0 < MID_X_PT else [2])
                for c in cols:
                    bottoms[c] = max(bottoms[c], y1)
            for c in (1, 2):
                gap = TEXT_BOTTOM_PT - bottoms[c]
                if gap > GAP_PT:
                    gaps.append({"page": p.number + 1, "col": c, "gap_pt": round(gap, 1)})
    return gaps


def colpos(page: int, x_pt: float) -> tuple[int, int]:
    return (page, 1 if x_pt < MID_X_PT else 2)


def next_col(pc):
    return (pc[0], 2) if pc[1] == 1 else (pc[0] + 1, 1)


def block_pos(info, k):
    v = info["bookmarks"].get("_blk%d" % k)
    return colpos(v[0], v[1]) if v else None


def find_problem(model, layout: Layout, info, tried: set):
    """First layout defect caused by a float anchor: a float on the title page, or a float that dragged
    its anchor paragraph into the next column and left the previous column's foot empty."""
    anchors = info["anchors"]
    floats = []
    for f in info["floats"]:
        idx = int(f["title"].split(":")[3])
        floats.append((idx, colpos(f["page"], f["x_pt"])))
    on_title = [idx for idx, pc in floats if pc[0] == 1]
    if on_title and ("title", tuple(on_title)) not in tried:
        return ("title", on_title, (2, 1))
    for g in info["gaps"]:
        gap_col = (g["page"], g["col"])
        nxt = next_col(gap_col)
        pushers = [idx for idx, pc in floats if pc == nxt and block_pos(info, anchors[idx]) == nxt]
        if pushers and ("gap", tuple(pushers), nxt) not in tried:
            return ("gap", pushers, nxt)
    return None


def reanchor(model, layout: Layout, idxs, target_col, pinfo):
    """Anchor floats at the first block that starts in target_col (or later) in the parked layout."""
    seq = model.blocks[2:]
    for idx in idxs:
        start = pinfo["anchors_all"][idx]
        new = len(seq)
        for k in range(start, len(seq)):
            pos = block_pos(pinfo, k)
            if pos is not None and pos >= target_col:
                new = k
                break
        j = new
        while j > 0 and j - 1 >= start and seq[j - 1].kind == "heading":
            pos = block_pos(pinfo, j - 1)
            if pos is None or pos < target_col:
                break
            j -= 1
        layout.shifts[idx] = j


def settle(model, layout: Layout, trial, max_fixes=8):
    """Re-anchor floats until none sits on the title page and none leaves a column gap (LaTeX-like
    deferral of a top float to the next column)."""
    stats, info = trial(layout)
    tried = set()
    for _ in range(max_fixes):
        prob = find_problem(model, layout, info, tried)
        if prob is None:
            break
        kind, idxs, target_col = prob
        tried.add((kind, tuple(idxs)) if kind == "title" else (kind, tuple(idxs), target_col))
        seq = model.blocks[2:]
        anchors_all = float_anchors(seq, layout)
        parked = replace(layout, shifts=dict(layout.shifts), parked=tuple(sorted(set(layout.parked) | set(idxs))))
        _s, pinfo = trial(parked, note="measure: %s floats %s parked" % (kind, idxs))
        pinfo["anchors_all"] = anchors_all
        reanchor(model, layout, idxs, target_col, pinfo)
        stats, info = trial(layout)
    return stats, info


def slide(model, layout: Layout, trial, stats, info, max_steps=3):
    """Close a remaining column gap by anchoring the float that opens the next column one to
    max_steps blocks later, so text fills the gap first (never directly after a heading, which
    would separate it from its paragraph). Keeps the best layout with the same page count."""
    best = (layout, stats, info)
    best_gap = sum(g["gap_pt"] for g in info["gaps"])
    if not best_gap:
        return best
    seq = model.blocks[2:]
    anchors = float_anchors(seq, layout)
    floats = [(int(f["title"].split(":")[3]), colpos(f["page"], f["x_pt"])) for f in info["floats"]]
    for g in info["gaps"]:
        nxt = next_col((g["page"], g["col"]))
        for idx, pc in floats:
            if pc != nxt:
                continue
            for step in range(1, max_steps + 1):
                a = anchors[idx] + step
                if a >= len(seq) or seq[a - 1].kind == "heading":
                    continue
                cand = replace(layout, shifts=dict(layout.shifts))
                cand.shifts[idx] = a
                s2, i2 = trial(cand, note="slide float %d to block %d" % (idx, a))
                gap = sum(x["gap_pt"] for x in i2["gaps"])
                if i2["pages_pdf"] == info["pages_pdf"] and gap < best_gap:
                    best, best_gap = (cand, s2, i2), gap
                    if not gap:
                        return best
    return best


def ladder(pages: int, target: int) -> list[dict]:
    if pages > target:        # tighten, staying inside the template's spacing norms
        return [dict(eq_space_pt=9.0), dict(eq_space_pt=6.0), dict(eq_space_pt=6.0, float_gap_pt=6.0),
                dict(eq_space_pt=6.0, float_gap_pt=6.0, tab_cap_after_pt=3.0),
                dict(eq_space_pt=6.0, float_gap_pt=5.0, tab_cap_after_pt=3.0, fig_cap_before_pt=2.0),
                dict(eq_space_pt=6.0, float_gap_pt=5.0, tab_cap_after_pt=3.0, fig_cap_before_pt=2.0, widow_control=False)]
    return [dict(float_gap_pt=10.0), dict(float_gap_pt=12.0), dict(float_gap_pt=12.0, tab_cap_after_pt=8.0),
            dict(float_gap_pt=14.0, tab_cap_after_pt=8.0, fig_cap_before_pt=6.0)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tex", type=Path, default=ROOT / "paper.tex")
    ap.add_argument("--target-pages", type=int, default=None,
                    help="Word PDF page target (default: the LaTeX PDF page count)")
    ap.add_argument("--no-fit", action="store_true", help="export once with template-default layout")
    ap.add_argument("--skip-latex", action="store_true", help="reuse build/camera_ready/latex (must be current)")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--placeholder-missing-figures", action="store_true",
                    help="preview aid: stand-in images for figures that do not exist yet (flagged in the report)")
    args = ap.parse_args()
    tex = args.tex.resolve()
    t0 = time.time()
    placeholders = []
    if args.placeholder_missing_figures:
        placeholders = make_placeholders(tex)
        if placeholders:
            print("WARNING: placeholder figures used for: " + ", ".join(placeholders))
    elif PLACEHOLDER_DIR.exists():
        shutil.rmtree(PLACEHOLDER_DIR)
    extra = PLACEHOLDER_DIR if placeholders else None
    if args.skip_latex and (LATEX_DIR / (tex.stem + ".pdf")).exists():
        latex_pdf = LATEX_DIR / (tex.stem + ".pdf")
    else:
        latex_pdf = compile_latex(tex, extra)
    aux = read_aux(LATEX_DIR / (tex.stem + ".aux"))
    import fitz
    with fitz.open(latex_pdf) as d:
        latex_pages = len(d)
    target = args.target_pages or latex_pages
    print("LaTeX PDF: %s (%d pages)" % (latex_pdf.relative_to(ROOT), latex_pages))
    WORD_DIR.mkdir(parents=True, exist_ok=True)
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    try:
        model = SourceModel(tex, aux, extra_dirs=[extra] if extra else [])
        maths = convert_math(model.inline.maths, WORK)
        trials = []
        docx_t, pdf_t = WORK / "trial.docx", WORK / "trial.pdf"

        def trial(lay, note=""):
            stats, info = build_once(model, maths, lay, docx_t, pdf_t)
            rec = {"note": note, "pages": info["pages_pdf"], "float_pages": [f["page"] for f in info["floats"]],
                   "gaps": info["gaps"], "layout": dataclasses.asdict(lay)}
            trials.append(rec)
            short = {k: v for k, v in dataclasses.asdict(lay).items() if v != getattr(Layout(), k)}
            print("  trial %d: %d pages, floats on pages %s, column gaps %s %s %s"
                  % (len(trials), info["pages_pdf"], rec["float_pages"],
                     [(g["page"], g["col"], g["gap_pt"]) for g in info["gaps"]], short, note))
            return stats, info

        layout = Layout()
        stats, info = settle(model, layout, trial)
        if not args.no_fit and info["pages_pdf"] == target and info["gaps"]:
            layout, stats, info = slide(model, layout, trial, stats, info)
        if not args.no_fit and info["pages_pdf"] != target:
            base = replace(layout, shifts=dict(layout.shifts))
            for step in ladder(info["pages_pdf"], target):
                cand = replace(base, shifts=dict(base.shifts), **step)
                s2, i2 = settle(model, cand, trial)
                if i2["pages_pdf"] == target:
                    layout, stats, info = cand, s2, i2
                    break
            else:
                cand = replace(layout, shifts=dict(layout.shifts), balance=False)
                s2, i2 = settle(model, cand, trial)
                if i2["pages_pdf"] == target:
                    layout, stats, info = cand, s2, i2
        # final build without helper bookmarks, exported again from the delivered DOCX
        docx = WORD_DIR / (STEM + ".docx")
        pdf = WORD_DIR / (STEM + ".pdf")
        stats, info_final = build_once(model, maths, layout, docx, pdf, bookmarks=False)
        info_final["bookmarks"] = info.get("bookmarks", {})
        report = verify(model, maths, latex_pdf, pdf, docx, stats, layout, info_final, trials, target)
        report["placeholder_figures"] = placeholders
        report["checks"]["no_placeholder_figures"] = not placeholders
        report["elapsed_s"] = round(time.time() - t0, 1)
        (WORD_DIR / "word_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str),
                                                   encoding="utf-8")
    finally:
        if not args.keep_work and WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
    pc = report["page_counts"]
    print("LaTeX PDF pages: %d   Word PDF pages: %d   (target %d)" % (pc["latex_pdf"], pc["word_pdf"], target))
    print("checks: " + ", ".join("%s=%s" % kv for kv in report["checks"].items()))
    print("prose diff ratio: %.4f; missing sentences: %d" % (report["text_parity"]["prose_diff_ratio"],
                                                              len(report["text_parity"]["missing_sentences"])))
    print("report: %s" % (WORD_DIR / "word_report.json").relative_to(ROOT))
    if pc["latex_pdf"] != 6 or pc["word_pdf"] != 6:
        print("NOTE: WiCOMM target is exactly 6 pages (LaTeX %d, Word %d)." % (pc["latex_pdf"], pc["word_pdf"]))


if __name__ == "__main__":
    main()
