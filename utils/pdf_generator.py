import os
import sys
import io
import urllib.request
from datetime import datetime
import pytz
import plotly.graph_objects as go

turkey_tz = pytz.timezone('Europe/Istanbul')
import plotly.io as pio
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
_ASSETS_DIR = os.path.join(_ROOT, 'assets')

# Official DejaVu 2.37 TTF bundle (single download; GitHub raw paths for individual TTFs are unreliable).
_DEJAVU_TARBALL_URL = (
    'https://downloads.sourceforge.net/project/dejavu/dejavu/2.37/dejavu-fonts-ttf-2.37.tar.bz2'
)
_DEJAVU_TAR_PREFIX = 'dejavu-fonts-ttf-2.37/ttf/'
_DEJAVU_FILES = ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf')


def _ensure_dejavu_fonts():
    os.makedirs(_ASSETS_DIR, exist_ok=True)
    paths = [os.path.join(_ASSETS_DIR, f) for f in _DEJAVU_FILES]
    if all(os.path.isfile(p) for p in paths):
        return
    import shutil
    import tarfile
    import tempfile

    fd, tmp_path = tempfile.mkstemp(suffix='.tar.bz2')
    os.close(fd)
    try:
        urllib.request.urlretrieve(_DEJAVU_TARBALL_URL, tmp_path)
        with tarfile.open(tmp_path, 'r:bz2') as archive:
            for fname in _DEJAVU_FILES:
                member_name = _DEJAVU_TAR_PREFIX + fname
                member = archive.getmember(member_name)
                source = archive.extractfile(member)
                dest = os.path.join(_ASSETS_DIR, fname)
                with open(dest, 'wb') as out:
                    shutil.copyfileobj(source, out)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _register_fonts():
    """Register DejaVu TTFs for Turkish (Unicode) text in PDFs."""
    try:
        _ensure_dejavu_fonts()
    except Exception:
        pass

    regular_path = os.path.join(_ASSETS_DIR, 'DejaVuSans.ttf')
    bold_path = os.path.join(_ASSETS_DIR, 'DejaVuSans-Bold.ttf')
    oblique_path = os.path.join(_ASSETS_DIR, 'DejaVuSans-Oblique.ttf')

    if not os.path.isfile(regular_path) or not os.path.isfile(bold_path):
        return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

    registered = set(pdfmetrics.getRegisteredFontNames())
    if 'DejaVu' not in registered:
        pdfmetrics.registerFont(TTFont('DejaVu', regular_path))
    if 'DejaVu-Bold' not in registered:
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', bold_path))
    if os.path.isfile(oblique_path) and 'DejaVu-Oblique' not in registered:
        pdfmetrics.registerFont(TTFont('DejaVu-Oblique', oblique_path))

    italic = 'DejaVu-Oblique' if os.path.isfile(oblique_path) else 'DejaVu'
    return 'DejaVu', 'DejaVu-Bold', italic

FONT_REGULAR, FONT_BOLD, FONT_ITALIC = _register_fonts()


def fig_to_image(fig, width=400, height=300):
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height)
        buf = io.BytesIO(img_bytes)
        buf.seek(0)
        return buf
    except Exception:
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
        font=dict(family="Arial", size=10),
        margin=dict(l=60, r=40, t=60, b=80)
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
        yaxis_title="Değer (TL)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial", size=10),
        legend=dict(x=0, y=1),
        margin=dict(l=60, r=40, t=60, b=80),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10))
    )
    return fig

