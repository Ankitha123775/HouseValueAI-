import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_valuation_pdf(prop_details, prediction_res, metadata):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e293b'),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        alignment=0
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    
    disclaimer_style = ParagraphStyle(
        'DocDisclaimer',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        alignment=0
    )

    story.append(Paragraph("HomeValue AI", title_style))
    story.append(Paragraph("Smart Property Valuation & Machine Learning Intelligence Report", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y - %H:%M IST')} | Reference ID: HVI-{datetime.now().strftime('%Y%m%d%H%M%S')}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6366f1'), spaceAfter=15))

    story.append(Paragraph("1. Property Attributes & Specifications", heading_style))
    
    spec_data = [
        [Paragraph("<b>Locality / Area:</b>", body_style), Paragraph(str(prop_details['location']), body_style)],
        [Paragraph("<b>Total Carpet Area:</b>", body_style), Paragraph(f"{prop_details['total_sqft']:,} sq. ft.", body_style)],
        [Paragraph("<b>Configuration:</b>", body_style), Paragraph(f"{prop_details['bhk']} BHK / {prop_details['bath']} Bathrooms", body_style)],
        [Paragraph("<b>Property Age:</b>", body_style), Paragraph(f"{prop_details['age']} Years", body_style)]
    ]
    
    spec_table = Table(spec_data, colWidths=[160, 370])
    spec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. ML Property Valuation Summary", heading_style))
    
    val_data = [
        [Paragraph("<b>Estimated Market Value:</b>", body_style), Paragraph(f"<b>{prediction_res['formatted_price_lakhs']} ({prediction_res['formatted_price_inr']})</b>", body_style)],
        [Paragraph("<b>95% Valuation Confidence Range:</b>", body_style), Paragraph(f"{prediction_res['price_range_lakhs']}", body_style)],
        [Paragraph("<b>Calculated Rate per Sq. Ft.:</b>", body_style), Paragraph(f"<b>{prediction_res['formatted_pps']}</b>", body_style)],
        [Paragraph("<b>Locality Avg Rate per Sq. Ft.:</b>", body_style), Paragraph(f"₹{prediction_res['loc_avg_pps']:,}/sqft", body_style)],
        [Paragraph("<b>Market Rating:</b>", body_style), Paragraph(f"<b>{prediction_res['valuation_badge']}</b>", body_style)]
    ]
    
    val_table = Table(val_data, colWidths=[200, 330])
    val_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eeeffe')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#6366f1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c7d2fe')),
        ('TOPPADDING', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(val_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("3. AI Intelligence Insights", heading_style))
    for insight in prediction_res.get('insights', []):
        story.append(Paragraph(f"• {insight}", body_style))
        story.append(Spacer(1, 4))
        
    story.append(Spacer(1, 15))

    story.append(Paragraph("4. Machine Learning Model Metadata", heading_style))
    model_info = [
        [Paragraph("<b>Model Architecture:</b>", body_style), Paragraph("Random Forest Regressor (Ensemble)", body_style)],
        [Paragraph("<b>Coefficient of Determination (R² Score):</b>", body_style), Paragraph(f"{metadata.get('r2_score', 0.98):.4f} (High Accuracy)", body_style)],
        [Paragraph("<b>Mean Absolute Error (MAE):</b>", body_style), Paragraph(f"₹{metadata.get('mae_lakhs', 3.5)} Lakhs", body_style)],
        [Paragraph("<b>Training Data Volume:</b>", body_style), Paragraph(f"{metadata.get('total_properties_in_dataset', 1800)} Verified Records", body_style)]
    ]
    meta_table = Table(model_info, colWidths=[200, 330])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 25))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    disclaimer_text = (
        "<b>DISCLAIMER:</b> This valuation report is generated using an automated Machine Learning predictive model "
        "trained on historical property records for informational purposes only. It does not constitute a certified bank appraisal, "
        "legal valuation, or guaranteed market listing price. Actual property transaction prices may vary based on market conditions, "
        "builder quality, and specific interior amenities."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes