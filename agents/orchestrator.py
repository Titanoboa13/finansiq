import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from utils.rag_system import get_rag_context
from utils.market_data import get_all_market_data

RISK_KEYWORDS = [
    "kripto", "bitcoin", "ethereum", "tüm param", "bütün param",
    "hepsini", "tek hisse", "borç al", "kredi çek", "mortgage",
    "kaldıraç", "leverage", "margin"
]

def detect_risk(message: str) -> bool:
    message_lower = message.lower()
    return any(kw in message_lower for kw in RISK_KEYWORDS)

def get_risk_education_prompt(message: str, communication_level: str) -> str:
    if communication_level == 'basit':
        style = "çok sade Türkçeyle, teknik terim kullanmadan"
    else:
        style = "anlaşılır Türkçeyle"

    return f"""
Sen FinansIQ'nun finansal koç ve risk uzmanısın. {style} yaz.

Kullanıcı şunu söyledi: "{message}"

Bu yüksek riskli bir finansal karar içeriyor.
Kullanıcıyı eğit ve uyar. Şunları yap:
1. Riskleri 2-3 cümleyle açıkla
2. Alternatif bir yaklaşım öner
3. "Yine de simüle etmemi ister misin?" diye sor

Paternalist olma, kullanıcıya saygılı davran.
Türkçe yaz.
"""

def run_chat_agent(
    message: str,
    chat_history: list,
    profile_data: dict,
    market_data: dict,
    api_key: str
) -> dict:

    communication_level = profile_data.get('communication_level', 'orta')
    risk_profile = profile_data.get('risk_profile', 'Dengeli')
    is_risky = detect_risk(message)

    # RAG context çek
    rag_context = get_rag_context(message)

    if communication_level == 'basit':
        style = "çok sade Türkçeyle, günlük hayattan örneklerle, teknik terim kullanmadan"
    elif communication_level == 'teknik':
        style = "teknik finansal terminolojiyle, sayısal analizle"
    else:
        style = "anlaşılır Türkçeyle"

    if is_risky:
        prompt = get_risk_education_prompt(message, communication_level)
    else:
        history_text = ""
        if chat_history:
            recent = chat_history[-6:]
            history_text = "\n".join([
                f"{'Kullanıcı' if m['role'] == 'user' else 'FinansIQ'}: {m['content']}"
                for m in recent
            ])

        prompt = f"""
Sen FinansIQ'nun finansal danışmanısın. {style} yaz.
Sadece Türkiye finansal piyasaları ve kişisel finans konularında yardım et.
Finans dışı konularda kibarca konu dışı olduğunu belirt.

Kullanıcı Profili:
- Risk Profili: {risk_profile}
- İletişim Seviyesi: {communication_level}
- Aylık Gelir: {profile_data.get('monthly_income', 0):,.0f} TL
- Toplam Birikim: {profile_data.get('total_savings', 0):,.0f} TL
- Hedef: {profile_data.get('financial_goal', '-')}

Güncel Piyasa:
- USD/TL: {market_data.get('usd_try', {}).get('value', '-')}
- Altın: {market_data.get('gold_gram_try', {}).get('value', '-')} TL/gram
- BIST100: {market_data.get('bist100', {}).get('value', '-')}
- TCMB Faiz: %{market_data.get('tcmb_rate', {}).get('value', '-')}
- Enflasyon: %{market_data.get('inflation_rate', {}).get('value', '-')}

Finansal Bilgi Tabanı:
{rag_context}

Sohbet Geçmişi:
{history_text}

Kullanıcının Sorusu: {message}

Kısa, net ve yardımcı bir yanıt ver. Türkçe yaz.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        reply = response.text
    except Exception as e:
        reply = "Şu an yanıt üretemiyorum. Lütfen tekrar deneyin."

    return {
        "reply": reply,
        "is_risky": is_risky,
        "rag_used": bool(rag_context)
    }

def generate_financial_advice(profile_data: dict, portfolio_result: dict, api_key: str) -> str:
    communication_level = profile_data.get('communication_level', 'orta')

    if communication_level == 'basit':
        style = "çok sade Türkçeyle"
    elif communication_level == 'teknik':
        style = "teknik finansal terminolojiyle"
    else:
        style = "anlaşılır Türkçeyle"

    goal_prob = portfolio_result.get('goal_probability', {})
    portfolio = portfolio_result.get('portfolio', {})

    prompt = f"""
Sen FinansIQ'nun baş finansal danışmanısın. {style} yaz.

Kullanıcı Özeti:
- Risk Profili: {profile_data.get('risk_profile')}
- Hedef: {profile_data.get('financial_goal')} - {profile_data.get('goal_amount', 0):,.0f} TL
- Süre: {profile_data.get('goal_years')} yıl
- Hedefe ulaşma olasılığı: %{goal_prob.get('probability', 0)}
- Aylık ek tasarruf ihtiyacı: {goal_prob.get('monthly_extra_needed', 0):,.0f} TL

Portföy: {', '.join([f'{k}: %{v*100:.0f}' for k, v in portfolio.items()])}

Bu kullanıcıya özel 4-5 maddelik kişisel finansal tavsiye listesi oluştur.
Her madde somut ve uygulanabilir olsun.
Türkçe yaz.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception:
        return "Kişisel tavsiyeler şu an üretilemiyor."