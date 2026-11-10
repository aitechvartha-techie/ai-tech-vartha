#!/usr/bin/env python3
"""Build a resume from a JSON file into a designed PDF (and an editable DOCX copy).

Usage:
  python build_resume.py resume.json [--out NAME] [--docx] [--template clean] [--pages 1]
                         [--page A4|Letter] [--accent "#2D5BFF"] [--margins narrow|normal|wide] [--preset fresher]
                         [--photo photo.jpg]

Templates
  ATS-safe (single column, best for job portals and company career sites):
    clean      Poppins name, accent bars on headings, skill tags
    elegant    large serif name, thin accent rule, small-caps headings, lots of white space
    compact    dense one-pager for long careers
  Designer (best when a person reads it: email, WhatsApp, referral, printed walk-in):
    sidebar    coloured left column: photo or initials, contact with icons, skills, languages
    timeline   dates down a line with dots, career reads like a story
    monogram   initials badge, tinted header, chips

All text stays real, selectable text. If content doesn't fit the page limit, spacing and size are tightened down to a
readable minimum; if it still doesn't fit, the script exits with code 3 so the content can be shortened.
"""
import argparse, json, os, re, sys, zipfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, FrameBreak, KeepTogether, NextPageTemplate,
                                PageTemplate, Paragraph, Spacer, TableStyle)
from reportlab.platypus import Table as _Table


def Table(*a, **k):   # left-aligned by default, so rows sized for page 1 don't centre on a wider page 2
    k.setdefault("hAlign", "LEFT")
    return _Table(*a, **k)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")

TEMPLATES = {
    "clean":    dict(kind="ats", name="display", head="bar", skills="chips", entry="stack", header="plain", size=9.6),
    "elegant":  dict(kind="ats", name="serif", head="smallcaps", skills="rows", entry="stack", header="centered", size=9.8),
    "compact":  dict(kind="ats", name="display", head="line", skills="rows", entry="stack", header="plain", size=8.9),
    "sidebar":  dict(kind="designer", name="display", head="short", skills="chips", entry="stack", header="sidebar", size=9.3),
    "timeline": dict(kind="designer", name="display", head="bar", skills="chips", entry="timeline", header="tint", size=9.4),
    "monogram": dict(kind="designer", name="display", head="short", skills="chips", entry="stack", header="monogram", size=9.5),
}
CUSTOM_KEYS = {   # "style": {"custom": {...}} mixes any template's parts into your own design
    "header": ("plain", "centered", "tint", "monogram", "sidebar"),
    "head": ("bar", "line", "short", "smallcaps"),
    "skills": ("chips", "rows"),
    "entry": ("stack", "timeline"),
    "name": ("display", "serif"),
    "strip": (True, False),
}


def resolve(st):
    t = dict(TEMPLATES[st["template"]])
    t.setdefault("strip", st["template"] == "clean")
    for k, v in (st.get("custom") or {}).items():
        if k in CUSTOM_KEYS and v in CUSTOM_KEYS[k]:
            t[k] = v
        elif k in CUSTOM_KEYS:
            print(f"custom {k}={v!r} ignored; choose from {CUSTOM_KEYS[k]}")
    if st.get("custom"):   # a custom mix is ATS-safe only if it stays one plain column
        t["kind"] = "designer" if t["header"] in ("sidebar", "monogram", "tint") or t["entry"] == "timeline" else "ats"
    return t


ALIASES = {"modern": "clean", "classic": "elegant", "minimal": "elegant", "banner": "monogram"}
ORDERS = {
    "experienced": ["summary", "experience", "projects", "skills", "education", "certifications", "achievements",
                    "volunteering", "languages", "extra", "personal"],
    "fresher": ["summary", "education", "projects", "experience", "skills", "certifications", "achievements",
                "volunteering", "languages", "extra", "personal"],
}
SIDEBAR_KEYS = ["skills", "languages", "certifications", "personal"]
TITLES = {"summary": "Profile", "experience": "Experience", "projects": "Projects", "skills": "Skills",
          "education": "Education", "certifications": "Certifications", "achievements": "Achievements",
          "volunteering": "Volunteering", "languages": "Languages", "personal": "Details", "contact": "Contact"}
MARGINS = {"narrow": 12, "normal": 15, "wide": 19}
MIN_SIZE = 8.3
INK, MUTE, LINE = colors.HexColor("#1B1F24"), colors.HexColor("#5B6470"), colors.HexColor("#D9DEE4")
F = {}


