from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime


def generate_financial_pdf_report(user, report, financial_data, deposits=None, account=None):
    """Generate a PDF financial report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("Financial Report", title_style)
    elements.append(title)
    
    # User info
    user_info = f"<b>User:</b> {user.full_name}<br/><b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    if report.date_from or report.date_to:
        date_range = f"<br/><b>Period:</b> {report.date_from or 'Start'} to {report.date_to or 'Present'}"
        user_info += date_range
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Account Summary
    elements.append(Paragraph("Account Summary", heading_style))
    account_summary = financial_data.get('account_summary', {})
    account_data = [
        ['Metric', 'Amount'],
        ['Total Contributions', f"KES {account_summary.get('total_contributions', 0):,.2f}"],
        ['Interest Earned', f"KES {account_summary.get('interest_earned', 0):,.2f}"],
        ['Account Balance', f"KES {account_summary.get('account_balance', 0):,.2f}"],
    ]
    
    account_table = Table(account_data, colWidths=[3*inch, 2.5*inch])
    account_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(account_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Period Summary
    elements.append(Paragraph("Period Summary", heading_style))
    period_summary = financial_data.get('period_summary', {})
    period_data = [
        ['Metric', 'Value'],
        ['Total Deposits', f"KES {period_summary.get('total_deposits', 0):,.2f}"],
        ['Number of Transactions', str(period_summary.get('deposit_count', 0))],
        ['Average Deposit', f"KES {period_summary.get('average_deposit', 0):,.2f}"],
    ]
    
    period_table = Table(period_data, colWidths=[3*inch, 2.5*inch])
    period_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Monthly Breakdown
    monthly_breakdown = financial_data.get('monthly_breakdown', [])
    if monthly_breakdown:
        elements.append(Paragraph("Monthly Breakdown", heading_style))
        monthly_data = [['Month', 'Total Amount', 'Transactions']]
        for month in monthly_breakdown:
            monthly_data.append([
                month['month'],
                f"KES {month['total_amount']:,.2f}",
                str(month['transaction_count'])
            ])
        
        monthly_table = Table(monthly_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(monthly_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Recent Transactions
    recent_transactions = financial_data.get('recent_transactions', [])
    if recent_transactions:
        elements.append(Paragraph("Recent Transactions", heading_style))
        transaction_data = [['Date', 'Amount', 'Method', 'Status']]
        for trans in recent_transactions[:10]:
            created_at = trans.get('created_at')
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%Y-%m-%d')
            else:
                date_str = str(created_at)[:10]
            
            transaction_data.append([
                date_str,
                f"KES {trans.get('amount', 0):,.2f}",
                trans.get('payment_method', 'N/A'),
                trans.get('status', 'N/A')
            ])
        
        trans_table = Table(transaction_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(trans_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_compensatory_pdf_report(user, report, compensatory_data):
    """Generate PDF for compensatory report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("Compensatory Report", title_style)
    elements.append(title)
    
    # User info
    user_info = f"<b>User:</b> {user.full_name}<br/><b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    if report.date_from or report.date_to:
        date_range = f"<br/><b>Period:</b> {report.date_from or 'Start'} to {report.date_to or 'Present'}"
        user_info += date_range
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph("Summary", heading_style))
    summary = compensatory_data.get('summary', {})
    summary_data = [
        ['Metric', 'Value'],
        ['Total Beneficiaries', str(summary.get('total_beneficiaries', 0))],
        ['Active Beneficiaries', str(summary.get('active_beneficiaries', 0))],
        ['Inactive Beneficiaries', str(summary.get('inactive_beneficiaries', 0))],
        ['Total Contributions', f"KES {summary.get('total_contributions', 0):,.2f}"],
        ['Total Allocated', f"{summary.get('total_allocated_percentage', 0)}%"],
        ['Unallocated', f"{summary.get('unallocated_percentage', 0)}% (KES {summary.get('unallocated_amount', 0):,.2f})"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Beneficiary Allocations
    beneficiaries = compensatory_data.get('beneficiaries', [])
    if beneficiaries:
        elements.append(Paragraph("Beneficiary Allocations", heading_style))
        beneficiary_data = [['Name', 'Relationship', 'Percentage', 'Allocated Amount', 'Status']]
        for ben in beneficiaries:
            beneficiary_data.append([
                ben.get('name', 'N/A'),
                ben.get('relationship', 'N/A'),
                f"{ben.get('percentage', 0)}%",
                f"KES {ben.get('allocated_amount', 0):,.2f}",
                ben.get('status', 'N/A')
            ])
        
        ben_table = Table(beneficiary_data, colWidths=[1.5*inch, 1.3*inch, 1*inch, 1.5*inch, 0.7*inch])
        ben_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(ben_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_activity_pdf_report(user, report, activity_data):
    """Generate PDF for activity report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("Activity Report", title_style)
    elements.append(title)
    
    # User info
    user_info = f"<b>User:</b> {user.full_name}<br/><b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    if report.date_from or report.date_to:
        date_range = f"<br/><b>Period:</b> {report.date_from or 'Start'} to {report.date_to or 'Present'}"
        user_info += date_range
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph("Summary", heading_style))
    summary = activity_data.get('summary', {})
    summary_data = [
        ['Metric', 'Value'],
        ['Total Activities', str(summary.get('total_activities', 0))],
        ['Unique Actions', str(summary.get('unique_actions', 0))],
        ['Most Common Action', summary.get('most_common_action') or 'N/A'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Action Breakdown
    action_breakdown = activity_data.get('action_breakdown', [])
    if action_breakdown:
        elements.append(Paragraph("Action Breakdown", heading_style))
        action_data = [['Action', 'Count']]
        for action in action_breakdown:
            action_data.append([
                action.get('action', 'N/A'),
                str(action.get('count', 0))
            ])
        
        action_table = Table(action_data, colWidths=[4*inch, 1.5*inch])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(action_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Recent Activities
    recent_activities = activity_data.get('recent_activities', [])
    if recent_activities:
        elements.append(Paragraph("Recent Activities", heading_style))
        recent_data = [['Date', 'Action', 'Description']]
        for activity in recent_activities[:15]:
            created_at = activity.get('created_at')
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = str(created_at)[:16]
            
            description = activity.get('description', '')
            if description and len(description) > 50:
                description = description[:47] + '...'
            
            recent_data.append([
                date_str,
                activity.get('action', 'N/A')[:30],
                description
            ])
        
        recent_table = Table(recent_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
        recent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(recent_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer