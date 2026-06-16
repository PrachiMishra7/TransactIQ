import io
import os
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_pdf_report(
    output_path: str,
    file_name: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    quality_score: float,
    quality_label: str,
    errors: list[dict],
    summary: str,
) -> str:
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, spaceAfter=20, textColor=colors.HexColor("#1e293b"))
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=10, textColor=colors.HexColor("#334155"))
    body_style = styles["Normal"]

    story = []
    story.append(Paragraph("TransactIQ Validation Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph("File Information", heading_style))
    info_data = [
        ["File Name", file_name],
        ["Total Records", str(total_rows)],
        ["Valid Records", str(valid_rows)],
        ["Invalid Records", str(invalid_rows)],
        ["Quality Score", f"{quality_score}/100 ({quality_label})"],
    ]
    info_table = Table(info_data, colWidths=[2.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Error Breakdown by Type", heading_style))
    from collections import Counter
    type_counts = Counter(e.get("error_type", "unknown") for e in errors)
    error_data = [["Error Type", "Count"]] + [[k.replace("_", " ").title(), str(v)] for k, v in type_counts.most_common(10)]
    error_table = Table(error_data, colWidths=[3 * inch, 1.5 * inch])
    error_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(error_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("AI Summary & Recommendations", heading_style))
    for line in summary.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace("•", "&#8226;"), body_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    return output_path


def generate_error_csv(output_path: str, errors: list[dict]) -> str:
    df = pd.DataFrame(errors)
    if df.empty:
        df = pd.DataFrame(columns=["row", "column", "severity", "error", "error_type"])
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    df.to_csv(output_path, index=False)
    return output_path


def generate_cleaned_csv(output_path: str, df: pd.DataFrame) -> str:
    df.to_csv(output_path, index=False)
    return output_path
