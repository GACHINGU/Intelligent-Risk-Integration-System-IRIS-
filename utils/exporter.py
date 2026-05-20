# ─────────────────────────────────────────────────────────────────────────────
# IRIS — PDF Exporter
#
# Exports IRIS memos and reports as downloadable PDFs.
# Used by the dashboard for the "Download as PDF" button.
#
# Produces three PDF types:
#   1. Governor Memo
#   2. MPC Memo
#   3. Wananchi Brief
# ─────────────────────────────────────────────────────────────────────────────

import hashlib
# This forces Python to use a version of MD5 that doesn't crash
try:
    import hashlib
    _orig_md5 = hashlib.md5
    def _patched_md5(*args, **kwargs):
        kwargs.pop('usedforsecurity', None)
        return _orig_md5(*args, **kwargs)
    hashlib.md5 = _patched_md5
except Exception:
    pass

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from utils.logger import get_logger

logger = get_logger(__name__)

W, H     = A4
MARGIN   = 2.0 * cm
DOC_W    = W - 2 * MARGIN
CBK_DARK  = colors.HexColor('#003300')
CBK_GREEN = colors.HexColor('#006400')
GOLD      = colors.HexColor('#C5A028')
WHITE     = colors.white
MID_GREY  = colors.HexColor('#555555')
DARK_GREY = colors.HexColor('#1A1A1A')


def _styles():
    """Return a dict of ParagraphStyles for the PDF."""
    def S(nm, **kw):
        return ParagraphStyle(nm, **kw)
    return {
        "title":   S("T",  fontName="Helvetica-Bold",   fontSize=20, textColor=CBK_DARK,
                      alignment=TA_CENTER, leading=28, spaceAfter=6),
        "subject": S("Su", fontName="Helvetica-Oblique", fontSize=11, textColor=CBK_GREEN,
                      alignment=TA_CENTER, leading=16, spaceAfter=4),
        "meta":    S("Me", fontName="Helvetica",         fontSize=9,  textColor=MID_GREY,
                      alignment=TA_CENTER, leading=13, spaceAfter=2),
        "h1":      S("H1", fontName="Helvetica-Bold",    fontSize=11, textColor=WHITE,
                      alignment=TA_LEFT,   leading=16),
        "body":    S("B",  fontName="Helvetica",         fontSize=9.5, textColor=DARK_GREY,
                      alignment=TA_JUSTIFY, leading=15, spaceAfter=6, spaceBefore=2),
        "discl":   S("Di", fontName="Helvetica-Oblique", fontSize=7.5, textColor=MID_GREY,
                      alignment=TA_CENTER, leading=11),
    }


def _header_banner(cv, doc):
    """Render CBK header and footer on each page."""
    cv.saveState()
    cv.setFillColor(CBK_DARK)
    cv.rect(0, H - 1.6*cm, W, 1.6*cm, fill=1, stroke=0)
    cv.setFillColor(GOLD)
    cv.rect(0, H - 1.6*cm - 3, W, 3, fill=1, stroke=0)
    cv.setFillColor(WHITE)
    cv.setFont("Helvetica-Bold", 8)
    cv.drawString(MARGIN, H - 1.0*cm, "CENTRAL BANK OF KENYA — IRIS SYSTEM")
    cv.setFont("Helvetica", 8)
    cv.drawRightString(W - MARGIN, H - 1.0*cm,
                       f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}")
    cv.setFillColor(CBK_DARK)
    cv.rect(0, 0, W, 1.2*cm, fill=1, stroke=0)
    cv.setFillColor(WHITE)
    cv.setFont("Helvetica", 7.5)
    cv.drawString(MARGIN, 0.5*cm,
                  "SIMULATED EDUCATIONAL DOCUMENT — NOT AN OFFICIAL CBK PUBLICATION")
    cv.drawRightString(W - MARGIN, 0.5*cm, f"Page {doc.page}")
    cv.restoreState()


def _h1_block(text: str, colour_hex: str, styles: dict):
    """Render a section heading block."""
    tbl = Table([[Paragraph(text, styles["h1"])]], colWidths=[DOC_W])
    hex_col = colors.HexColor(colour_hex)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), hex_col),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, GOLD),
    ]))
    return tbl


