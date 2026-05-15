import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from google import genai
from utils.calculations import analyze_expenses
from utils.rag_system import get_rag_context

EXPENSE_CATEGORIES = [
    "Market ve Gıda",
    "Kira ve Konut",
    "Faturalar ve Abonelikler",
    "Ulaşım",
    "Eğlence",
    "Sağlık",
    "Eğitim",
    "Diğer"
]

CATEGORY_KEYWORDS = {
    "Market ve Gıda": ["market", "migros", "bim", "a101", "şok", "carrefour", "yemek", "restoran", "kafe", "cafe", "burger", "pizza", "gıda", "manav", "kasap"],
    "Kira ve Konut": ["kira", "aidat", "site", "apartman", "konut", "emlak", "tadilat", "mobilya", "ikea"],
    "Faturalar ve Abonelikler": ["elektrik", "su", "doğalgaz", "internet", "telefon", "netflix", "spotify", "youtube", "fatura", "turkcell", "vodafone", "türk telekom"],
    "Ulaşım": ["akbil", "metrobüs", "metro", "otobüs", "taksi", "uber", "benzin", "akaryakıt", "otopark", "araç", "servis"],
    "Eğlence": ["sinema", "tiyatro", "konser", "oyun", "bar", "gece", "tatil", "otel", "seyahat", "uçak", "bilet"],
    "Sağlık": ["eczane", "ilaç", "doktor", "hastane", "klinik", "diş", "göz", "sağlık"],
    "Eğitim": ["kurs", "kitap", "okul", "üniversite", "dershane", "udemy", "eğitim", "öğrenim"],
}

def categorize_expense(description: str) -> str:
    description_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in description_lower for kw in keywords):
            return category
    return "Diğer"

def parse_csv_expenses(csv_file) -> list:
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(csv_file, encoding='latin-1')
        except:
            return []

    expenses = []
    amount_col = None
    desc_col = None
    date_col = None

    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['tutar', 'miktar', 'amount', 'fiyat', 'borc', 'borç']):
            amount_col = col
        if any(kw in col_lower for kw in ['açıklama', 'aciklama', 'description', 'islem', 'işlem', 'detay']):
            desc_col = col
        if any(kw in col_lower for kw in ['tarih', 'date', 'zaman']):
            date_col = col

    if amount_col is None and len(df.columns) >= 2:
        amount_col = df.columns[1]
    if desc_col is None and len(df.columns) >= 1:
        desc_col = df.columns[0]

    for _, row in df.iterrows():
        try:
            amount_raw = str(row[amount_col]).replace(',', '.').replace(' ', '').replace('₺', '').replace('TL', '')
            amount = abs(float(amount_raw))
            if amount <= 0:
                continue
            description = str(row[desc_col]) if desc_col else "Diğer"
            date = str(row[date_col]) if date_col else ""
            category = categorize_expense(description)
            expenses.append({
                "description": description,
                "amount": amount,
                "category": category,
                "date": date
            })
        except:
            continue

    return expenses

def run_expense_agent(
    expenses: list,
    profile_data: dict,
    api_key: str
) -> dict:

    monthly_income = profile_data.get('monthly_income', 0)
    communication_level = profile_data.get('communication_level', 'orta')

    # Harcama analizi
    analysis = analyze_expenses(expenses, monthly_income)

    # RAG context
    rag_context = get_rag_context("Türkiye'de kişisel bütçe yönetimi ve tasarruf yöntemleri")

    if communication_level == 'basit':
        style = "çok sade Türkçeyle, teknik terim kullanmadan"
    elif communication_level == 'teknik':
        style = "detaylı finansal analizle"
    else:
        style = "anlaşılır Türkçeyle"

    warnings_text = ""
    if analysis['warnings']:
        warnings_text = "\n".join([
            f"- {w['category']}: {w['spent']:,.0f} TL harcandı, önerilen maksimum {w['recommended_max']:,.0f} TL"
            for w in analysis['warnings']
        ])
    else:
        warnings_text = "Harcama dağılımı dengeli görünüyor."

    prompt = f"""
Sen FinansIQ'nun harcama analiz uzmanısın. {style} yaz.

Kullanıcının Harcama Analizi:
- Toplam harcama: {analysis['total_spent']:,.0f} TL
- Aylık gelir: {monthly_income:,.0f} TL
- Tasarruf oranı: %{analysis['savings_rate']}
- Aylık tasarruf potansiyeli: {analysis['monthly_savings_potential']:,.0f} TL

Dikkat Çeken Harcamalar:
{warnings_text}

Finansal Bilgi:
{rag_context}

Harcama alışkanlıkları hakkında 3-4 cümleyle değerlendirme yap.
Somut tasarruf önerileri sun.
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
        gemini_comment = "Harcama analizi yorumu şu an üretilemiyor."

    return {
        "analysis": analysis,
        "expenses": expenses,
        "gemini_comment": gemini_comment,
        "category_list": EXPENSE_CATEGORIES
    }