# ---------------------------------------------------------------- fonts
def register_fonts():
    def reg(alias, files, fb):
        p = {k: os.path.join(FONTS, v) for k, v in files.items()}
        if all(os.path.exists(x) for x in p.values()):
            for k, x in p.items():
                pdfmetrics.registerFont(TTFont(f"{alias}-{k}", x))
            pdfmetrics.registerFontFamily(alias, normal=f"{alias}-r", bold=f"{alias}-b", italic=f"{alias}-i",
                                          boldItalic=f"{alias}-b")
            return {k: f"{alias}-{k}" for k in p}
        return fb
    lib_s = {"r": "LiberationSans-Regular.ttf", "b": "LiberationSans-Bold.ttf", "sb": "LiberationSans-Bold.ttf",
             "i": "LiberationSans-Italic.ttf"}
    fb_sans = reg("LibSans", lib_s, {"r": "Helvetica", "b": "Helvetica-Bold", "sb": "Helvetica-Bold", "i": "Helvetica-Oblique"})
    F["body"] = reg("Inter", {"r": "Inter-400.ttf", "b": "Inter-700.ttf", "sb": "Inter-600.ttf", "i": "Inter-400i.ttf"}, fb_sans)
    F["display"] = reg("Poppins", {"r": "Poppins-500.ttf", "b": "Poppins-700.ttf", "sb": "Poppins-600.ttf",
                                   "i": "Poppins-500.ttf"}, fb_sans)
    F["serif"] = reg("Lora", {"r": "Lora-400.ttf", "b": "Lora-700.ttf", "sb": "Lora-600.ttf", "i": "Lora-400i.ttf"},
                     {"r": "Times-Roman", "b": "Times-Bold", "sb": "Times-Bold", "i": "Times-Italic"})


# ---------------------------------------------------------------- helpers
def hexcolor(s, default="#2D5BFF"):
    s = (s or default).strip()
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", s):
        s = default
    return colors.HexColor("#" + s.lstrip("#"))


def mix(c, other, t):
    return colors.Color(c.red + (other.red - c.red) * t, c.green + (other.green - c.green) * t,
                        c.blue + (other.blue - c.blue) * t)


def inline(text):
    t = escape(str(text))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", t)
    return t


def safe(text, font):
    """inline() plus a fallback to the body font for characters the display font doesn't have (→, ₹ …)."""
    try:
        cmap = pdfmetrics.getFont(font).face.charToGlyph
    except Exception:
        return inline(text)
    out = []
    for ch in str(text):
        if ch.strip() and ord(ch) not in cmap:
            out.append(f'<font name="{F["body"]["r"]}">{escape(ch)}</font>')
        else:
            out.append(escape(ch))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", "".join(out))


def daterange(a, b):
    a, b = (a or "").strip(), (b or "").strip()
    return f"{a} – {b}" if a and b else (a or b)


def initials(name):
    parts = [p for p in re.split(r"\s+", name or "") if p]
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper() if parts else "?"


# ---------------------------------------------------------------- flowables
class SectionHead(Flowable):
    def __init__(self, text, style, accent, font, size, color=INK, space_before=9, rule_color=LINE):
        super().__init__()
        self.text, self.style, self.accent, self.font, self.size = text, style, accent, font, size
        self.color, self.sb, self.rule_color = color, space_before, rule_color
    def wrap(self, aw, ah):
        self.aw = aw
        self.h = self.size * 1.25 + (5 if self.style in ("line", "short", "smallcaps") else 2)
        return aw, self.h
    def getSpaceBefore(self):
        return self.sb
    def getSpaceAfter(self):
        return 4
    def draw(self):
        c = self.canv; y = self.h - self.size * 1.0
        txt = self.text
        if self.style == "smallcaps":
            c.setFont(self.font, self.size * 0.86); c.setFillColor(self.color)
            t = c.beginText(0, y); t.setFont(self.font, self.size * 0.86); t.setCharSpace(self.size * 0.14)
            t.textOut(txt.upper()); c.drawText(t)
            c.setStrokeColor(self.accent); c.setLineWidth(0.9); c.line(0, 1.2, 22, 1.2)
            return
        if self.style == "bar":
            c.setFillColor(self.accent); c.roundRect(0, y - 1.2, 3.2, self.size * 1.05, 1.2, stroke=0, fill=1)
            c.setFont(self.font, self.size); c.setFillColor(self.color); c.drawString(9, y, txt)
            return
        c.setFont(self.font, self.size); c.setFillColor(self.color); c.drawString(0, y, txt)
        if self.style == "line":
            c.setStrokeColor(self.rule_color); c.setLineWidth(0.7); c.line(0, 1.5, self.aw, 1.5)
        elif self.style == "short":
            c.setStrokeColor(self.accent); c.setLineWidth(2.2); c.line(0, 1.5, 18, 1.5)


class Chips(Flowable):
    def __init__(self, items, font, size, fill, text, pad=4.2, gap=4):
        super().__init__()
        self.items = [str(i) for i in items if str(i).strip()]
        self.font, self.size, self.fill, self.textc, self.pad, self.gap = font, size, fill, text, pad, gap
    def wrap(self, aw, ah):
        rows, x, row = [], 0, []
        self.ch = self.size + 2 * self.pad * 0.62
        items = []
        for it in self.items:   # an item wider than the column is split into word groups that fit
            if pdfmetrics.stringWidth(it, self.font, self.size) + 2 * self.pad <= aw:
                items.append(it); continue
            cur = ""
            for wd in it.split():
                tryw = (cur + " " + wd).strip()
                if cur and pdfmetrics.stringWidth(tryw, self.font, self.size) + 2 * self.pad > aw:
                    items.append(cur); cur = wd
                else:
                    cur = tryw
            if cur: items.append(cur)
        for it in items:
            w = min(pdfmetrics.stringWidth(it, self.font, self.size) + 2 * self.pad, aw)
            if row and x + w > aw:
                rows.append(row); row, x = [], 0
            row.append((it, x, w)); x += w + self.gap
        if row: rows.append(row)
        self.rows = rows
        self.h = len(rows) * (self.ch + self.gap) - (self.gap if rows else 0)
        return aw, self.h
    def draw(self):
        c = self.canv
        for r, row in enumerate(self.rows):
            y = self.h - (r + 1) * self.ch - r * self.gap
            for it, x, w in row:
                c.setFillColor(self.fill); c.roundRect(x, y, w, self.ch, self.ch / 2, stroke=0, fill=1)
                c.setFillColor(self.textc); c.setFont(self.font, self.size)
                c.drawString(x + self.pad, y + self.pad * 0.62 + self.size * 0.2, it)


