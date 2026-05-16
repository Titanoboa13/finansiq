import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gemini_client import safe_generate
from utils.market_data import get_all_market_data
from database.db import save_alarm, get_market_cache, save_market_cache
import json
from datetime import datetime

THRESHOLDS = {
    "usd_try_spike": 2.0,
    "gold_spike": 3.0,
    "bist_crash": -3.0,
    "usd_try_high": 42.0,
    "usd_try_low": 35.0,
}

MOCK_NEWS_EVENTS = []

def check_price_changes(current_data: dict, previous_data: dict) -> list:
    alerts = []

    curr_usd = current_data.get('usd_try', {}).get('value', 0)
    prev_usd = previous_data.get('usd_try', 0)
    if prev_usd > 0 and curr_usd > 0:
        usd_change = ((curr_usd - prev_usd) / prev_usd) * 100
        if usd_change >= THRESHOLDS['usd_try_spike']:
            alerts.append({
                "type": "usd_spike",
                "severity": "high",
                "message": f"⚠️ Dolar/TL {usd_change:.1f}% artarak {curr_usd:.2f} TL oldu. "
                          f"Portföyündeki dolar ağırlığını simüle etmek ister misin?",
                "action": "simulate_usd"
            })
        elif usd_change <= -THRESHOLDS['usd_try_spike']:
            alerts.append({
                "type": "usd_drop",
                "severity": "medium",
                "message": f"ℹ️ Dolar/TL {abs(usd_change):.1f}% düştü. "
                          f"TL varlıklarını artırmayı değerlendirmek ister misin?",
                "action": "simulate_tl"
            })

    if curr_usd >= THRESHOLDS['usd_try_high']:
        alerts.append({
            "type": "usd_high",
            "severity": "high",
            "message": f"🚨 Dolar {curr_usd:.2f} TL ile yüksek seviyelerde. "
                      f"Portföyündeki TL mevduat ağırlığını gözden geçirmek ister misin?",
            "action": "review_tl_assets"
        })

    curr_gold = current_data.get('gold_gram_try', {}).get('value', 0)
    prev_gold = previous_data.get('gold_gram_try', 0)
    if prev_gold > 0 and curr_gold > 0:
        gold_change = ((curr_gold - prev_gold) / prev_gold) * 100
        if gold_change >= THRESHOLDS['gold_spike']:
            alerts.append({
                "type": "gold_spike",
                "severity": "medium",
                "message": f"🥇 Gram altın {gold_change:.1f}% artarak {curr_gold:.0f} TL oldu. "
                          f"Portföyündeki altın ağırlığını gözden geçirelim mi?",
                "action": "review_gold"
            })

    curr_bist = current_data.get('bist100', {}).get('value', 0)
    prev_bist = previous_data.get('bist100', 0)
    if prev_bist > 0 and curr_bist > 0:
        bist_change = ((curr_bist - prev_bist) / prev_bist) * 100
        if bist_change <= THRESHOLDS['bist_crash']:
            alerts.append({
                "type": "bist_crash",
                "severity": "high",
                "message": f"📉 BIST100 {abs(bist_change):.1f}% düştü. "
                          f"Hisse senedi pozisyonunu gözden geçirmek ister misin?",
                "action": "review_bist"
            })

    return alerts

def get_static_alerts(market_data: dict, profile_data: dict) -> list:
    alerts = []
    risk_profile = profile_data.get('risk_profile', 'Dengeli')
    curr_usd = market_data.get('usd_try', {}).get('value', 0)
    inflation = market_data.get('inflation_rate', {}).get('value', 0)
    tcmb_rate = market_data.get('tcmb_rate', {}).get('value', 0)
    fed_rate = market_data.get('fed_rate', {}).get('value', 0)

    if inflation > 50:
        alerts.append({
            "type": "high_inflation",
            "severity": "high",
            "message": f"🔥 Enflasyon %{inflation:.0f} seviyesinde. "
                      f"Enflasyona karşı korunma araçlarını portföyüne eklemek ister misin?",
            "action": "inflation_protection"
        })

    if tcmb_rate > 0 and fed_rate > 0:
        rate_diff = tcmb_rate - fed_rate
        if rate_diff > 30:
            alerts.append({
                "type": "rate_differential",
                "severity": "medium",
                "message": f"📊 TCMB faizi (%{tcmb_rate:.0f}) ile FED faizi (%{fed_rate:.1f}) "
                          f"arasındaki fark yüksek. Bu durum TL için carry trade fırsatı yaratabilir.",
                "action": "rate_analysis"
            })

    if risk_profile == "Muhafazakâr" and curr_usd > 40:
        alerts.append({
            "type": "conservative_usd_warning",
            "severity": "medium",
            "message": f"💡 Risk profilin 'Muhafazakâr'. Dolar {curr_usd:.2f} TL seviyesinde. "
                      f"Döviz pozisyonunu gözden geçirmek ister misin?",
            "action": "review_portfolio"
        })

    return alerts

def generate_alarm_message(alert: dict, api_key: str, communication_level: str = 'orta') -> str:
    if communication_level == 'basit':
        style = "çok sade ve anlaşılır Türkçeyle"
    else:
        style = "kısa ve net Türkçeyle"

    prompt = f"""
Sen FinansIQ'nun piyasa takip uzmanısın. {style} yaz.

Piyasa Alarmı: {alert['message']}

Bu alarmı kullanıcıya 2 cümleyle açıkla ve ne yapması gerektiğini söyle.
Panik yaratma, sakin ve bilgilendirici ol.
Türkçe yaz.
"""
    return safe_generate(
        prompt=prompt,
        fallback=alert['message']
    )

def run_market_watcher(user_id: int, profile_data: dict, api_key: str) -> list:
    current_data = get_all_market_data()
    cache_key = f"prev_market_{user_id}"
    prev_cache = get_market_cache(cache_key)

    new_alerts = []

    if prev_cache:
        try:
            prev_data = json.loads(prev_cache['data_value'])
            price_alerts = check_price_changes(current_data, prev_data)
            new_alerts.extend(price_alerts)
        except:
            pass

    static_alerts = get_static_alerts(current_data, profile_data)
    new_alerts.extend(static_alerts)

    cache_data = {
        "usd_try": current_data.get('usd_try', {}).get('value', 0),
        "eur_try": current_data.get('eur_try', {}).get('value', 0),
        "gold_gram_try": current_data.get('gold_gram_try', {}).get('value', 0),
        "bist100": current_data.get('bist100', {}).get('value', 0),
        "timestamp": datetime.now().isoformat()
    }
    save_market_cache(cache_key, json.dumps(cache_data))

    for alert in new_alerts:
        try:
            save_alarm(user_id, alert['type'], alert['message'])
        except:
            pass

    return new_alerts