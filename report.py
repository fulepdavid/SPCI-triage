from datetime import datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import resource_path

pdfmetrics.registerFont(TTFont("DejaVu", resource_path("fonts/DejaVuSans.ttf")))


def _cell(text, style):
    if text is None:
        text = ""
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def write_report(answers, panel_title, tr):
    """Writes the answers to answers/answers_<timestamp>.pdf and returns the path."""
    answers_dir = Path("answers")
    answers_dir.mkdir(exist_ok=True)
    filename = answers_dir / f"answers_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    styles = getSampleStyleSheet()
    for name in ("Normal", "Heading1", "Heading2", "Title"):
        styles[name].fontName = "DejaVu"
    cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=11, leading=15)

    doc = SimpleDocTemplate(str(filename))

    data = [[_cell("Kérdés", cell), _cell("Válasz", cell)]]
    for a in answers:
        data.append([_cell(tr(a["question"]), cell), _cell(tr(a["answer"]), cell)])

    table = Table(data, colWidths=[doc.width * 0.4, doc.width * 0.6], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story = [
        Paragraph("<b>Triage lap</b>", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"Dátum: {datetime.now():%Y-%m-%d %H:%M}", styles["Normal"]),
        Paragraph(f"Panasz: {panel_title}", styles["Normal"]),
        Spacer(1, 20),
        table,
    ]
    doc.build(story)
    return filename