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


def generate_error_excel(output_path: str, errors: list[dict]) -> str:
    df = pd.DataFrame(errors)
    if df.empty:
        df = pd.DataFrame(columns=["row", "column", "severity", "error", "error_type"])
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Validation Errors')
        worksheet = writer.sheets['Validation Errors']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).str.len().max() if not df.empty else 0, len(str(col))) + 2
            # Handle columns beyond Z (e.g. AA) just in case, though error logs are small
            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = min(max_len, 50)
            
    return output_path


def generate_cleaned_excel(output_path: str, df: pd.DataFrame) -> str:
    # Ensure phone and ID columns are explicitly strings so Excel never uses scientific notation
    for col in df.columns:
        if "phone" in col.lower() or "id" in col.lower() or df[col].dtype == object:
            df[col] = df[col].astype(str)
            
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        worksheet = writer.sheets['Cleaned Data']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).str.len().max() if not df.empty else 0, len(str(col))) + 2
            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = min(max_len, 50)
            
    return output_path