def create_expense_bar_chart(category_totals: dict):
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=amounts,
        marker_color='#2E86AB',
        text=[f'{a:,.0f} TL' for a in amounts],
        textposition='auto',
    )])
    fig.update_layout(
        title="Harcama Kategorileri",
        xaxis_title="Kategori",
        yaxis_title="Tutar (TL)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Arial", size=10),
        margin=dict(l=60, r=40, t=60, b=80),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10))
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
        fontName=FONT_BOLD
    )
    style_subtitle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#16213E'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName=FONT_REGULAR
    )
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0F3460'),
        spaceBefore=12,
        spaceAfter=6,
        fontName=FONT_BOLD
    )
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=4,
        leading=14,
        fontName=FONT_REGULAR
    )
    style_warning = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName=FONT_ITALIC
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
    report_date = datetime.now(turkey_tz).strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(f"Hazırlayan: <b>{user_name}</b>", style_body))
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
        ['Aylık Gelir', f"{profile_data.get('monthly_income', 0):,.0f} TL"],
        ['Toplam Birikim', f"{profile_data.get('total_savings', 0):,.0f} TL"],
    ]

    profile_table = Table(profile_table_data, colWidths=[6*cm, 10*cm])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EBF5FB')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0F3460')),
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTNAME', (1, 0), (1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 0.8*cm))

    # --- PORTFÖY ÖNERİSİ ---
    story.append(Paragraph("2. Portföy Önerisi", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))

    try:
        pie_fig = go.Figure(data=[go.Pie(
            labels=list(portfolio.keys()),
            values=list(portfolio.values()),
            hole=0.3,
        )])
        pie_fig.update_layout(width=400, height=300, margin=dict(l=20, r=20, t=20, b=20))
        pie_img_bytes = pie_fig.to_image(format="png")
        story.append(Image(io.BytesIO(pie_img_bytes), width=300, height=225))
    except Exception:
        pass
    story.append(Spacer(1, 0.5*cm))

    portfolio_table_data = [['Yatırım Aracı', 'Ağırlık', 'Tahmini Yıllık Getiri']]
    from utils.calculations import EXPECTED_RETURNS
    for asset, weight in portfolio.items():
        ret = EXPECTED_RETURNS.get(asset, 0.20)
        portfolio_table_data.append([asset, f"%{weight*100:.0f}", f"%{ret*100:.0f}"])

    portfolio_table = Table(portfolio_table_data, colWidths=[7*cm, 5*cm, 5*cm])
    portfolio_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
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
        f"Hedeflediğiniz <b>{goal}</b> bugün <b>{current_goal:,.0f} TL</b> değerindedir. "
        f"Türkiye'deki yıllık ~%{inf_rate*100:.0f} enflasyon dikkate alındığında "
        f"{goal_years} yıl sonra yaklaşık <b>{real_goal:,.0f} TL</b> olması beklenmektedir.",
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
                f"Aylık <b>{expense_analysis['monthly_savings_potential']:,.0f} TL</b> tasarruf potansiyeli tespit edildi. "
                f"Yıllık tasarruf potansiyeli: <b>{expense_analysis['annual_savings_potential']:,.0f} TL</b>",
                style_body
            ))
        story.append(Spacer(1, 0.8*cm))

    # --- GEMİNİ TAVSİYELERİ ---
    story.append(Paragraph("5. Kişisel Tavsiyeler", style_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
    story.append(Spacer(1, 0.3*cm))
    advice_text = gemini_advice if gemini_advice else "Tavsiyeler şu an üretilemiyor."
    import re as _re
    # Strip markdown syntax (bold, italic, headers) for PDF rendering
    advice_clean = _re.sub(r'\*\*(.+?)\*\*', r'\1', advice_text)
    advice_clean = _re.sub(r'\*(.+?)\*', r'\1', advice_clean)
    advice_clean = _re.sub(r'^#{1,6}\s+', '', advice_clean, flags=_re.MULTILINE)
    # Split into paragraphs by blank lines
    advice_parts = [p.strip() for p in advice_clean.split('\n\n') if p.strip()]
    if not advice_parts:
        advice_parts = [advice_clean]
    for part in advice_parts:
        part_text = ' '.join(part.split('\n'))
        story.append(Paragraph(part_text, style_body))
        story.append(Spacer(1, 0.2*cm))
    story.append(Spacer(1, 0.8*cm))

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