class Icon(Flowable):
    """Small vector icons for the contact block."""
    def __init__(self, kind, color, bg, d=11):
        super().__init__(); self.kind, self.color, self.bg, self.d = kind, color, bg, d
    def wrap(self, aw, ah):
        return self.d, self.d
    def draw(self):
        c, d, k = self.canv, self.d, self.kind
        c.setFillColor(self.bg); c.circle(d / 2, d / 2, d / 2, stroke=0, fill=1)
        c.setStrokeColor(self.color); c.setFillColor(self.color); c.setLineWidth(0.8)
        m = d / 2; s = d / 11.0
        if k == "phone":
            c.roundRect(m - 2 * s, m - 3.2 * s, 4 * s, 6.4 * s, 0.9 * s, stroke=1, fill=0); c.line(m - 0.7 * s, m - 2.3 * s, m + 0.7 * s, m - 2.3 * s)
        elif k == "email":
            c.rect(m - 3.2 * s, m - 2.2 * s, 6.4 * s, 4.4 * s, stroke=1, fill=0)
            p = c.beginPath(); p.moveTo(m - 3.2 * s, m + 2.2 * s); p.lineTo(m, m - 0.3 * s); p.lineTo(m + 3.2 * s, m + 2.2 * s); c.drawPath(p, stroke=1, fill=0)
        elif k == "location":
            c.circle(m, m + 0.9 * s, 2.1 * s, stroke=1, fill=0)
            p = c.beginPath(); p.moveTo(m - 1.9 * s, m + 0.1 * s); p.lineTo(m, m - 3.2 * s); p.lineTo(m + 1.9 * s, m + 0.1 * s); c.drawPath(p, stroke=1, fill=0)
        elif k in ("linkedin", "github", "website"):
            c.circle(m, m, 3.1 * s, stroke=1, fill=0); c.line(m - 3.1 * s, m, m + 3.1 * s, m)
            c.ellipse(m - 1.3 * s, m - 3.1 * s, m + 1.3 * s, m + 3.1 * s, stroke=1, fill=0)
        else:
            c.circle(m, m, 1.2 * s, stroke=0, fill=1)


class ContactFlow(Flowable):
    """Icon + text items laid out inline, wrapping to new lines as needed."""
    def __init__(self, items, font, size, color, icon_color, icon_bg, gap=14, d=10):
        super().__init__()
        self.items, self.font, self.size, self.color = items, font, size, color
        self.ic, self.ib, self.gap, self.d = icon_color, icon_bg, gap, d
    def wrap(self, aw, ah):
        self.rows, row, x = [], [], 0
        for k, v in self.items:
            w = self.d + 4 + pdfmetrics.stringWidth(v, self.font, self.size)
            if row and x + w > aw:
                self.rows.append(row); row, x = [], 0
            row.append((k, v, x)); x += w + self.gap
        if row: self.rows.append(row)
        self.lh = max(self.d, self.size * 1.3) + 4
        self.h = len(self.rows) * self.lh
        return aw, self.h
    def draw(self):
        c = self.canv
        for r, row in enumerate(self.rows):
            y = self.h - (r + 1) * self.lh + 2
            for k, v, x in row:
                c.saveState(); c.translate(x, y); Icon(k, self.ic, self.ib, d=self.d).drawOn(c, 0, 0); c.restoreState()
                c.setFillColor(self.color); c.setFont(self.font, self.size)
                c.drawString(x + self.d + 4, y + self.d / 2 - self.size * 0.35, v)


class Badge(Flowable):
    """Round photo, or initials in a circle."""
    def __init__(self, d, fill, text_color, text, font, photo=None, ring=None):
        super().__init__(); self.d, self.fill, self.tc, self.text, self.font, self.photo, self.ring = d, fill, text_color, text, font, photo, ring
    def wrap(self, aw, ah):
        return self.d + 4, self.d + 4
    def draw(self):
        c, d = self.canv, self.d; cx, cy = d / 2 + 2, d / 2 + 2
        if self.photo:
            c.saveState(); p = c.beginPath(); p.circle(cx, cy, d / 2); c.clipPath(p, stroke=0, fill=0)
            img = ImageReader(self.photo); iw, ih = img.getSize(); sc = max(d / iw, d / ih)
            c.drawImage(img, cx - iw * sc / 2, cy - ih * sc / 2, iw * sc, ih * sc, mask="auto"); c.restoreState()
        else:
            c.setFillColor(self.fill); c.circle(cx, cy, d / 2, stroke=0, fill=1)
            c.setFillColor(self.tc); c.setFont(self.font, d * 0.38)
            c.drawCentredString(cx, cy - d * 0.135, self.text)
        if self.ring:
            c.setStrokeColor(self.ring); c.setLineWidth(1.4); c.circle(cx, cy, d / 2 + 1.5, stroke=1, fill=0)


