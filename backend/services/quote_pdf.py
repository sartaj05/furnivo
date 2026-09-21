from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def money(value):
    return f'INR {float(value or 0):,.2f}'


def build_quote_pdf(quote):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f'Furnivo {quote.quote_number}',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Right', parent=styles['BodyText'], alignment=TA_RIGHT))
    story = [
        Paragraph('FURNIVO', styles['Heading1']),
        Paragraph('Furniture · Interiors · Building Materials', styles['BodyText']),
        Spacer(1, 8 * mm),
        Table([
            ['Quotation', quote.quote_number],
            ['Customer', quote.customer_name],
            ['Date', quote.quote_date.isoformat()],
            ['Status', quote.status],
        ], colWidths=[35 * mm, 115 * mm], style=[
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6d776f')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]),
        Spacer(1, 8 * mm),
    ]

    rows = [['Item', 'SKU', 'Qty', 'Unit price', 'Amount']]
    for item in quote.items:
        rows.append([
            item.description,
            item.sku or '—',
            f'{float(item.quantity):g} {item.unit}',
            money(item.unit_price),
            money(item.line_total),
        ])
    rows.append(['', '', '', 'Subtotal', money(quote.subtotal)])
    if quote.discount_percent:
        rows.append(['', '', '', f'Discount ({float(quote.discount_percent):g}%)', f'- {money(quote.discount_amount)}'])
    if quote.tax_percent:
        rows.append(['', '', '', f'Tax ({float(quote.tax_percent):g}%)', money(quote.tax_amount)])
    if quote.shipping_amount:
        rows.append(['', '', '', 'Shipping', money(quote.shipping_amount)])
    rows.append(['', '', '', 'Grand total', money(quote.total)])

    table = Table(rows, colWidths=[62 * mm, 30 * mm, 24 * mm, 34 * mm, 34 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#234b3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.3, colors.HexColor('#dedfd7')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(table)

    if quote.notes:
        story.extend([Spacer(1, 8 * mm), Paragraph('<b>Notes</b>', styles['BodyText']), Paragraph(quote.notes, styles['BodyText'])])

    story.extend([Spacer(1, 12 * mm), Paragraph('Thank you for considering Furnivo.', styles['BodyText'])])
    doc.build(story)
    buffer.seek(0)
    return buffer
