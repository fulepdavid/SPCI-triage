from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import resource_path

pdfmetrics.registerFont(TTFont("DejaVu", resource_path("fonts/DejaVuSans.ttf")))


def write_report(answers, panel_title, tr):
    """Writes the answers to answers/answers_<timestamp>.pdf and returns the path."""
    answers_dir = Path("answers")
    answers_dir.mkdir(exist_ok=True)
    filename = answers_dir / f"answers_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    styles = getSampleStyleSheet()
    for name in ("Normal", "Heading1", "Heading2", "Title"):
        styles[name].fontName = "DejaVu"

    data = [["Kérdés", "Válasz"]]
    for a in answers:
        data.append([tr(a["question"]), tr(a["answer"])])

    table = Table(data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ]))

    story = [
        Paragraph("<b>Triage lap</b>", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"Dátum: {datetime.now():%Y-%m-%d %H:%M}", styles["Normal"]),
        Paragraph(f"Panasz: {panel_title}", styles["Normal"]),
        Spacer(1, 20),
        table,
    ]
    SimpleDocTemplate(str(filename)).build(story)
    return filename