class Dot(Flowable):
    """Timeline dot drawn on the column's left edge (the line itself is a table border)."""
    def __init__(self, color, x, r=2.7):
        super().__init__(); self.color, self.x, self.r = color, x, r
    def wrap(self, aw, ah):
        return 0, 0
    def draw(self):
        c = self.canv; c.setFillColor(colors.white); c.setStrokeColor(self.color); c.setLineWidth(1.5)
        c.circle(self.x, -4.6, self.r, stroke=1, fill=1)


class LanguageDots(Flowable):
    def __init__(self, items, font, size, color, dim, text):
        super().__init__(); self.items, self.font, self.size, self.color, self.dim, self.text = items, font, size, color, dim, text
    def wrap(self, aw, ah):
        self.aw = aw; self.h = len(self.items) * self.size * 1.8; return aw, self.h
    def draw(self):
        c = self.canv
        for i, (name, lvl) in enumerate(self.items):
            y = self.h - (i + 1) * self.size * 1.8 + self.size * 0.5
            c.setFillColor(self.text); c.setFont(self.font, self.size); c.drawString(0, y, name)
            for k in range(5):
                c.setFillColor(self.color if k < lvl else self.dim)
                c.circle(self.aw - 3 - (4 - k) * 8, y + self.size * 0.33, 2.4, stroke=0, fill=1)


LEVELS = {"native": 5, "mother tongue": 5, "fluent": 5, "professional": 4, "advanced": 4, "good": 4,
          "intermediate": 3, "conversational": 3, "spoken": 3, "basic": 2, "beginner": 1}


def parse_lang(x):
    if isinstance(x, dict):
        return x.get("name", ""), int(x.get("level", 4))
    m = re.match(r"\s*(.+?)\s*\((.+?)\)\s*$", str(x))
    if m:
        return m.group(1), LEVELS.get(m.group(2).lower(), 3)
    return str(x), 5


# ---------------------------------------------------------------- story pieces
def styles(t, base, sp, accent, on_dark=False):
    body = F["body"]; disp = F["serif"] if t["name"] == "serif" else F["display"]
    ink = colors.white if on_dark else INK
    mute = mix(colors.white, accent, 0.22) if on_dark else MUTE
    lead = base * 1.42
    S = {
        "body": ParagraphStyle("body", fontName=body["r"], fontSize=base, leading=lead, textColor=ink),
        "bul": ParagraphStyle("bul", fontName=body["r"], fontSize=base, leading=lead, textColor=ink,
                              leftIndent=base * 1.05, bulletIndent=base * 0.1, spaceAfter=1.4 * sp, bulletFontName=body["b"],
                              bulletColor=accent if not on_dark else colors.white),
        "role": ParagraphStyle("role", fontName=body["sb"], fontSize=base * 1.07, leading=base * 1.4, textColor=ink),
        "org": ParagraphStyle("org", fontName=body["r"], fontSize=base * 0.97, leading=base * 1.35, textColor=accent if not on_dark else mute),
        "date": ParagraphStyle("date", fontName=body["r"], fontSize=base * 0.9, leading=base * 1.4, textColor=mute, alignment=TA_RIGHT),
        "tdate": ParagraphStyle("tdate", fontName=body["sb"], fontSize=base * 0.86, leading=base * 1.3, textColor=mute),
        "small": ParagraphStyle("small", fontName=body["r"], fontSize=base * 0.92, leading=base * 1.35, textColor=mute),
        "name": ParagraphStyle("name", fontName=disp["b"] if t["name"] != "serif" else disp["sb"], fontSize=base * 2.75,
                               leading=base * 3.25, textColor=ink, spaceAfter=base * 0.25),
        "headline": ParagraphStyle("headline", fontName=F["display"]["r"] if t["name"] != "serif" else body["r"],
                                   fontSize=base * 1.2, leading=base * 1.55, textColor=accent if not on_dark else mute),
        "contact": ParagraphStyle("contact", fontName=body["r"], fontSize=base * 0.9, leading=base * 1.4, textColor=mute),
    }
    S["headfont"] = disp["sb"] if t["name"] != "serif" else body["sb"]
    return S


def section_head(key, t, st, S, accent, base, sp, dark=False):
    txt = (st.get("titles", {}) or {}).get(key) or TITLES.get(key, key.title())
    return SectionHead(txt, t["head"], accent if not dark else colors.white, S["headfont"],
                       base * (1.18 if t["head"] != "smallcaps" else 1.15),
                       color=colors.white if dark else INK, space_before=(8 if st["template"] != "compact" else 6) * sp)


def contact_items(d):
    c = d.get("contact", {}) or {}
    out = [(k, c[k]) for k in ("phone", "email", "location", "linkedin", "github", "website") if c.get(k)]
    out += [("other", x) for x in c.get("other", []) if x]
    return out