def export_memo_to_pdf(memo: dict) -> bytes:
    """
    Export a memo dict to a PDF byte stream.

    INPUT:  memo — dict from one of the memo template builders
    OUTPUT: bytes — PDF file content (save or send as download)
    """
    buf    = io.BytesIO()
    styles = _styles()

    memo_colour = memo.get("colour", "#006400")

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.2*cm, bottomMargin=2.0*cm,
        title=memo.get("subject", "IRIS Memo"),
        author="IRIS — Policy Analysis Unit, CBK",
    )

    story = []

    # ── Cover block ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 0.8*cm),
        Paragraph("CENTRAL BANK OF KENYA", styles["title"]),
        Paragraph("Policy Analysis Unit — IRIS System", styles["meta"]),
        Spacer(1, 0.3*cm),
        HRFlowable(width="100%", thickness=2, color=GOLD),
        HRFlowable(width="100%", thickness=1, color=CBK_GREEN),
        Spacer(1, 0.4*cm),
        Paragraph(memo.get("type", "MEMO").replace("_", " "), styles["subject"]),
        Spacer(1, 0.3*cm),
    ]

    # Meta table
    meta_data = [
        [Paragraph("TO",      ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5,
                                              textColor=WHITE, alignment=TA_CENTER, leading=12)),
         Paragraph("FROM",    ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5,
                                              textColor=WHITE, alignment=TA_CENTER, leading=12)),
         Paragraph("DATE",    ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5,
                                              textColor=WHITE, alignment=TA_CENTER, leading=12)),
         Paragraph("REF",     ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5,
                                              textColor=WHITE, alignment=TA_CENTER, leading=12))],
        [Paragraph(memo.get("addressee", ""),  styles["body"]),
         Paragraph(memo.get("from",      ""),  styles["body"]),
         Paragraph(memo.get("date",      ""),  styles["body"]),
         Paragraph(memo.get("ref",       ""),  styles["body"])],
    ]
    meta_tbl = Table(meta_data, colWidths=[DOC_W*0.35, DOC_W*0.25, DOC_W*0.18, DOC_W*0.22])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  CBK_DARK),
        ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor("#F5F5F5")),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story += [meta_tbl, Spacer(1, 0.4*cm),
              HRFlowable(width="100%", thickness=1, color=GOLD),
              Spacer(1, 0.4*cm)]

    # IRIS score box
    score   = memo.get("iris_score", 50)
    regime  = memo.get("regime", "MODERATE")
    urgency = memo.get("urgency", "MEDIUM")
    score_data = [[
        Paragraph(
            f"IRIS Risk Score: <b>{score:.1f}/100</b> — {regime} | Urgency: {urgency}",
            ParagraphStyle("sb", fontName="Helvetica-Bold", fontSize=10,
                           textColor=colors.HexColor(memo_colour),
                           alignment=TA_CENTER, leading=14)
        )
    ]]
    score_tbl = Table(score_data, colWidths=[DOC_W])
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(memo_colour + "18")),
        ("BOX",           (0, 0), (-1, -1), 1.5, colors.HexColor(memo_colour)),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [score_tbl, Spacer(1, 0.6*cm)]

    # ── Sections ───────────────────────────────────────────────────────────────
    for section in memo.get("sections", []):
        title = section.get("title", "")
        body  = section.get("body",  "")

        story.append(KeepTogether([
            _h1_block(title, memo_colour, styles),
            Spacer(1, 0.2*cm),
        ]))

        # Split body into paragraphs on double newline
        for para_text in body.split("\n\n"):
            para_text = para_text.strip()
            if para_text:
                story.append(Paragraph(para_text, styles["body"]))

        # Highlight box for rate action
        if section.get("highlight"):
            highlight_col = section.get("highlight_colour", "#006400")
            hl_data = [[Paragraph(body[:500], styles["body"])]]
            hl_tbl  = Table(hl_data, colWidths=[DOC_W - 20])
            hl_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor(highlight_col+"22")),
                ("BOX",          (0,0),(-1,-1), 1.5, colors.HexColor(highlight_col)),
                ("TOPPADDING",   (0,0),(-1,-1), 8),
                ("BOTTOMPADDING",(0,0),(-1,-1), 8),
                ("LEFTPADDING",  (0,0),(-1,-1), 10),
            ]))
            story.append(hl_tbl)

        story.append(Spacer(1, 0.3*cm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 0.4*cm),
        HRFlowable(width="100%", thickness=1, color=GOLD),
        Spacer(1, 0.2*cm),
        Paragraph(
            "This document was auto-generated by IRIS v1.0 — Intelligent Risk Integration System. "
            "It is a simulated educational document and does not represent an official CBK publication. "
            "Lead Scientist: Stephen Munene | Policy Analysis Unit, Central Bank of Kenya.",
            styles["discl"]
        ),
    ]

    doc.build(story, onFirstPage=_header_banner, onLaterPages=_header_banner)
    buf.seek(0)
    return buf.read()


def get_pdf_download_name(memo_type: str) -> str:
    """Return a clean filename for the PDF download."""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    names = {
        "GOVERNOR_MEMO":  f"IRIS_Governor_Memo_{date_str}.pdf",
        "MPC_MEMO":       f"IRIS_MPC_Memo_{date_str}.pdf",
        "WANANCHI_BRIEF": f"IRIS_Wananchi_Brief_{date_str}.pdf",
    }
    return names.get(memo_type, f"IRIS_Memo_{date_str}.pdf")