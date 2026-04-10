from __future__ import annotations

from io import BytesIO
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PDF_FONT_NAME = "STSong-Light"
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "]",
    flags=re.UNICODE,
)
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def _ensure_cjk_font() -> None:
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    if PDF_FONT_NAME not in registered_fonts:
        pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT_NAME))


def _build_styles() -> dict[str, ParagraphStyle]:
    _ensure_cjk_font()
    base_styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=base_styles["Title"],
            fontName=PDF_FONT_NAME,
            fontSize=18,
            leading=24,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "heading": ParagraphStyle(
            "CustomHeading",
            parent=base_styles["Heading2"],
            fontName=PDF_FONT_NAME,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#1f3a5f"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "CustomBody",
            parent=base_styles["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=10.5,
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "CustomBullet",
            parent=base_styles["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=10.5,
            leading=16,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=4,
        ),
    }


def _escape_text(text: str) -> str:
    sanitized = _sanitize_text(text)
    return (
        sanitized.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _sanitize_text(text: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", text)
    return (
        cleaned.replace("•", "-")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .strip()
    )


def _strip_markdown(text: str) -> str:
    cleaned = _sanitize_text(text)
    cleaned = BOLD_PATTERN.sub(r"\1", cleaned)
    cleaned = cleaned.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = cleaned.replace("`", "")
    return cleaned


def _looks_like_table_separator(line: str) -> bool:
    stripped = line.replace(" ", "")
    return stripped.startswith("|") and set(stripped) <= {"|", ":", "-"}


def _parse_markdown_table(lines: list[str], start_index: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start_index

    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("|"):
            break
        if _looks_like_table_separator(line):
            index += 1
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
        index += 1

    return rows, index


def _build_table(rows: list[list[str]], styles: dict[str, ParagraphStyle]) -> Table:
    column_count = max(len(row) for row in rows)
    normalized_rows: list[list[str]] = []

    for row_index, row in enumerate(rows):
        padded_row = row + [""] * (column_count - len(row))
        style = styles["heading"] if row_index == 0 else styles["body"]
        normalized_rows.append([Paragraph(_escape_text(cell), style) for cell in padded_row])

    table = Table(normalized_rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9eb6cf")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_summary_pdf(summary_markdown: str, course_name: str) -> bytes:
    styles = _build_styles()
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=course_name,
    )

    story = [
        Paragraph(_escape_text(course_name), styles["title"]),
        Spacer(1, 6),
    ]

    lines = summary_markdown.splitlines()
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 6))
            index += 1
            continue

        if line.startswith("|"):
            rows, next_index = _parse_markdown_table(lines, index)
            if rows:
                story.append(_build_table(rows, styles))
                story.append(Spacer(1, 8))
                index = next_index
                continue

        if line.startswith("## "):
            story.append(Paragraph(_escape_text(_strip_markdown(line[3:].strip())), styles["heading"]))
        elif line.startswith("# "):
            story.append(Paragraph(_escape_text(_strip_markdown(line[2:].strip())), styles["title"]))
        elif line.startswith("- ") or line.startswith("* "):
            bullet_text = _strip_markdown(line[2:].strip())
            story.append(Paragraph(_escape_text(f"- {bullet_text}"), styles["bullet"]))
        elif line.startswith("  * "):
            bullet_text = _strip_markdown(line[4:].strip())
            story.append(Paragraph(_escape_text(f"  - {bullet_text}"), styles["bullet"]))
        elif line.startswith("  - "):
            bullet_text = _strip_markdown(line[4:].strip())
            story.append(Paragraph(_escape_text(f"  - {bullet_text}"), styles["bullet"]))
        else:
            story.append(Paragraph(_escape_text(_strip_markdown(line)), styles["body"]))

        index += 1

    document.build(story)
    return buffer.getvalue()
