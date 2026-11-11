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

# The report is always Hungarian, whatever language the patient used.


def _hu(value):
    if isinstance(value, dict):
        return str(value.get("hu", ""))
    return "" if value is None else str(value)


def _format_value(entry, value):
    """Display format only. The stored answer keeps the raw digits."""
    if not isinstance(value, str):
        return _hu(value)
    if entry.get("id") == "TAJSZAM" and len(value) == 9 and value.isdigit():
        return f"{value[:3]} {value[3:6]} {value[6:]}"
    if entry.get("keyboard_type") == "date" and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value


def _rows(entry):
    """Returns one (label, value) pair per table row."""
    value = entry["answer"]
    if isinstance(value, dict) and "rows" in value:
        return value["rows"]
    return [(_hu(entry["question"]), _format_value(entry, value))]


def _cell(text, style):
    return Paragraph(escape("" if text is None else str(text)), style)


def write_report(answers, panel_title):
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
    for entry in answers:
        for label, value in _rows(entry):
            data.append([_cell(label, cell), _cell(value, cell)])

    table = Table(data, colWidths=[doc.width * 0.45, doc.width * 0.55], repeatRows=1)
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
        Paragraph(escape(f"Dátum: {datetime.now():%Y-%m-%d %H:%M}"), styles["Normal"]),
        Paragraph(escape(f"Panasz: {_hu(panel_title)}"), styles["Normal"]),
        Spacer(1, 20),
        table,
    ]
    doc.build(story)
    return filename