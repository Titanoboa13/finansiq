import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from utils.calculations import apply_scenario, calculate_goal_probability
from utils.rag_system import get_rag_context

SCENARIO_DEFINITIONS = {
    "usd_increase": {
        "label": "Dolar Artışı",
        "description": "Dolar/TL kuru yükselirse",
        "unit": "% artış",
        "min": 5, "max": 50, "default": 20,
        "icon": "💵"
    },
    "bist_crash": {
        "label": "BIST Düşüşü",
        "description": "Borsa sert düşerse",
        "unit": "% düşüş",
        "min": 5, "max": 50, "default": 20,
        "icon": "📉"
    },
    "inflation_drop": {
        "label": "Enflasyon Düşüşü",
        "description": "Enflasyon gerilerse",
        "unit": "% düşüş",
        "min": 5, "max": 40, "default": 15,
        "icon": "📊"
    },
    "extra_monthly": {
        "label": "Ek Aylık Tasarruf",
        "description": "Her ay ek birikim yaparsam",
        "unit": "TL/ay",
        "min": 500, "max": 50000, "default": 2000,
        "icon": "💰"
    },
    "gold_increase": {
        "label": "Altın Artışı",
        "description": "Altın fiyatı yükselirse",
        "unit": "% artış",
        "min": 5, "max": 50, "default": 20,
        "icon": "🥇"
    },
}

def run_scenario_agent(
    scenario_type: str,
    scenario_value: float,
    portfolio: dict,
    profile_data: dict,
    base_projection: dict,
    api_key: str
) -> dict:

    total_savings = profile_data.get('total_savings', 0)
    goal_years = profile_data.get('goal_years', 5)
    real_goal = profile_data.get('real_goal_amount', 0)
    annual_return_base = sum(
        portfolio.get(asset, 0) * 0.35
        for asset in portfolio
    )
    communication_level = profile_data.get('communication_level', 'orta')

    # Senaryo hesapla
    scenario_result = apply_scenario(
        base_portfolio=portfolio,
        scenario_type=scenario_type,
        scenario_value=scenario_value,
        initial_savings=total_savings,
        years=goal_years
    )

    # Yeni olasılık hesapla
    new_probability = calculate_goal_probability(
        projected_value=scenario_result['final_value'],
        real_goal_amount=real_goal if real_goal > 0 else profile_data.get('goal_amount', 1),
        annual_return=scenario_result['modified_annual_return'],
        years=goal_years
    )

    base_final = base_projection.get('final_value', 0)
    new_final = scenario_result['final_value']
    change_amount = new_final - base_final
    change_percent = (change_amount / base_final * 100) if base_final > 0 else 0

    # RAG context
    scenario_def = SCENARIO_DEFINITIONS.get(scenario_type, {})
    rag_query = f"Türkiye'de {scenario_def.get('description', scenario_type)} durumunda yatırım stratejisi"
    rag_context = get_rag_context(rag_query)

    if communication_level == 'basit':
        style = "çok sade Türkçeyle, teknik terim kullanmadan, günlük hayattan örneklerle"
    elif communication_level == 'teknik':
        style = "teknik finansal terminolojiyle, sayısal analizle"
    else:
        style = "anlaşılır Türkçeyle"

    prompt = f"""
Sen FinansIQ'nun senaryo analiz uzmanısın. {style} yaz.

Senaryo: {scenario_def.get('description', scenario_type)} (%{scenario_value} / {scenario_value} TL)

Mevcut Portföy: {', '.join([f'{k}: %{v*100:.0f}' for k, v in portfolio.items()])}

Sonuçlar:
- Baz durum portföy değeri: {base_final:,.0f} TL
- Bu senaryoda portföy değeri: {new_final:,.0f} TL
- Değişim: {change_amount:+,.0f} TL (%{change_percent:+.1f})
- Hedefe ulaşma olasılığı: %{new_probability['probability']}

Finansal Bilgi:
{rag_context}

Bu senaryo gerçekleşirse portföye etkisini 3 cümleyle açıkla.
Ne yapılması gerektiğini öner.
Türkçe yaz.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        gemini_comment = response.text
    except Exception:
        gemini_comment = "Senaryo yorumu şu an üretilemiyor."

    return {
        "scenario_type": scenario_type,
        "scenario_value": scenario_value,
        "scenario_label": scenario_def.get('label', scenario_type),
        "base_final_value": base_final,
        "new_final_value": new_final,
        "change_amount": change_amount,
        "change_percent": change_percent,
        "new_probability": new_probability,
        "projection_by_year": scenario_result['projection_by_year'],
        "gemini_comment": gemini_comment
    }