import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types

LITERACY_QUESTIONS = [
    {
        "id": 1,
        "question": "Merkez Bankası faiz oranlarını artırdığında hisse senetleri genellikle ne yönde hareket eder?",
        "options": ["A) Yükselir", "B) Düşer", "C) Değişmez", "D) Tahmin edilemez"],
        "correct": "B",
        "explanation": "Faiz artışı şirketlerin borçlanma maliyetini artırır ve yatırımcıları tahvil gibi sabit getirili araçlara yönlendirir. Bu nedenle hisse senetleri genellikle düşer."
    },
    {
        "id": 2,
        "question": "Enflasyon birikimini nasıl etkiler?",
        "options": ["A) Artırır", "B) Değiştirmez", "C) Reel değerini düşürür", "D) İkiye katlar"],
        "correct": "C",
        "explanation": "Enflasyon paranın satın alma gücünü azaltır. Birikiminizdeki nominal miktar aynı kalsa bile reel değeri düşer."
    },
    {
        "id": 3,
        "question": "Portföy çeşitlendirmesinin temel amacı nedir?",
        "options": ["A) Getiriyi maksimize etmek", "B) Riski azaltmak", "C) Vergi ödemekten kaçınmak", "D) Daha fazla hisse almak"],
        "correct": "B",
        "explanation": "Farklı varlık sınıflarına yatırım yaparak tek bir varlıktaki kayıpların tüm portföyü etkilemesi önlenir."
    },
    {
        "id": 4,
        "question": "Dolar/TL kuru yükseldiğinde ithalat maliyetleri ne olur?",
        "options": ["A) Düşer", "B) Değişmez", "C) Artar", "D) Yarıya iner"],
        "correct": "C",
        "explanation": "TL'nin değer kaybetmesi, dövizle yapılan ithalatı pahalılaştırır ve enflasyona katkıda bulunur."
    },
    {
        "id": 5,
        "question": "Tahvil ile hisse senedi arasındaki temel fark nedir?",
        "options": [
            "A) Tahvil daha yüksek getiri sağlar",
            "B) Tahvil sabit getiri sunar, hisse senedi değişken",
            "C) İkisi aynı şeydir",
            "D) Hisse senedi daha güvenlidir"
        ],
        "correct": "B",
        "explanation": "Tahvil belirli bir faiz oranıyla borç senedidir. Hisse senedi ise şirkete ortak olmaktır ve getirisi değişkendir."
    },
    {
        "id": 6,
        "question": "FED (ABD Merkez Bankası) faiz artırdığında Türkiye'ye etkisi ne olur?",
        "options": [
            "A) TL değer kazanır",
            "B) Dolar güçlenir, TL değer kaybedebilir",
            "C) Türkiye etkilenmez",
            "D) Altın fiyatı düşer"
        ],
        "correct": "B",
        "explanation": "FED faiz artışı doları güçlendirir. Güçlü dolar gelişen piyasalardan sermaye çıkışına ve TL'nin değer kaybetmesine yol açabilir."
    },
    {
        "id": 7,
        "question": "Altın neden güvenli liman olarak görülür?",
        "options": [
            "A) Her zaman değer kazanır",
            "B) Devlet güvencesi vardır",
            "C) Küresel belirsizlik dönemlerinde değerini korur",
            "D) Faiz geliri sağlar"
        ],
        "correct": "C",
        "explanation": "Altın, hiçbir ülkenin para birimine bağlı olmadığı için kriz dönemlerinde yatırımcıların sığındığı güvenli bir değer deposudur."
    },
    {
        "id": 8,
        "question": "Bileşik faiz nedir?",
        "options": [
            "A) İki bankadan aynı anda faiz almak",
            "B) Faizin üzerine tekrar faiz işlemesi",
            "C) Sabit oranlı faiz",
            "D) Devlet tarafından belirlenen faiz"
        ],
        "correct": "B",
        "explanation": "Bileşik faizde kazanılan faiz ana paraya eklenir ve bir sonraki dönem daha büyük tutar üzerinden faiz hesaplanır. Uzun vadede güçlü servet artışı sağlar."
    },
    {
        "id": 9,
        "question": "Acil durum fonu ne kadar olmalıdır?",
        "options": [
            "A) 1 aylık gider",
            "B) 3-6 aylık gider",
            "C) 1 yıllık gider",
            "D) 10 yıllık gider"
        ],
        "correct": "B",
        "explanation": "Finansal uzmanlar beklenmedik durumlar için 3-6 aylık gideri karşılayacak likit bir acil durum fonu bulundurmayı önerir."
    },
    {
        "id": 10,
        "question": "DCA (Düzenli Maliyet Ortalaması) stratejisi nedir?",
        "options": [
            "A) Tüm parayı tek seferde yatırmak",
            "B) Her ay sabit miktarda yatırım yapmak",
            "C) Sadece düşüşte almak",
            "D) Sadece yüksekte satmak"
        ],
        "correct": "B",
        "explanation": "DCA stratejisinde her ay sabit miktar yatırılır. Bu yöntem piyasa zamanlaması riskini azaltır ve uzun vadede maliyet ortalamasını dengeler."
    }
]