def entry_blocks(kind, e, t, S, accent, width, sp, base):
    if kind == "experience":
        title, sub, where, dates, items, link = e.get("role", ""), e.get("org", ""), e.get("location", ""), daterange(e.get("start"), e.get("end")), e.get("bullets"), None
    elif kind == "projects":
        title, sub, where, dates, items, link = e.get("name", ""), e.get("context", ""), "", e.get("date", ""), e.get("bullets"), e.get("link")
    else:
        title = e.get("degree", ""); sub = " · ".join(x for x in (e.get("school", ""), e.get("score", "")) if x)
        where, dates, items, link = e.get("location", ""), daterange(e.get("start"), e.get("end")), e.get("details"), None
    subline = " · ".join(x for x in (sub, where) if x)
    bl = [Paragraph(inline(b), S["bul"], bulletText="•") for b in items or [] if str(b).strip()]
    head_txt = inline(title) + (f'  <font color="#5B6470" size="{base*0.86:.1f}">{inline(link)}</font>' if link else "")
    if t["entry"] == "timeline":
        dw = 25 * mm
        inner = [Dot(accent, -13.0), Paragraph(head_txt, S["role"])]
        if subline: inner.append(Paragraph(inline(subline), S["org"]))
        inner.append(Spacer(1, 1.5 * sp)); inner += bl
        tb = Table([[Paragraph(inline(dates), S["tdate"]), inner]], colWidths=[dw, "*"])
        tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0),
                                ("LEFTPADDING", (1, 0), (1, 0), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 7 * sp),
                                ("LINEBEFORE", (1, 0), (1, 0), 1.0, mix(accent, colors.white, 0.6))]))
        return [tb]
    top = Table([[Paragraph(head_txt, S["role"]), Paragraph(inline(dates), S["date"])]], colWidths=["74%", "26%"])
    top.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                             ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    blk = [top]
    if subline: blk.append(Paragraph(inline(subline), S["org"]))
    blk.append(Spacer(1, 1.6 * sp))
    return [KeepTogether(blk + bl[:2])] + bl[2:] + [Spacer(1, 5.5 * sp)]


def body_section(key, d, t, st, S, accent, width, sp, base, dark=False):
    v = d.get(key)
    out = []
    if key == "extra":
        for sec in d.get("extra", []) or []:
            out.append(SectionHead(sec.get("title", "More"), t["head"], accent, S["headfont"], base * 1.18))
            out += [Paragraph(inline(b), S["bul"], bulletText="•") for b in sec.get("items", [])]
        return out
    if not v:
        return out
    out.append(section_head(key, t, st, S, accent, base, sp, dark))
    if key == "summary":
        out.append(Paragraph(inline(v), S["body"]))
    elif key in ("experience", "projects", "education"):
        for e in v:
            out += entry_blocks(key, e, t, S, accent, width, sp, base)
    elif key == "skills":
        groups = v if (isinstance(v, list) and v and isinstance(v[0], dict)) else [{"group": "", "items": v}]
        if t["skills"] == "chips":
            for g in groups:
                if g.get("group"):
                    out.append(Paragraph(inline(g["group"]), ParagraphStyle("sg", parent=S["small"], fontName=F["body"]["sb"],
                                         textColor=colors.white if dark else MUTE, spaceBefore=2 * sp, spaceAfter=2.5)))
                fill = mix(accent, colors.white, 0.86) if not dark else mix(accent, colors.white, 0.2)
                out.append(Chips(g.get("items", []), F["body"]["r"], base * 0.88, fill, INK if not dark else colors.white))
                out.append(Spacer(1, 2.5 * sp))
        else:
            rows = [[Paragraph(f"<b>{inline(g.get('group',''))}</b>", S["body"]), Paragraph(inline(", ".join(g.get("items", []))), S["body"])] for g in groups]
            tb = Table(rows, colWidths=["22%", "78%"])
            tb.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                    ("TOPPADDING", (0, 0), (-1, -1), 0.6 * sp), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0 * sp),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            out.append(tb)
    elif key == "certifications":
        for cert in v:
            if isinstance(cert, str):
                out.append(Paragraph(inline(cert), S["bul"], bulletText="•")); continue
            txt = f"<b>{inline(cert.get('name',''))}</b>"
            meta = " · ".join(x for x in (cert.get("issuer", ""), cert.get("date", "")) if x)
            if dark:
                out.append(Paragraph(txt, S["body"]))
                if meta: out.append(Paragraph(inline(meta), S["small"]))
                out.append(Spacer(1, 3 * sp))
            else:
                out.append(Paragraph(txt + (f'  <font color="#5B6470">{inline(meta)}</font>' if meta else ""), S["bul"], bulletText="•"))
    elif key in ("achievements", "volunteering"):
        out += [Paragraph(inline(b), S["bul"], bulletText="•") for b in (v if isinstance(v, list) else [v])]
    elif key == "languages":
        items = [parse_lang(x) for x in (v if isinstance(v, list) else [v])]
        if dark:
            out.append(LanguageDots(items, F["body"]["r"], base * 0.95, colors.white, mix(accent, colors.white, 0.35), colors.white))
        else:
            out.append(Paragraph(" · ".join(inline(n) for n, _ in items), S["body"]))
    elif key == "personal":
        if dark:
            for k, x in v.items():
                out.append(Paragraph(f"<b>{inline(k)}</b>", S["small"])); out.append(Paragraph(inline(x), S["body"])); out.append(Spacer(1, 2 * sp))
        else:
            out.append(Paragraph("  ·  ".join(f"<b>{inline(k)}:</b> {inline(x)}" for k, x in v.items()), S["body"]))
    return out


