"""Monthly PDF report generation and email."""
import os
import tempfile
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from utils.currency import SYMBOLS


def generate_pdf_report(user, transactions, goals, budgets, output_path=None):
    """Generate a PDF report for the current month."""
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(),
                                   f"finsight_report_{date.today().strftime('%Y%m')}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"FinSight Monthly Report", styles["Title"]))
    elements.append(Paragraph(f"{date.today().strftime('%B %Y')}  |  {user.full_name}",
                              styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Summary
    income = sum(t.amount for t in transactions if t.type == "income")
    expense = sum(t.amount for t in transactions if t.type == "expense")
    sym = SYMBOLS.get(user.preferred_currency or "INR", "")
    elements.append(Paragraph(f"Total Income: {sym}{income:,.2f}", styles["Heading2"]))
    elements.append(Paragraph(f"Total Expenses: {sym}{expense:,.2f}", styles["Heading2"]))
    elements.append(Paragraph(f"Net Savings: {sym}{income - expense:,.2f}", styles["Heading2"]))
    elements.append(Spacer(1, 15))

    # Transaction table
    if transactions:
        elements.append(Paragraph("Recent Transactions", styles["Heading3"]))
        data = [["Date", "Category", "Type", "Amount", "Description"]]
        for t in sorted(transactions, key=lambda x: x.transaction_date, reverse=True)[:20]:
            data.append([
                t.transaction_date.strftime("%d %b"),
                t.category_name,
                t.type.title(),
                f"{sym}{t.amount:,.2f}",
                t.description or "",
            ])
        table = Table(data, colWidths=[60, 80, 55, 70, 150])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ]))
        elements.append(table)

    # Goals
    if goals:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Savings Goals", styles["Heading3"]))
        gdata = [["Goal", "Progress", "Target", "Status"]]
        for g in goals:
            gdata.append([g.name, f"{g.progress_pct:.0f}%", f"{sym}{g.target_amount:,.0f}", g.status.title()])
        gtable = Table(gdata, colWidths=[100, 60, 80, 70])
        gtable.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22c55e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(gtable)

    doc.build(elements)
    return output_path


def send_report_email(smtp_host, smtp_port, smtp_user, smtp_pass,
                      to_email, pdf_path):
    """Send the PDF report via email (SMTP)."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    msg = MIMEMultipart()
    msg["Subject"] = f"FinSight Report - {date.today().strftime('%B %Y')}"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText("Your monthly FinSight report is attached.", "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
        msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
