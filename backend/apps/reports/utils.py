from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def generate_financial_pdf_report(user, deposits, account):
    """Generate a PDF financial report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Financial Report - {user.full_name}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Summary
    summary_data = [
        ['Total Contributions:', f'KES {account.total_contributions:,.2f}'],
        ['Interest Earned:', f'KES {account.interest_earned:,.2f}'],
        ['Total Deposits:', len(deposits)],
        ['Report Date:', datetime.now().strftime('%Y-%m-%d')],
    ]
    
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Deposits table
    deposit_header = Paragraph("Deposit History", styles['Heading2'])
    elements.append(deposit_header)
    elements.append(Spacer(1, 0.2 * inch))
    
    deposit_data = [['Date', 'Amount', 'Method', 'Status']]
    for deposit in deposits:
        deposit_data.append([
            deposit.created_at.strftime('%Y-%m-%d'),
            f'KES {deposit.amount:,.2f}',
            deposit.payment_method,
            deposit.status
        ])
    
    deposit_table = Table(deposit_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    deposit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(deposit_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