def tight(tb):
    tb.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return tb


def header_block(d, t, st, S, accent, width, base, sp):
    name, head = d.get("name", ""), d.get("headline", "")
    contacts = contact_items(d)
    photo = st.get("photo") if st.get("photo") and os.path.exists(st.get("photo")) else None
    out = []
    if t["header"] == "centered":
        for k in ("name", "headline", "contact"):
            S[k].alignment = TA_CENTER
        out.append(Paragraph(safe(name, S["name"].fontName), S["name"]))
        if head: out.append(Paragraph(safe(head, S["headline"].fontName), S["headline"]))
        out.append(Spacer(1, 3 * sp))
        out.append(Paragraph("   ·   ".join(inline(v) for _, v in contacts), S["contact"]))
        out.append(Spacer(1, 6 * sp))
        r = Table([[""]], colWidths=[40], rowHeights=[1.2]); r.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), accent)]))
        r.hAlign = "CENTER"; out.append(r); out.append(Spacer(1, 3 * sp))
        return out
    has_badge = t["header"] == "monogram" or photo
    bw = 23 * mm if has_badge else 0
    inner_w = width - (bw + 7 * mm if has_badge else 0)
    blocks = [Paragraph(safe(name, S["name"].fontName), S["name"])]
    if head: blocks.append(Paragraph(safe(head, S["headline"].fontName), S["headline"]))
    blocks.append(Spacer(1, 4 * sp))
    if contacts:
        blocks.append(ContactFlow([(k, str(v)) for k, v in contacts], F["body"]["r"], base * 0.9, MUTE, accent,
                                  mix(accent, colors.white, 0.84)))
    if has_badge:
        badge = Badge(bw - 4, accent, colors.white, initials(name), F["display"]["b"], photo=photo, ring=mix(accent, colors.white, 0.55))
        hdr = Table([[badge, blocks]], colWidths=[bw + 7 * mm, inner_w])
        out.append(tight(hdr))
    else:
        out += blocks
    out.append(Spacer(1, 3 * sp))
    return out


