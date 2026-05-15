import os
import sys
import io
import base64
from datetime import datetime
import plotly.graph_objects as go
import plotly.io as pio
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fig_to_image(fig, width=400, height=300):
    try:
        img_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=2)
        return io.BytesIO(img_bytes)
    except Exception as e:
        return None

def create_portfolio_pie_chart(portfolio: dict):
    labels = list(portfolio.keys())
    values = [v * 100 for v in portfolio.values()]
    colors_list = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=colors_list),
        textinfo='label+percent',
        textfont_size=12,
    )])
    fig.update_layout(
        title="Portföy Dağılımı",
        showlegend=True,
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial", size=11),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def create_projection_chart(projection_data: list, goal_amount: float, goal_type: str):
    years = [p['year'] for p in projection_data]
    values = [p['value'] for p in projection_data]
    goal_line = [goal_amount] * len(years)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode='lines+markers',
        name='Portföy Projeksiyonu',
        line=dict(color='#2ECC71', width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=years, y=goal_line,
        mode='lines',
        name=f'Hedef ({goal_type})',
        line=dict(color='#E74C3C', width=2, dash='dash')
    ))
    fig.update_layout(
        title="5 Yıllık Birikim Projeksiyonu",
        xaxis_title="Yıl",
        yaxis_title="Değer (₺)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial", size=11),
        legend=dict(x=0, y=1),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def create_expense_bar_chart(category_totals: dict):
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=amounts,
        marker_color='#2E86AB',
        text=[f'{a:,.0f} ₺' for a in amounts],
        textposition='auto',
    )])
    fig.update_layout(
        title="Harcama Kategorileri",
        xaxis_title="Kategori",
        yaxis_title="Tutar (₺)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial", size=10),
        margin=dict(l=20, r=20, t=40, b=80),
        xaxis=dict(tickangle=-30)
    )
    return fig

def generate_pdf_report(
    user_data: dict,
    profile_data: dict,
    portfolio: dict,
    projection_data: list,
    goal_analysis: dict,
    expense_analysis: dict,
    gemini_advice: str,
    output_path: str = None
) -> bytes:

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1A1A2E'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    style_subtitle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#16213E'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0F3460'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=4,
        leading=14,
        fontName='Helvetica'
    )
    style_warning = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    story = []

    # --- KAPAK ---
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("FinansIQ", style_title))
    story.append(Paragraph("Kişisel Finansal Danışman Raporu", style_subtitle))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0F3460')))
    story.append(Spacer(1, 0.3*cm))

    user_name = f"{user_data.get('name', '')} {user_data.get('surname', '')}"
    report_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(f"Hazırlanan: <b>{user_name}</b>", style_body))
    story.append(Paragraph(f"Tarih: {report_date}", style_body))
    story.append(Spacer(1, 1*cm))

    # --- PROFİL ÖZETİ ---
    story.append(Paragraph("1. Finansal Profil", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))

    risk_profile = profile_data.get('risk_profile', 'Dengeli')
    literacy_score = profile_data.get('literacy_score', 0)
    goal = profile_data.get('financial_goal', '-')
    goal_years = profile_data.get('goal_years', 0)

    profile_table_data = [
        ['Risk Profili', risk_profile],
        ['Finansal Okuryazarlık Skoru', f"{literacy_score}/10"],
        ['Finansal Hedef', goal],
        ['Hedef Süresi', f"{goal_years} yıl"],
        ['Aylık Gelir', f"{profile_data.get('monthly_income', 0):,.0f} ₺"],
        ['Toplam Birikim', f"{profile_data.get('total_savings', 0):,.0f} ₺"],
    ]

    profile_table = Table(profile_table_data, colWidths=[6*cm, 10*cm])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EBF5FB')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0F3460')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 0.8*cm))

    # --- PORTFÖy ÖNERİSİ ---
    story.append(Paragraph("2. Portföy Önerisi", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))

    pie_fig = create_portfolio_pie_chart(portfolio)
    pie_img = fig_to_image(pie_fig, width=500, height=320)
    if pie_img:
        story.append(Image(pie_img, width=14*cm, height=9*cm))
    story.append(Spacer(1, 0.5*cm))

    portfolio_table_data = [['Yatırım Aracı', 'Ağırlık', 'Tahmini Yıllık Getiri']]
    from utils.calculations import EXPECTED_RETURNS
    for asset, weight in portfolio.items():
        ret = EXPECTED_RETURNS.get(asset, 0.30)
        portfolio_table_data.append([asset, f"%{weight*100:.0f}", f"%{ret*100:.0f}"])

    portfolio_table = Table(portfolio_table_data, colWidths=[7*cm, 5*cm, 5*cm])
    portfolio_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(portfolio_table)
    story.append(Spacer(1, 0.8*cm))

    # --- HEDEF ANALİZİ ---
    story.append(Paragraph("3. Hedef Analizi", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))

    real_goal = goal_analysis.get('future_amount', 0)
    current_goal = goal_analysis.get('current_amount', 0)
    inf_rate = goal_analysis.get('inflation_rate', 0)

    story.append(Paragraph(
        f"Hedeflediğiniz <b>{goal}</b> bugün <b>{current_goal:,.0f} ₺</b> değerindedir. "
        f"Türkiye'deki yıllık ~%{inf_rate*100:.0f} enflasyon dikkate alındığında "
        f"{goal_years} yıl sonra yaklaşık <b>{real_goal:,.0f} ₺</b> olması beklenmektedir.",
        style_body
    ))
    story.append(Spacer(1, 0.3*cm))

    if projection_data:
        proj_fig = create_projection_chart(projection_data, real_goal, goal)
        proj_img = fig_to_image(proj_fig, width=550, height=300)
        if proj_img:
            story.append(Image(proj_img, width=15*cm, height=8*cm))
    story.append(Spacer(1, 0.8*cm))

    # --- HARCAMA ANALİZİ ---
    if expense_analysis and expense_analysis.get('category_totals'):
        story.append(Paragraph("4. Harcama Analizi", style_heading))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
        story.append(Spacer(1, 0.3*cm))

        exp_fig = create_expense_bar_chart(expense_analysis['category_totals'])
        exp_img = fig_to_image(exp_fig, width=550, height=300)
        if exp_img:
            story.append(Image(exp_img, width=15*cm, height=8*cm))

        if expense_analysis.get('monthly_savings_potential', 0) > 0:
            story.append(Paragraph(
                f"Aylık <b>{expense_analysis['monthly_savings_potential']:,.0f} ₺</b> tasarruf potansiyeli tespit edildi. "
                f"Yıllık tasarruf potansiyeli: <b>{expense_analysis['annual_savings_potential']:,.0f} ₺</b>",
                style_body
            ))
        story.append(Spacer(1, 0.8*cm))

    # --- GEMİNİ TAVSİYELERİ ---
    story.append(Paragraph("5. Kişisel Tavsiyeler", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(gemini_advice, style_body))
    story.append(Spacer(1, 1*cm))

    # --- YASAL UYARI ---
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Bu rapor yatırım tavsiyesi niteliği taşımamaktadır. "
        "Yatırım kararlarınızı vermeden önce lisanslı bir finansal danışmana başvurmanız önerilir. "
        f"FinansIQ tarafından {report_date} itibarıyla hazırlanmıştır.",
        style_warning
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

    return pdf_bytes