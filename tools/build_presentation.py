"""Build the WiCOMM-2026 presentation for paper 167 on the conference template.

python tools/build_presentation.py <path to the pptx skill's scripts/add_slide.py>

Reads WiCOMM_2026.pptx (slide 1: title design, slide 2: content design), duplicates the
content slide to eight slides, and fills them in an editorial, figure-first style: the
approved heading, a 24 pt takeaway sentence, and one dominant visual per slide, laid out
with whitespace and hairline rules rather than cards. Navy marks protected service and
fail-closed, red marks lost assurance and fail-degraded. Icons come from
presentation/assets/icons (rendered by presentation/assets/make_icons.js). Every number is
from the camera-ready paper. Writes presentation/Paper167_WiCOMM2026_Presentation.pptx.
"""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'WiCOMM_2026.pptx'
OUT_DIR = ROOT / 'presentation'
OUT = OUT_DIR / 'Paper167_WiCOMM2026_Presentation_Final.pptx'
ICONS = OUT_DIR / 'assets' / 'icons'
ADD_SLIDE = Path(sys.argv[1]) if len(sys.argv) > 1 else None

FONT = 'Calibri'
NAVY = RGBColor(0x00, 0x20, 0x60)
NAVY2 = RGBColor(0x2F, 0x55, 0x96)
RED = RGBColor(0xC0, 0x00, 0x00)
RED2 = RGBColor(0xD9, 0x5A, 0x4E)
GREY = RGBColor(0xB4, 0xBB, 0xC8)
INK = RGBColor(0x1F, 0x2A, 0x44)
MUTED = RGBColor(0x4E, 0x58, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RULE = RGBColor(0xC9, 0xD2, 0xE3)
TINT_RED = RGBColor(0xF8, 0xE1, 0xDE)
MOUNT1 = RGBColor(0xE1, 0xE8, 0xF0)
MOUNT2 = RGBColor(0xCF, 0xDB, 0xE8)
NB = '‑'   # non-breaking hyphen
SP = ' '   # non-breaking space
HEX = {NAVY: 'navy', RED: 'red', WHITE: 'white', GREY: 'grey'}
L, R = 0.75, 12.45          # content edges, matching the template's heading rule
TOP = 1.95                  # first content line under the takeaway


# ---------------------------------------------------------------- primitives
def para_runs(p, runs, size, color, bold=False, italic=False):
    for item in runs:
        text_, opt = (item, {}) if isinstance(item, str) else item
        r = p.add_run()
        r.text = text_
        f = r.font
        f.name = FONT
        f.size = Pt(opt.get('size', size))
        f.bold = opt.get('bold', bold)
        f.italic = opt.get('italic', italic)
        f.color.rgb = opt.get('color', color)
        if opt.get('sup'):
            r.font._rPr.set('baseline', '30000')
        if opt.get('sub'):
            r.font._rPr.set('baseline', '-25000')


def text(slide, x, y, w, h, paras, size=18, color=INK, bold=False, italic=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space_after=0, name=None):
    """paras: list of paragraphs; each is a str or a list of str/(str, opts) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space_after:
            p.space_after = Pt(space_after)
        para_runs(p, [runs] if isinstance(runs, (str, tuple)) else runs, size, color, bold, italic)
    return tb


def rect(slide, x, y, w, h, fill, radius=None, name=None):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def rule(slide, x1, y1, x2, y2, color=RULE, width=1.0, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    return c


def icon(slide, name, color, x, y, size):
    return slide.shapes.add_picture(str(ICONS / f'{name}_{HEX[color]}.png'), Inches(x), Inches(y),
                                    Inches(size), Inches(size))


def dot(slide, x, y, d, fill):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def pill(slide, x, y, w, h, label, fill, color, size=15):
    s = rect(slide, x, y, w, h, fill, radius=0.5)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    para_runs(tf.paragraphs[0], [label], size, color, bold=True)
    return s


def heading(slide, title):
    for sh in slide.shapes:
        if sh.is_placeholder:
            runs = sh.text_frame.paragraphs[0].runs
            runs[0].text = title
            for r in runs[1:]:
                r.text = ''
            return
    raise RuntimeError('no heading placeholder')


def takeaway(slide, sentence):
    return text(slide, L, 1.12, R - L, 0.6, [sentence], size=24, color=NAVY, bold=True,
                anchor=MSO_ANCHOR.MIDDLE, name='Takeaway')


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body


def chart_fonts(ch, size=14):
    ch.font.name = FONT
    ch.font.size = Pt(size)
    ch.font.color.rgb = MUTED


def figure(tmp, name, clip=None):
    page = fitz.open(ROOT / 'figures/camera_ready' / f'{name}.pdf')[0]
    r = fitz.Rect(*clip) if clip else page.rect
    png = tmp / f'{name}{"_clip" if clip else ""}.png'
    pix = page.get_pixmap(dpi=500, alpha=False, clip=r)
    img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).convert('RGBA')
    a = np.array(img)
    white = (a[..., :3].min(axis=2) >= 248)          # the figure's painted white page
    a[white, 3] = 0
    Image.fromarray(a).save(png)
    return png, r.height / r.width


# ---------------------------------------------------------------- slide 1
def slide_title(s):
    by_name = {sh.name.split(';')[1]: sh for sh in s.shapes if sh.has_text_frame}

    def fill(shape, runs, size, color, bold=True, italic=False, top=None, height=None):
        if top is not None:
            shape.top = Inches(top)
        if height is not None:
            shape.height = Inches(height)
        tf = shape.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        for extra in tf.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)
        p.alignment = PP_ALIGN.CENTER
        para_runs(p, runs, size, color, bold=bold, italic=italic)

    fill(by_name['44'], ['Fail-Closed or Fail-Degraded? A Simulation Study of Forced Assurance Loss in '
                         'Contested Multi-Hop QKD Networks'], 30, RED, top=3.62, height=1.2)
    fill(by_name['45'], ['Lakshya Jain', ('1', {'sup': True}), ', Siddhi Arora', ('2', {'sup': True})],
         22, NAVY, top=5.2)
    fill(by_name['46'], [('1', {'sup': True}), 'Maharaja Agrasen Institute of Technology, Delhi   |   ',
                         ('2', {'sup': True}), 'Noida Institute of Engineering and Technology, Greater Noida'],
         17, NAVY, bold=False, italic=True, top=5.72)
    pid = by_name['47']
    pid.left, pid.width = Inches(11.12), Inches(1.4)
    fill(pid, ['167'], 16, RED, italic=True, top=7.09)
    pid.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    notes(s, "Good morning, everyone. I'm Lakshya Jain, and this is joint work with Siddhi Arora. "
             "Our question is a practical one. When a multi-hop quantum key distribution network "
             "runs out of key, should it refuse service, or quietly fall back to weaker "
             "cryptography? And if an attacker wants to push it into that fallback, what does it "
             "cost them?")


# ---------------------------------------------------------------- slide 2
def slide_motivation(s):
    heading(s, 'Motivation: When Quantum Key Runs Out')
    takeaway(s, 'Out of key, a network must refuse service or quietly weaken it')
    base = 4.3
    for x, w, h, c in ((0.95, 3.2, 1.25, MOUNT1), (3.35, 3.6, 1.85, MOUNT2), (6.35, 3.5, 1.45, MOUNT1),
                       (9.1, 3.2, 1.15, MOUNT2)):
        m = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x), Inches(base - h), Inches(w), Inches(h))
        m.fill.solid()
        m.fill.fore_color.rgb = c
        m.line.fill.background()
        m.shadow.inherit = False
    stops = [(1.45, 4.08), (2.55, 3.0), (5.15, 2.4), (8.1, 2.8), (10.7, 3.1), (11.8, 4.08)]
    for (x1, y1), (x2, y2) in zip(stops, stops[1:]):
        rule(s, x1, y1, x2, y2, color=NAVY, width=2.0, dash=True)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        icon(s, 'FaKey', RED, mx - 0.16, my - 0.52, 0.32)
    for x, y in stops[1:-1]:
        dot(s, x - 0.33, y - 0.36, 0.66, WHITE)
        icon(s, 'FaBroadcastTower', NAVY, x - 0.25, y - 0.29, 0.5)
    pill(s, L, 3.9, 1.4, 0.4, 'Rear base', NAVY, WHITE, size=15)
    pill(s, R - 1.4, 3.9, 1.4, 0.4, 'Front post', RED, WHITE, size=15)
    text(s, L, 4.5, R - L, 0.7, [
        [f'Every relay re-encrypts the key with a one{NB}time pad, so an ', ('n', {'italic': True}),
         f'{NB}hop path pays for key on ', ('every hop', {'bold': True}),
         ', and a free-space hop makes only about 10', ('2', {'sup': True}), f'{SP}bit/s.']],
         size=18, color=MUTED)
    rule(s, 6.6, 5.45, 6.6, 6.85)
    cols = [(L, NAVY, 'FaLock', 'Fail closed', 'Refuse the request, as a layered PQC design does.',
             'The commander sees an outage and can act.'),
            (6.95, RED, 'FaLockOpen', 'Fail degraded', f'Fall back to a weaker cipher, as ITU{NB}T Y.3803 allows.',
             'Nobody notices until the audit.')]
    for x, c, ic, title, l1, l2 in cols:
        icon(s, ic, c, x, 5.48, 0.46)
        text(s, x + 0.65, 5.4, 4.8, 0.55, [title], size=26, color=c, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x, 6.05, 5.45, 0.85, [[(l1, {'bold': True})], [l2]], size=18, space_after=2)
    notes(s, "Picture a brigade up in the mountains, talking to its rear base through a chain of "
             "relay sites. In a trusted-relay network every relay decrypts and re-encrypts the key, "
             "so a path of n hops pays for key n times over, shown by the red keys on each link. "
             "Free-space links only make around a hundred bits a second, so what runs out first is "
             "key, not connectivity. At that point the network has two choices. It can fail closed "
             "and refuse the request: the commander sees an outage and can react. Or it can fail "
             "degraded and fall back to a weaker cipher, which ITU-T Y.3803 allows: nothing looks "
             "wrong until someone audits the logs. Which is worse, and what does it cost an attacker "
             "to force it?")


# ---------------------------------------------------------------- slide 3
def slide_gap(s):
    heading(s, 'Research Gap and Contributions')
    takeaway(s, 'Prior work counts service, not the ITS protection it lost')
    c1, c2 = 5.0, 6.35            # column centres: served? / which grade?
    rect(s, c2 - 0.62, TOP - 0.1, 1.24, 4.05, TINT_RED, radius=0.08, name='Missing column')
    text(s, L, TOP, 3.6, 0.35, ['Line of prior work'], size=15, color=MUTED, bold=True)
    text(s, c1 - 0.7, TOP, 1.4, 0.35, ['Served?'], size=15, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    text(s, c2 - 0.62, TOP, 1.24, 0.35, ['ITS loss?'], size=15, color=RED, bold=True, align=PP_ALIGN.CENTER)
    rows = [('Routing', 'which path a request takes'),
            ('Quality of service', 'who gets key first'),
            ('Exhaustion and fallback', 'what happens when key runs out'),
            ('Adversary models', 'depletion, attack radius')]
    for i, (name, desc) in enumerate(rows):
        y = TOP + 0.5 + i * 0.86
        rule(s, L, y - 0.08, c2 + 0.62, y - 0.08)
        text(s, L, y, 3.9, 0.4, [name], size=20, color=NAVY, bold=True)
        text(s, L, y + 0.4, 3.9, 0.35, [desc], size=15, color=MUTED)
        icon(s, 'FaCheck', NAVY, c1 - 0.2, y + 0.18, 0.4)
        icon(s, 'FaTimes', RED, c2 - 0.2, y + 0.18, 0.4)
    text(s, L, 6.05, 6.3, 0.8, [[('The missing column. ', {'bold': True, 'color': RED}),
                                  'No study we found reports how much traffic entitled to ITS key '
                                  'is served below ITS on a multi-hop network under attack.']], size=17)
    x0 = 7.75
    text(s, x0, TOP, R - x0, 0.45, ['What this paper adds'], size=22, color=NAVY, bold=True)
    items = [('A threat-aware model', ' where stored key outlives generation'),
             ('Forced assurance loss F', ' and the downgrade-forcing cost k*'),
             ('A cut condition', ' that bounds how long compliant service lasts'),
             ('Evidence on five graphs', ' that forcing needs capability, a cut and time'),
             ('An audit', ' of a learned controller, and accounting checked against published measurements')]
    for i, (lead, rest) in enumerate(items):
        y = TOP + 0.7 + i * 0.84
        dot(s, x0, y + 0.12, 0.13, RED)
        text(s, x0 + 0.3, y, R - x0 - 0.3, 0.8, [[(lead, {'bold': True, 'color': NAVY}), rest]], size=18)
    notes(s, "Here's the gap. Routing papers, quality-of-service papers, papers on key exhaustion "
             "and fallback, and papers that model an adversary all ask the same question: was the "
             "request served or blocked? That's the column of ticks. What no study we found reports is "
             "the highlighted column: how much entitled traffic lost its ITS protection. A "
             "post-quantum-only session simply counts as served. That's what we add: a model that "
             "keeps stored key and failure surfaces apart, two metrics for exactly this loss, a "
             "cut condition, evidence on five graphs, and an audit of our own method.")


# ---------------------------------------------------------------- slide 4
def slide_model(s, tmp):
    heading(s, 'System Model: Formation, Key Grades and Adversary')
    takeaway(s, f'Every session to the front crosses one of two 240{SP}bit/s links')
    png, ratio = figure(tmp, 'fig1_architecture', clip=(0, 9, 248.4, 90))
    w = 7.1
    s.shapes.add_picture(str(png), Inches(L), Inches(TOP + 0.05), width=Inches(w))
    text(s, L, TOP + 0.1 + w * ratio, w, 0.35,
         ['Paper Fig. 1(a). Orange crosses mark the two-link minimum cut.'], size=13, color=MUTED, italic=True)
    y3 = 5.25
    text(s, L, y3, w, 0.4, ['Three failure surfaces, kept separate'], size=18, color=NAVY, bold=True)
    surf = [('Quantum channel', f'QBER past 0.075 stops fresh key'),
            ('Classical transport', 'no relaying, no fallback'),
            ('Key service', 'no KEM fallback setup')]
    cw = (w - 0.4) / 3
    for i, (t, d) in enumerate(surf):
        x = L + i * (cw + 0.2)
        text(s, x, y3 + 0.48, cw, 1.1, [[(t, {'bold': True})], [(d, {'color': MUTED})]], size=16,
             space_after=2)
    x0 = 8.25
    wl = R - x0
    text(s, x0, TOP, wl, 0.45, ['The assurance ladder'], size=22, color=NAVY, bold=True)
    steps = [('1', 'One-time pad', 'ITS', NAVY, wl),
             ('2', 'QKD-keyed cipher', 'ITS key', NAVY2, wl - 0.3),
             ('3', 'QKD ⊕ ML-KEM', 'below ITS', RED2, wl - 0.6),
             ('4', 'ML-KEM only', 'post-quantum', RED, wl - 0.9)]
    for i, (n, desc, tag, c, wd) in enumerate(steps):
        y = TOP + 0.6 + i * 0.64
        rect(s, x0, y, wd, 0.54, c, radius=0.15)
        text(s, x0 + 0.15, y, 0.6, 0.54, [[('G', {'bold': True}), (n, {'sub': True, 'bold': True})]],
             size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x0 + 0.72, y, wd - 1.9, 0.54, [desc], size=16, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x0 + wd - 1.3, y, 1.18, 0.54, [tag], size=13, color=WHITE, bold=True,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x0, 5.18, wl, 0.4, [[('Floors  ', {'bold': True, 'color': NAVY}),
                                 'C2 → G', ('2', {'sub': True}), '   ISR → G', ('1', {'sub': True}),
                                 '   LOG → G', ('3', {'sub': True})]], size=17)
    rule(s, x0, 5.72, R, 5.72)
    icon(s, 'FaUserSecret', RED, x0, 5.9, 0.44)
    text(s, x0 + 0.65, 5.84, wl - 0.65, 1.0, [
        [('The attacker ', {'bold': True, 'color': RED}), 'raises the QBER on links it buys until they abort.'],
        ['Stored key survives, so it must outlast the stock.']], size=15, space_after=2)
    notes(s, "This is our main network, an eight-node tactical formation. Look at the orange "
             "crosses: every session from the rear base to the forward posts has to cross one of "
             "those two 240 bit-per-second links, and the fat fibre behind them can't help. We keep "
             "three failure surfaces apart: noise on the quantum channel stops fresh key, denial of "
             "classical transport stops relaying and any fallback, and denial of the key service blocks a KEM "
             "fallback. On the right is the assurance ladder, from one-time pad down to ML-KEM on "
             "its own; each traffic class has a floor it's entitled to. The attacker raises the "
             "error rate until links abort, but stored key can still be spent, so the attack has "
             "to last long enough to drain it.")


# ---------------------------------------------------------------- slide 5
def slide_metrics(s):
    heading(s, 'Metrics and Experimental Setup')
    takeaway(s, 'Availability hides the damage, so we measure the grade served')
    text(s, L, TOP, R - L, 0.35, [f'Fail-degraded, two-link cut held for 24{SP}h, 2% fill'], size=15, color=MUTED,
         bold=True)
    by, bh, bw = TOP + 0.85, 0.8, R - L
    segs = [(6.6, NAVY), (90.9, RED), (2.5, GREY)]
    x = L
    edges = []
    for v, c in segs:
        sw = bw * v / 100
        rect(s, x, by, sw, bh, c)
        edges.append((x, sw))
        x += sw
    text(s, L, by - 0.45, 2.6, 0.4, [[('6.6% ', {'bold': True, 'size': 20}), 'at grade']], size=16, color=NAVY)
    text(s, edges[1][0] + 1.0, by, edges[1][1] - 2.0, bh, [[('Served below its floor', {'bold': True})]], size=24,
         color=WHITE,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, R - 2.4, by - 0.45, 2.4, 0.4, [[('2.5% ', {'bold': True, 'size': 20}), 'not served']], size=16,
         color=MUTED, align=PP_ALIGN.RIGHT)
    ay = by + bh + 0.18
    end = edges[1][0] + edges[1][1]
    rule(s, L, ay, end, ay, color=MUTED, width=1.25)
    rule(s, L, ay - 0.1, L, ay, color=MUTED, width=1.25)
    rule(s, end, ay - 0.1, end, ay, color=MUTED, width=1.25)
    text(s, L, ay + 0.06, end - L, 0.35, ['97.5% counted as available'], size=16, color=MUTED,
         align=PP_ALIGN.CENTER)
    y = 4.55
    cw = (R - L - 0.8) / 3
    defs = [([('A = Q + L', {'color': NAVY})], 'Availability splits into service at its authorised '
                                                'grade (Q) and below it (L).'),
            ([('F', {'color': RED}), ('  forced assurance loss', {'size': 18, 'color': MUTED})],
             'Requests entitled to ITS key that are served below ITS. Blocked ones stay in the count.'),
            ([('T* = ΣU', {'color': NAVY}), ('e', {'color': NAVY, 'sub': True}), ('(0) / D̄', {'color': NAVY})],
             f'The longest compliant service can last under a held cut: 1.44{SP}h at 2% fill.')]
    for i, (f, d) in enumerate(defs):
        x = L + i * (cw + 0.4)
        if i:
            rule(s, x - 0.2, y + 0.05, x - 0.2, y + 1.55)
        text(s, x, y, cw, 0.5, [f], size=26, bold=True)
        text(s, x, y + 0.6, cw, 1.0, [d], size=16)
    rule(s, L, 6.35, R, 6.35)
    text(s, L, 6.45, R - L, 0.4, [f'Tested with 24{SP}h attacks, 12 paired seeds and 95% bootstrap intervals, '
                                  'behind a 43-check gate and 127 regression tests.'], size=16, color=MUTED)
    notes(s, "Why new metrics? Because availability on its own hides the problem. This bar is "
             "fail-degraded under the held cut. 97.5 percent of requests count as available, but "
             "only the navy sliver, 6.6 percent, is at the grade it was entitled to; the red block "
             "is served below its floor. So we split availability into Q and L. Our "
             "headline metric F counts requests entitled to ITS key that end up without it, keeping "
             "blocked requests in the count so both modes are compared fairly. And the cut condition "
             "gives a clock: stock behind the cut divided by demand bounds compliant service at 1.44 hours "
             "at two percent fill. "
             "Everything is tested over 24-hour attacks with twelve paired seeds and bootstrap "
             "intervals, behind a validation gate.")


# ---------------------------------------------------------------- slide 6
def doughnut(s, x, y, size, parts, hole=70):
    data = CategoryChartData()
    data.categories = [p[0] for p in parts]
    data.add_series('share', [p[1] for p in parts])
    gf = s.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(x), Inches(y), Inches(size), Inches(size), data)
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    chart_fonts(ch)
    plot = ch.plots[0]
    plot.has_data_labels = False
    for i, (_, _, c) in enumerate(parts):
        pt = plot.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c
        pt.format.line.color.rgb = WHITE
        pt.format.line.width = Pt(2)
    ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
    dn = ch._chartSpace.find('.//c:doughnutChart', ns)
    h = dn.find('c:holeSize', ns)
    if h is None:
        h = etree.SubElement(dn, '{%s}holeSize' % ns['c'])
    h.set('val', str(hole))
    return gf


def slide_result(s):
    heading(s, 'Key Result: The Fail-Mode Exchange Rate')
    takeaway(s, 'Same attack: refuse nearly everything, or serve it below grade')
    d = 2.95
    rings = [(L + 0.1, NAVY, 'Fail closed', '6.7%', 'served', 'Refuses the rest: a visible outage',
              [('At grade', 6.7, NAVY), ('Refused', 93.3, GREY)]),
             (L + 3.65, RED, 'Fail degraded', '97.5%', 'served', 'Only 6.6% at its grade',
              [('At grade', 6.6, NAVY), ('Below floor', 90.9, RED), ('Refused', 2.5, GREY)])]
    for x, c, title, big, small, line_, parts in rings:
        text(s, x, TOP, d, 0.45, [title], size=22, color=c, bold=True, align=PP_ALIGN.CENTER)
        doughnut(s, x, TOP + 0.5, d, parts)
        text(s, x, TOP + 0.5 + d / 2 - 0.42, d, 0.55, [big], size=30, color=c, bold=True, align=PP_ALIGN.CENTER)
        text(s, x, TOP + 0.5 + d / 2 + 0.12, d, 0.35, [small], size=15, color=MUTED, align=PP_ALIGN.CENTER)
        text(s, x - 0.2, TOP + 0.6 + d, d + 0.4, 0.4, [line_], size=16, color=INK, bold=True,
             align=PP_ALIGN.CENTER)
    ly = 6.2
    for i, (lab, c) in enumerate([('at authorised grade', NAVY), ('below floor (all classes)', RED), ('refused', GREY)]):
        lx = L + 0.1 + (0, 2.3, 5.0)[i]
        rect(s, lx, ly + 0.07, 0.22, 0.22, c)
        text(s, lx + 0.32, ly, 2.4, 0.36, [lab], size=14, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
    x0 = 8.05
    rule(s, x0 - 0.35, TOP, x0 - 0.35, 6.8)
    stats = [('90.1%', 60, RED, 'of requests entitled to ITS key are served without it (95% CI 89.2–91.0, 12 seeds)'),
             ('93.2%', 34, RED, f'of served sessions run on ML{NB}KEM{NB}768 alone'),
             ('87.6–92.9%', 34, NAVY, 'forced loss on all five graphs when the cut is held')]
    y = TOP - 0.1
    for i, (big, size, c, desc) in enumerate(stats):
        hb = 1.0 if size == 60 else 0.62
        text(s, x0, y, R - x0, hb, [big], size=size, color=c, bold=True)
        text(s, x0, y + hb, R - x0, 0.7, [desc], size=17, color=INK)
        y += hb + 0.95 if i == 0 else hb + 0.85
    notes(s, "This is the result to take home. Same attack, same graph, two fail modes. On the "
             "left, fail closed: the network refuses almost everything and serves 6.7 percent, a "
             "clear and visible outage. In the middle, fail degraded: it serves 97.5 percent, so "
             "availability looks fine, but look at the ring. Only 6.6 percent is at its proper "
             "grade; the red is service below the floor. That's 90.1 percent of entitled requests "
             "losing ITS protection, and 93 percent of served sessions running on ML-KEM alone. "
             "The fallback doesn't buy assurance back; it hides the loss. And it's not one graph: "
             "on all five, a held cut forces 88 to 93 percent.")


# ---------------------------------------------------------------- slide 7
def depth_chart(s, x, y, w, h):
    data = CategoryChartData()
    data.categories = ['1', '2', '3', '4', '5', '6']
    data.add_series('Static ranking', (1, 4, 5, 6, 7, 8))
    data.add_series('Residual betweenness or minimum cut', (1, 2, 2, 2, 2, 2))
    gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), data)
    ch = gf.chart
    chart_fonts(ch, 14)
    ch.has_title = False
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(14)
    for ser, c, marker in zip(ch.plots[0].series, (NAVY, RED), (XL_MARKER_STYLE.CIRCLE, XL_MARKER_STYLE.DIAMOND)):
        ser.format.line.color.rgb = c
        ser.format.line.width = Pt(3)
        ser.smooth = False
        ser.marker.style = marker
        ser.marker.size = 10
        ser.marker.format.fill.solid()
        ser.marker.format.fill.fore_color.rgb = c
        ser.marker.format.line.color.rgb = c
    va, ca = ch.value_axis, ch.category_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = 0, 9, 3
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RULE
    va.format.line.fill.background()
    va.has_title = True
    va.axis_title.text_frame.text = 'Links to attack, k*'
    ca.has_title = True
    ca.axis_title.text_frame.text = 'Relay-chain depth (hops)'
    ca.format.line.color.rgb = RULE
    for ax in (va, ca):
        ax.tick_labels.font.size = Pt(14)
        ax.tick_labels.font.color.rgb = MUTED
        for p in ax.axis_title.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(14)
                r.font.bold = False
                r.font.color.rgb = MUTED
                r.font.name = FONT
    return gf


def slide_forcing(s):
    heading(s, 'What Forcing Requires: Capability, Cut and Endurance')
    takeaway(s, 'Forcing needs capability, a cut and time. Remove one, it fails')
    text(s, L, TOP, 7.4, 0.4, [[('k*', {'bold': True}), ': links an attacker must buy to force F ≥ 50% in '
                               f'24{SP}h (fail-degraded, 2% fill, 8 seeds)']], size=14, color=MUTED)
    depth_chart(s, L - 0.1, TOP + 0.4, 7.45, 4.5)
    x0 = 8.4
    rule(s, x0 - 0.35, TOP, x0 - 0.35, 6.8)
    blocks = [('FaBolt', 'Capability', [['A link aborts only once ', (f'Δe{SP}≥{SP}0.045', {'bold': True}),
                                         f'; below that (γ{SP}={SP}1), under 0.1% is forced.']]),
              ('FaCut', 'A cut', [['A smart attacker needs only the ', (f'2{NB}link cut', {'bold': True}),
                                   ', however deep the chain.']]),
              ('FaHourglassHalf', 'Time', [['First forcing after ', (f'about 1.5{SP}h', {'bold': True}),
                                            f' at 2% fill; from full stores, nothing in 24{SP}h.']])]
    for i, (ic, title, body) in enumerate(blocks):
        y = TOP + i * 1.38
        if i:
            rule(s, x0, y - 0.13, R, y - 0.13)
        icon(s, ic, RED, x0, y + 0.04, 0.42)
        text(s, x0 + 0.62, y, R - x0 - 0.62, 0.5, [title], size=22, color=NAVY, bold=True,
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, x0, y + 0.55, R - x0, 0.75, body, size=16)
    rule(s, x0, 6.02, R, 6.02)
    text(s, x0, 6.1, R - x0, 0.75, ['Routing adds 0.12 points of Q; floors cut F to 63.6% by denying '
                                    'logistics key; a learned controller gains little and raises payload '
                                    'exposure.'], size=14, color=MUTED)
    notes(s, "So what does it take to force a downgrade? Three things, and the attacker needs all "
             "of them. Capability: a link only aborts once the injected error passes 0.045; below "
             "that, with the standard BB84 response, almost nothing is forced. A cut: look at the chart. A naive static ranking, the "
             "navy line, makes a longer chain look safer, needing d plus two links. A smart attacker "
             "who recomputes after each removal, the red line, needs only the two-link cut at every "
             "depth. Depth buys no protection. And time: the attack has to outlast the stored key. "
             "First forcing comes after about an hour and a half, and from full stores nothing is "
             "forced all day. We also measured key-aware routing, reservation floors and a learned "
             "controller; their effects are summarised at the bottom right.")


# ---------------------------------------------------------------- slide 8
def slide_conclusion(s):
    heading(s, 'Conclusions and Recommendations for Operators')
    takeaway(s, 'Report the grade of what you serve, not only that you served it')
    x0, w0 = L, 6.55
    text(s, x0, TOP, w0, 0.45, ['Three rules for operators'], size=22, color=NAVY, bold=True)
    rules = [[('Report Q and F', {'bold': True, 'color': NAVY}), ' next to availability A.'],
             [('Keep stock behind the minimum cut', {'bold': True, 'color': NAVY}),
              ' for T* hours of the attacks you fear.'],
             [('Set fail modes per traffic class', {'bold': True, 'color': NAVY}),
              ', and put a price on every exception.']]
    for i, r in enumerate(rules):
        y = TOP + 0.7 + (0, 0.72, 1.72)[i]
        dot(s, x0, y + 0.13, 0.14, RED)
        text(s, x0 + 0.35, y, w0 - 0.35, 0.85, [r], size=20)
    rule(s, x0, 5.55, x0 + w0, 5.55)
    text(s, x0, 5.7, w0, 1.1, [[('Open and reproducible. ', {'bold': True, 'color': NAVY}),
                                 'Every number comes from the released simulator, configurations '
                                 'and per-seed results.']], size=16, color=MUTED)
    px = 7.45
    rect(s, px, TOP, R - px, 6.85 - TOP, NAVY, radius=0.04, name='Thank you panel')
    text(s, px + 0.5, TOP + 0.55, R - px - 1.0, 0.9, ['Thank you'], size=44, color=WHITE, bold=True)
    text(s, px + 0.5, TOP + 1.5, R - px - 1.0, 0.45, ['Questions are welcome'], size=22, color=WHITE)
    contacts = [('FaEnvelope', '10jainlakshya@gmail.com'), ('FaEnvelope', 'Sid.arora1701@gmail.com'),
                ('FaGithub', 'github.com/LakshyaJ1/Quantum_ResearchPaper')]
    for i, (ic, t) in enumerate(contacts):
        y = TOP + 2.55 + i * 0.52
        icon(s, ic, WHITE, px + 0.5, y + 0.06, 0.28)
        text(s, px + 0.95, y, R - px - 1.1, 0.42, [t], size=14, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Let me wrap up. Refusing service costs availability; degrading quietly costs "
             "assurance, and under a held cut that's ninety percent of entitled traffic. An attacker "
             "can only force it with capability, a cut and enough time, so stock behind the cut is a "
             "real defence. If you remember one thing: report the grade of what you serve, not only "
             "that you served it. For operators that means three rules: report Q and F next to "
             "availability, keep stock behind the minimum cut for the attacks you fear, and set fail "
             "modes per traffic class. Every number in this talk comes from our released simulator and "
             "per-seed results. Thank you, and I'm happy to take questions.")


# ---------------------------------------------------------------- build
def main():
    if ADD_SLIDE is None:
        raise SystemExit('usage: build_presentation.py <path to pptx skill scripts/add_slide.py>')
    OUT_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        work = tmp / 'unpacked'
        zipfile.ZipFile(TEMPLATE).extractall(work)
        for _ in range(6):              # identical copies, so their order does not matter
            subprocess.run([sys.executable, str(ADD_SLIDE), str(work), 'slide2.xml', '--after', 'slide2.xml'],
                           capture_output=True, text=True, check=True)
        packed = tmp / 'base.pptx'
        with zipfile.ZipFile(packed, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(work.rglob('*')):
                if f.is_file():
                    z.write(f, f.relative_to(work).as_posix())
        prs = Presentation(packed)
        slides = list(prs.slides)
        assert len(slides) == 8, len(slides)
        slide_title(slides[0])
        slide_motivation(slides[1])
        slide_gap(slides[2])
        slide_model(slides[3], tmp)
        slide_metrics(slides[4])
        slide_result(slides[5])
        slide_forcing(slides[6])
        slide_conclusion(slides[7])
        prs.core_properties.title = 'Fail-Closed or Fail-Degraded? (WiCOMM-2026, paper 167)'
        prs.core_properties.author = 'Lakshya Jain, Siddhi Arora'
        prs.save(OUT)
    print(OUT)


if __name__ == '__main__':
    main()
