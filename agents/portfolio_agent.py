import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from utils.calculations import (
    get_portfolio_for_profile,
    calculate_portfolio_return,
    calculate_projection,
    calculate_real_goal_amount,
    calculate_goal_probability
)
from utils.market_data import get_all_market_data
from utils.rag_system import get_rag_context

def run_portfolio_agent(profile_data: dict, api_key: str) -> dict:
    with_status = []

    # Adım 1: Piyasa verisi
    with_status.append("📊 Piyasa verileri çekiliyor...")
    market_data = get_all_market_data()

    # Adım 2: Portföy dağılımı
    with_status.append("💼 Portföy analiz ediliyor...")
    risk_profile = profile_data.get('risk_profile', 'Dengeli')
    portfolio = get_portfolio_for_profile(risk_profile)
    annual_return = calculate_portfolio_return(portfolio)

    # Adım 3: Enflasyon düzeltmeli hedef
    with_status.append("🎯 Hedef analizi yapılıyor...")
    goal_amount = profile_data.get('goal_amount', 0)
    goal_type = profile_data.get('financial_goal', 'diğer')
    goal_years = profile_data.get('goal_years', 5)
    total_savings = profile_data.get('total_savings', 0)
    monthly_income = profile_data.get('monthly_income', 0)
    monthly_expenses = profile_data.get('monthly_expenses', 0)
    monthly_contribution = max(0, monthly_income - monthly_expenses) * 0.5

    goal_analysis = calculate_real_goal_amount(goal_amount, goal_type, goal_years)
    real_goal = goal_analysis['future_amount']

    # Adım 4: Projeksiyon
    with_status.append("📈 Projeksiyon hesaplanıyor...")
    projection = calculate_projection(
        initial_savings=total_savings,
        monthly_contribution=monthly_contribution,
        annual_return=annual_return,
        years=goal_years
    )

    # Adım 5: Hedef olasılığı
    goal_probability = calculate_goal_probability(
        projected_value=projection['final_value'],
        real_goal_amount=real_goal,
        annual_return=annual_return,
        years=goal_years
    )

    # Adım 6: RAG + Gemini açıklama
    with_status.append("🤖 Gemini öneriler üretiyor...")
    rag_context = get_rag_context(f"Türkiye'de {risk_profile} risk profiline uygun portföy önerisi")

    communication_level = profile_data.get('communication_level', 'orta')
    if communication_level == 'basit':
        style = "çok sade Türkçeyle, teknik terim kullanmadan"
    elif communication_level == 'teknik':
        style = "teknik finansal terminolojiyle detaylı olarak"
    else:
        style = "anlaşılır Türkçeyle"

    prompt = f"""
Sen FinansIQ'nun portföy danışmanısın. {style} yaz.

Kullanıcı Profili:
- Risk Profili: {risk_profile}
- Toplam Birikim: {total_savings:,.0f} TL
- Hedef: {goal_type} - {goal_amount:,.0f} TL (bugünkü değer)
- Enflasyon düzeltmeli gerçek hedef: {real_goal:,.0f} TL
- Süre: {goal_years} yıl
- Hedefe ulaşma olasılığı: %{goal_probability['probability']}

Önerilen Portföy Dağılımı:
{chr(10).join([f"- {k}: %{v*100:.0f}" for k, v in portfolio.items()])}

Finansal Bilgi Tabanı:
{rag_context}

Güncel Piyasa:
- USD/TL: {market_data['usd_try']['value']}
- Altın: {market_data['gold_gram_try']['value']} TL/gram
- BIST100: {market_data['bist100']['value']}

Bu portföy dağılımını neden önerdiğini 4-5 cümleyle açıkla.
Her yatırım aracı için kısa bir gerekçe ver.
Türkçe yaz.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        gemini_explanation = response.text
    except Exception as e:
        gemini_explanation = f"Portföy açıklaması şu an üretilemiyor. Hata: {str(e)}"

    return {
        "portfolio": portfolio,
        "annual_return": annual_return,
        "market_data": market_data,
        "goal_analysis": goal_analysis,
        "projection": projection,
        "goal_probability": goal_probability,
        "gemini_explanation": gemini_explanation,
        "monthly_contribution": monthly_contribution,
        "status_steps": with_status
    }