# ---------------------------------------------------------------- render
def build(d, st, out_pdf, scale):
    t = resolve(st)
    size = A4 if str(st.get("page", "A4")).upper() == "A4" else LETTER
    W, H = size
    m = MARGINS.get(st.get("margins", "normal"), 15) * mm
    accent = hexcolor(st.get("accent"))
    tint = mix(accent, colors.white, 0.92)
    base = st["size"] * scale; sp = scale
    pages = {"n": 0}
    order = st.get("order") or ORDERS.get(st.get("preset", "experienced"), ORDERS["experienced"])
    order = [k for k in order if k not in set(st.get("hide", []))]
    doc = BaseDocTemplate(out_pdf, pagesize=size, leftMargin=m, rightMargin=m, topMargin=m, bottomMargin=m * 0.9,
                          title=f"{d.get('name','')} – Resume", author=d.get("name", ""), subject=d.get("headline", "Resume"),
                          creator="resume-builder skill")

    def count(c, doc_):
        pages["n"] = doc_.page

    if t["header"] == "sidebar":
        sw = W * 0.335
        def bg(c, doc_):
            count(c, doc_); c.saveState(); c.setFillColor(accent); c.rect(0, 0, sw, H, stroke=0, fill=1); c.restoreState()
        def bg_later(c, doc_):   # page 2+: a thin colour strip instead of an empty sidebar
            count(c, doc_); c.saveState(); c.setFillColor(accent); c.rect(0, 0, 9 * mm, H, stroke=0, fill=1); c.restoreState()
        side = Frame(m * 0.9, m * 0.9, sw - m * 1.6, H - m * 1.9, id="side", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        main = Frame(sw + m * 0.8, m * 0.9, W - sw - m * 1.6, H - m * 1.9, id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        main2 = Frame(9 * mm + m, m * 0.9, W - 9 * mm - 2 * m, H - m * 1.9, id="main2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([PageTemplate("first", [side, main], onPage=bg), PageTemplate("later", [main2], onPage=bg_later)])
        SD = styles(t, base, sp, accent, on_dark=True); SM = styles(t, base, sp, accent)
        sidew = sw - m * 1.6
        photo = st.get("photo") if st.get("photo") and os.path.exists(st.get("photo")) else None
        b = Badge(30 * mm, mix(accent, colors.black, 0.22), colors.white, initials(d.get("name", "")), F["display"]["b"], photo=photo,
                  ring=mix(accent, colors.white, 0.45))
        story = [Spacer(1, 2), b, Spacer(1, 8 * sp)]
        if contact_items(d):
            story.append(section_head("contact", t, st, SD, accent, base, sp, dark=True))
        for k, v in contact_items(d):
            fs = SD["small"].fontSize
            while fs > 6.4 and pdfmetrics.stringWidth(str(v), F["body"]["r"], fs) > sidew - 17:
                fs -= 0.2
            story.append(tight(Table([[Icon(k, accent, colors.white, d=11),
                                       Paragraph(inline(v), ParagraphStyle("sc", parent=SD["small"], fontSize=fs, leading=fs * 1.3,
                                                                           textColor=colors.white))]],
                                     colWidths=[16, sidew - 16])))
            story.append(Spacer(1, 3))
        for key in [k for k in order if k in SIDEBAR_KEYS]:
            story += body_section(key, d, t, st, SD, accent, sidew, sp, base, dark=True)
        story += [NextPageTemplate("later"), FrameBreak()]
        SM["name"].fontSize = base * 2.6; SM["name"].leading = base * 3.1
        story.append(Paragraph(safe(d.get("name", ""), SM["name"].fontName), SM["name"]))
        if d.get("headline"): story.append(Paragraph(safe(d["headline"], SM["headline"].fontName), SM["headline"]))
        story.append(Spacer(1, 2 * sp))
        mw = W - sw - m * 1.6
        for key in [k for k in order if k not in SIDEBAR_KEYS]:
            story += body_section(key, d, t, st, SM, accent, mw, sp, base)
        doc.build(story)
        return pages["n"]

    width = W - 2 * m
    hdr_h = [0]
    def onpage(c, doc_):
        count(c, doc_)
        if t["header"] in ("tint", "monogram") and doc_.page == 1:
            c.saveState(); c.setFillColor(tint); c.rect(0, H - hdr_h[0], W, hdr_h[0], stroke=0, fill=1)
            c.setFillColor(accent); c.rect(0, H - hdr_h[0], W, 2.2, stroke=0, fill=1); c.restoreState()
        if t.get("strip"):
            c.saveState(); c.setFillColor(accent); c.rect(0, H - 5, W, 5, stroke=0, fill=1); c.restoreState()
    frame = Frame(m, m * 0.9, width, H - m * 1.9, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("p", [frame], onPage=onpage)])
    S = styles(t, base, sp, accent)
    if st["template"] == "compact":
        S["name"].fontSize = base * 2.4; S["name"].leading = base * 2.9
    hb = header_block(d, t, st, S, accent, width, base, sp)
    hgt = sum(f.wrap(width, H)[1] for f in hb)
    hdr_h[0] = m + hgt + 4 * sp
    story = list(hb)
    if t["header"] in ("tint", "monogram"):
        story.append(Spacer(1, 8 * sp))
    for key in order:
        story += body_section(key, d, t, st, S, accent, width, sp, base)
    doc.build(story)
    return pages["n"]


def render(d, st, out_pdf):
    target = int(st.get("pages", 1)); last = (0, 1.0)
    for scale in [1.0, 0.97, 0.94, 0.91, 0.88, 0.85]:
        if st["size"] * scale < MIN_SIZE - 1e-6:
            break
        n = build(d, st, out_pdf, scale); last = (n, scale)
        if n <= target:
            return last
    return last


# ---------------------------------------------------------------- DOCX (simple editable copy)
def write_docx(d, st, path):
    acc = (st.get("accent") or "#2D5BFF").lstrip("#"); base = 10.5; fontname = "Calibri"
    size = A4 if str(st.get("page", "A4")).upper() == "A4" else LETTER
    mg = int(MARGINS.get(st.get("margins", "normal"), 15) / 25.4 * 1440)
    tabpos = int(size[0] / 72 * 1440) - 2 * mg
    hp = lambda pt: str(int(round(pt * 2))); body = []
    def run(text, b=False, i=False, color=None, sz=None):
        pr = f'<w:rFonts w:ascii="{fontname}" w:hAnsi="{fontname}" w:cs="{fontname}"/>' + ("<w:b/>" if b else "") + ("<w:i/>" if i else "")
        pr += (f'<w:color w:val="{color}"/>' if color else "") + f'<w:sz w:val="{hp(sz or base)}"/>'
        return f'<w:r><w:rPr>{pr}</w:rPr><w:t xml:space="preserve">{escape(str(text))}</w:t></w:r>'
    def rich(text):
        return "".join(run(p, b=k % 2 == 1) for k, p in enumerate(re.split(r"\*\*(.+?)\*\*", str(text))) if p)
    def para(runs, before=0, after=2, ind=None, tab=False, border=False, keep=False):
        p = ("<w:keepNext/>" if keep else "") + (f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="{acc}"/></w:pBdr>' if border else "")
        p += (f'<w:tabs><w:tab w:val="right" w:pos="{tabpos}"/></w:tabs>' if tab else "") + f'<w:spacing w:before="{int(before*20)}" w:after="{int(after*20)}"/>' + (ind or "")
        body.append(f"<w:p><w:pPr>{p}</w:pPr>{runs}</w:p>")
    def heading(txt): para(run(txt, b=True, color=acc, sz=base * 1.2), before=9, after=3, border=True, keep=True)
    def bullet(txt): para(run("•\t", color=acc) + rich(txt), after=1, ind='<w:ind w:left="360" w:hanging="240"/>')
    para(run(d.get("name", ""), b=True, sz=24, color=acc), after=1)
    if d.get("headline"): para(run(d["headline"], sz=base * 1.15), after=1)
    cs = [v for _, v in contact_items(d)]
    if cs: para(run("  ·  ".join(cs), color="5B6470", sz=base * 0.92), after=4)
    order = st.get("order") or ORDERS.get(st.get("preset", "experienced"), ORDERS["experienced"])
    for key in [k for k in order if k not in set(st.get("hide", []))]:
        v = d.get(key)
        if key == "extra":
            for sec in d.get("extra", []) or []:
                heading(sec.get("title", "More")); [bullet(x) for x in sec.get("items", [])]
            continue
        if not v: continue
        heading((st.get("titles", {}) or {}).get(key) or TITLES.get(key, key.title()))
        if key == "summary": para(rich(v))
        elif key in ("experience", "projects", "education"):
            for e in v:
                name = e.get("role") or e.get("name") or e.get("degree", "")
                if e.get("link"): name += "  " + e["link"]
                sub = e.get("org") or e.get("context") or " · ".join(x for x in (e.get("school", ""), e.get("score", "")) if x)
                dates = e.get("date") or daterange(e.get("start"), e.get("end"))
                para(run(name, b=True, sz=base * 1.04) + (run("\t") + run(dates, color="5B6470", sz=base * 0.92) if dates else ""), tab=True, after=0, keep=True)
                sl = " · ".join(x for x in (sub, e.get("location", "")) if x)
                if sl: para(run(sl, color=acc), after=1)
                for b in e.get("bullets") or e.get("details") or []: bullet(b)
                para("", after=2)
        elif key == "skills":
            groups = v if (isinstance(v, list) and v and isinstance(v[0], dict)) else [{"group": "", "items": v}]
            for g in groups:
                para((run(g["group"] + ": ", b=True) if g.get("group") else "") + run(", ".join(g.get("items", []))), after=1)
        elif key == "certifications":
            for c in v: bullet(c if isinstance(c, str) else " · ".join(x for x in (c.get("name", ""), c.get("issuer", ""), c.get("date", "")) if x))
        elif key in ("achievements", "volunteering"): [bullet(x) for x in (v if isinstance(v, list) else [v])]
        elif key == "languages": para(run(", ".join(parse_lang(x)[0] for x in (v if isinstance(v, list) else [v]))))
        elif key == "personal": para("".join(run(f"{k}: ", b=True) + run(f"{x}    ") for k, x in v.items()))
    w, h = int(size[0] / 72 * 1440), int(size[1] / 72 * 1440)
    sect = f'<w:sectPr><w:pgSz w:w="{w}" w:h="{h}"/><w:pgMar w:top="{mg}" w:right="{mg}" w:bottom="{mg}" w:left="{mg}" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>'
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(body) + sect + "</w:body></w:document>")
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("word/document.xml", xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("--out"); ap.add_argument("--docx", action="store_true")
    for k in ("template", "page", "accent", "margins", "preset", "photo"):
        ap.add_argument(f"--{k}")
    ap.add_argument("--pages", type=int); ap.add_argument("--size", type=float)
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    st = dict(d.get("style", {}) or {})
    for k in ("template", "page", "accent", "margins", "preset", "pages", "size", "photo"):
        if getattr(a, k) is not None:
            st[k] = getattr(a, k)
    st["template"] = ALIASES.get(st.get("template", "clean"), st.get("template", "clean"))
    if st["template"] not in TEMPLATES:
        sys.exit(f"unknown template {st['template']!r}; use one of: {', '.join(TEMPLATES)}")
    st.setdefault("size", TEMPLATES[st["template"]]["size"]); st.setdefault("pages", 1)
    if st.get("photo") and not os.path.isabs(st["photo"]):
        st["photo"] = os.path.join(os.path.dirname(os.path.abspath(a.json)), st["photo"])
    register_fonts()
    def scripts_found(x, out):
        if isinstance(x, str):
            for ch in x:
                o = ord(ch)
                if 0x0900 <= o <= 0x0DFF: out.add("Indic (e.g. Malayalam)")
                elif 0x0600 <= o <= 0x06FF: out.add("Arabic")
                elif 0x4E00 <= o <= 0x9FFF: out.add("Chinese/Japanese")
        elif isinstance(x, dict):
            for k, v in x.items():
                if k != "style": scripts_found(v, out)
        elif isinstance(x, list):
            for v in x: scripts_found(v, out)
        return out
    other = scripts_found(d, set())
    if other:
        print(f"WARNING: the resume has {', '.join(sorted(other))} text. The PDF fonts can't show it (it prints as boxes).")
        print("         Write the resume in English (names in English letters), or deliver only the DOCX (--docx), which Word shapes correctly.")
    name = a.out or re.sub(r"[^A-Za-z0-9]+", "_", d.get("name", "resume")).strip("_") + "_Resume"
    out_pdf = name if name.endswith(".pdf") else name + ".pdf"
    pages, scale = render(d, st, out_pdf)
    kind = resolve(st)["kind"]
    print(f"PDF: {out_pdf}  ({pages} page{'s' if pages > 1 else ''}, template {st['template']} "
          f"[{'ATS-safe' if kind == 'ats' else 'designer: best when a person reads it'}], body {st['size'] * scale:.1f} pt)")
    if a.docx:
        out_docx = out_pdf[:-4] + ".docx"; write_docx(d, st, out_docx)
        print(f"DOCX: {out_docx}  (simple editable copy for Word / Google Docs)")
    if pages > int(st["pages"]):
        print(f"DOES NOT FIT: needs {pages} pages at the smallest readable size, limit is {st['pages']}. "
              f"Shorten the content (oldest roles, weakest bullets, long summary) or allow {pages} pages.")
        sys.exit(3)


if __name__ == "__main__":
    main()
