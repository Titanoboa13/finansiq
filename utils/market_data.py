import yfinance as yf
import requests
import json
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import save_market_cache, get_market_cache

# --- FALLBACK DEĞERLERİ (API çalışmazsa bunlar kullanılır) ---
FALLBACK_DATA = {
    "usd_try": 38.50,
    "eur_try": 41.20,
    "gold_gram_try": 3850.0,
    "bist100": 9800.0,
    "tcmb_rate": 46.0,
    "inflation_rate": 65.0,
    "fed_rate": 4.50,
}

def _save_to_cache(key, value):
    try:
        save_market_cache(key, json.dumps({"value": value, "timestamp": datetime.now().isoformat()}))
    except:
        pass

def _get_from_cache(key):
    try:
        row = get_market_cache(key)
        if row:
            data = json.loads(row['data_value'])
            return data['value'], data['timestamp']
    except:
        pass
    return None, None

def _fetch_with_fallback(key, fetch_func):
    try:
        value = fetch_func()
        if value and value > 0:
            _save_to_cache(key, value)
            return value, "live"
    except Exception:
        pass
    cached_value, timestamp = _get_from_cache(key)
    if cached_value:
        return cached_value, f"cache:{timestamp}"
    return FALLBACK_DATA.get(key, 0), "fallback"

# --- USD/TRY ---
def get_usd_try():
    def fetch():
        ticker = yf.Ticker("USDTRY=X")
        data = ticker.fast_info
        return round(data.last_price, 2)
    return _fetch_with_fallback("usd_try", fetch)

# --- EUR/TRY ---
def get_eur_try():
    def fetch():
        ticker = yf.Ticker("EURTRY=X")
        data = ticker.fast_info
        return round(data.last_price, 2)
    return _fetch_with_fallback("eur_try", fetch)

# --- ALTIN (Gram/TRY) ---
def get_gold_gram_try():
    def fetch():
        gold_usd = yf.Ticker("GC=F").fast_info.last_price  # Ons altın USD
        usd_try, _ = get_usd_try()
        gram = (gold_usd / 31.1035) * usd_try  # Ons -> Gram dönüşümü
        return round(gram, 2)
    return _fetch_with_fallback("gold_gram_try", fetch)

# --- BIST100 ---
def get_bist100():
    def fetch():
        ticker = yf.Ticker("XU100.IS")
        data = ticker.fast_info
        return round(data.last_price, 2)
    return _fetch_with_fallback("bist100", fetch)

# --- TCMB FAİZ ORANI ---
def get_tcmb_rate():
    def fetch():
        url = "https://tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url, timeout=5)
        # TCMB XML'den faiz çekmek yerine sabit değer kullanıyoruz
        # Gerçek projede TCMB API entegrasyonu yapılabilir
        raise Exception("TCMB API direct fetch not implemented, using cache/fallback")
    return _fetch_with_fallback("tcmb_rate", fetch)

# --- ENFLASYON ---
def get_inflation_rate():
    def fetch():
        raise Exception("Using cache/fallback for inflation")
    return _fetch_with_fallback("inflation_rate", fetch)

# --- FED FAİZ ORANI ---
def get_fed_rate():
    def fetch():
        raise Exception("Using cache/fallback for FED rate")
    return _fetch_with_fallback("fed_rate", fetch)

# --- TÜM VERİLERİ TEK SEFERDE ÇEK ---
def get_all_market_data():
    usd, usd_source = get_usd_try()
    eur, eur_source = get_eur_try()
    gold, gold_source = get_gold_gram_try()
    bist, bist_source = get_bist100()
    tcmb, tcmb_source = get_tcmb_rate()
    inflation, inf_source = get_inflation_rate()
    fed, fed_source = get_fed_rate()

    data = {
        "usd_try": {"value": usd, "source": usd_source},
        "eur_try": {"value": eur, "source": eur_source},
        "gold_gram_try": {"value": gold, "source": gold_source},
        "bist100": {"value": bist, "source": bist_source},
        "tcmb_rate": {"value": tcmb, "source": tcmb_source},
        "inflation_rate": {"value": inflation, "source": inf_source},
        "fed_rate": {"value": fed, "source": fed_source},
        "fetched_at": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    return data

def get_data_status_message(market_data):
    sources = [v['source'] for k, v in market_data.items() if isinstance(v, dict) and 'source' in v]
    if all(s == "live" for s in sources):
        return None
    fallback_count = sum(1 for s in sources if s == "fallback")
    cache_count = sum(1 for s in sources if "cache" in str(s))
    if fallback_count > 0:
        return f"⚠️ {fallback_count} veri kaynağına ulaşılamıyor. Son bilinen veriler kullanılıyor."
    if cache_count > 0:
        return f"ℹ️ Bazı veriler önbellekten yüklendi. ({market_data.get('fetched_at', '')})"
    return None