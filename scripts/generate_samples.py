"""Generate the bundled sample assets (Excel guide, PDF reference, DOCX template).

Run this once after installing dependencies on Windows:

    py -m pip install -e .
    py scripts\\generate_samples.py

It writes three files into ``src/mcp_market_research/samples/``:

- ``sample_channel_guide.xlsx`` — three channels: social_media, email, in_store
- ``sample_template.pdf``       — visual layout reference with placeholders
- ``sample_template.docx``      — docxtpl Jinja2 template that mirrors the PDF
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "mcp_market_research" / "samples"


def build_excel(path: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    wrap = Alignment(wrap_text=True, vertical="top")
    headers = ["section", "question_type", "guidance", "example", "required", "notes"]

    channels: dict[str, list[list[object]]] = {
        "social_media": [
            ["Awareness", "single_choice",
             "Ask which platforms the respondent uses most for discovering brands like the client.",
             "Which platforms do you use most often to discover new brands?",
             "yes", ""],
            ["Awareness", "open_text",
             "Probe how the respondent first heard about the client's category.",
             "How did you first hear about <category>?",
             "no", ""],
            ["Engagement", "rating",
             "Measure 1-5 how engaging the respondent finds the client's social content.",
             "Rate the client's social content (1=boring, 5=very engaging).",
             "yes", "Use a 5-point scale, anchor labels."],
            ["Engagement", "multi_choice",
             "Which content formats drive the most engagement.",
             "Which formats do you engage with? (select all)",
             "yes", "Options: short video, long video, image, carousel, story, livestream."],
            ["Conversion", "yes_no",
             "Has the respondent ever purchased after seeing a social ad from the client.",
             "Have you ever bought from <client> after seeing one of their social posts/ads?",
             "yes", ""],
        ],
        "email": [
            ["Subscription", "single_choice",
             "How the respondent joined the email list.",
             "How did you originally sign up for our emails?",
             "yes", ""],
            ["Content", "rating",
             "Perceived usefulness of email content on a 1-5 scale.",
             "How useful do you find the emails? (1=not at all, 5=extremely)",
             "yes", ""],
            ["Frequency", "single_choice",
             "Preferred email cadence.",
             "What is your preferred email frequency?",
             "yes", "Options: daily, weekly, biweekly, monthly, less."],
            ["Content", "multi_choice",
             "Topics the respondent wants to see more of.",
             "Which topics would you like to see more of?",
             "no", ""],
            ["Loyalty", "open_text",
             "What would make the respondent recommend the newsletter.",
             "What single change would make you recommend our newsletter?",
             "no", ""],
        ],
        "in_store": [
            ["Visit", "single_choice",
             "Frequency of visits to the physical location.",
             "How often do you visit our store?",
             "yes", ""],
            ["Experience", "rating",
             "Overall in-store experience rating, 1-5.",
             "Rate your overall experience today (1=poor, 5=excellent).",
             "yes", ""],
            ["Staff", "rating",
             "Helpfulness of staff during the visit.",
             "How helpful were our staff today?",
             "yes", ""],
            ["Product", "open_text",
             "Anything the respondent wishes had been in stock.",
             "Was there anything you were looking for that we didn't have?",
             "no", ""],
            ["Loyalty", "yes_no",
             "Whether the respondent intends to return.",
             "Do you plan to visit us again in the next 3 months?",
             "yes", ""],
        ],
    }

    for sheet_name, rows in channels.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = wrap
        for row in rows:
            ws.append(row)
        for col_letter, width in zip("ABCDEF", (16, 16, 50, 50, 10, 30), strict=False):
            ws.column_dimensions[col_letter].width = width
        for row_cells in ws.iter_rows(min_row=2):
            for cell in row_cells:
                cell.alignment = wrap

    notes = wb.create_sheet("_meta")
    notes["A1"] = "This workbook is the bundled sample. Add or modify channels by adding sheets."
    notes["A2"] = "Sheets prefixed with '_' (like this one) are skipped by the parser."

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def build_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Market Research Questionnaire Template",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, spaceAfter=8)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=11, leading=14)

    story: list[object] = [
        Paragraph("{{COMPANY_NAME}}", h1),
        Paragraph("{{QUESTIONNAIRE_TITLE}}", h2),
        Paragraph(
            "Language: {{LANGUAGE}} &nbsp;&nbsp; Country: {{COUNTRY}} "
            "&nbsp;&nbsp; Generated: {{GENERATED_DATE}}",
            body,
        ),
        Spacer(1, 0.6 * cm),
        Paragraph("Introduction", h2),
        Paragraph(
            "Thank you for taking part in this short survey. Your answers help us "
            "improve our products and services. Responses are confidential and used "
            "only in aggregate.",
            body,
        ),
        Spacer(1, 0.4 * cm),
        Paragraph("&lt;&lt;SECTIONS_START&gt;&gt;", body),
        Paragraph("Section heading", h2),
        Paragraph("1. Sample question text here. *", body),
        Paragraph("[ ] Option A &nbsp;&nbsp; [ ] Option B &nbsp;&nbsp; [ ] Option C", body),
        Paragraph("2. Another question here.", body),
        Paragraph("&lt;&lt;SECTIONS_END&gt;&gt;", body),
        Spacer(1, 0.6 * cm),
        Paragraph("Closing", h2),
        Paragraph(
            "Thank you for your time. If you have additional comments, please share "
            "them with us at {{COMPANY_NAME}} support.",
            body,
        ),
    ]
    doc.build(story)


def build_docx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = title.add_run("{{ company_name }}")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)

    subtitle = doc.add_paragraph()
    sub_run = subtitle.add_run("{{ questionnaire_title }}")
    sub_run.bold = True
    sub_run.font.size = Pt(14)

    meta = doc.add_paragraph()
    meta.add_run(
        "Language: {{ language }}    Country: {{ country_code or '-' }}    "
        "Generated: {{ generated_date }}"
    ).italic = True

    doc.add_paragraph(
        "Thank you for taking part in this short survey. Your answers help us "
        "improve our products and services. Responses are confidential and used "
        "only in aggregate."
    )

    doc.add_paragraph("{% for section in sections %}")
    heading = doc.add_paragraph()
    h_run = heading.add_run("{{ section.heading }}")
    h_run.bold = True
    h_run.font.size = Pt(13)

    doc.add_paragraph("{% for q in section.questions %}")
    doc.add_paragraph(
        "{{ loop.index }}. {{ q.text }}{% if q.required %} *{% endif %}"
    )
    doc.add_paragraph(
        "{% if q.options %}{% for opt in q.options %}[ ] {{ opt }}    "
        "{% endfor %}{% endif %}"
    )
    doc.add_paragraph("{% endfor %}")
    doc.add_paragraph("{% endfor %}")

    doc.add_paragraph(
        "Thank you for your time. If you have additional comments, please share "
        "them with us at {{ company_name }} support."
    )

    doc.save(str(path))


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    excel_path = SAMPLES / "sample_channel_guide.xlsx"
    pdf_path = SAMPLES / "sample_template.pdf"
    docx_path = SAMPLES / "sample_template.docx"

    build_excel(excel_path)
    print(f"wrote {excel_path}")
    build_pdf(pdf_path)
    print(f"wrote {pdf_path}")
    build_docx(docx_path)
    print(f"wrote {docx_path}")


if __name__ == "__main__":
    main()