def calculate_literacy_score(answers: dict) -> dict:
    correct_count = 0
    results = []

    for q in LITERACY_QUESTIONS:
        qid = str(q['id'])
        user_answer = answers.get(qid, "").upper()
        is_correct = user_answer == q['correct']
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": q['id'],
            "question": q['question'],
            "user_answer": user_answer,
            "correct_answer": q['correct'],
            "is_correct": is_correct,
            "explanation": q['explanation']
        })

    score = correct_count
    if score <= 3:
        risk_profile = "Muhafazakâr"
        communication_level = "basit"
        level_desc = "Başlangıç"
    elif score <= 6:
        risk_profile = "Dengeli"
        communication_level = "orta"
        level_desc = "Orta"
    else:
        risk_profile = "Agresif"
        communication_level = "teknik"
        level_desc = "İleri"

    return {
        "score": score,
        "total": len(LITERACY_QUESTIONS),
        "correct_count": correct_count,
        "risk_profile": risk_profile,
        "communication_level": communication_level,
        "level_description": level_desc,
        "results": results
    }

def get_profile_summary_prompt(profile_data: dict, communication_level: str) -> str:
    if communication_level == "basit":
        style = "çok sade ve anlaşılır bir dille, teknik terimler kullanmadan"
    elif communication_level == "orta":
        style = "açık ve anlaşılır bir dille, temel finansal terimleri kullanarak"
    else:
        style = "teknik ve detaylı bir dille, finansal terminolojiyi kullanarak"

    return f"""
Sen FinansIQ'nun finansal danışmanısın. Kullanıcının profilini {style} değerlendir.

Kullanıcı Profili:
- Risk Profili: {profile_data.get('risk_profile')}
- Finansal Okuryazarlık: {profile_data.get('literacy_score')}/10
- Aylık Gelir: {profile_data.get('monthly_income', 0):,.0f} TL
- Aylık Gider: {profile_data.get('monthly_expenses', 0):,.0f} TL
- Toplam Birikim: {profile_data.get('total_savings', 0):,.0f} TL
- Finansal Hedef: {profile_data.get('financial_goal')}
- Hedef Süresi: {profile_data.get('goal_years')} yıl

3-4 cümleyle profilin güçlü yönlerini ve dikkat edilmesi gereken noktaları belirt.
Türkçe yaz.
"""

def run_profile_agent(profile_data: dict, api_key: str) -> str:
    try:
        client = genai.Client(api_key=api_key)
        communication_level = profile_data.get('communication_level', 'orta')
        prompt = get_profile_summary_prompt(profile_data, communication_level)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Profil analizi şu an yapılamıyor. Lütfen tekrar deneyin."