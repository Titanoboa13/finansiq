# 💎 FinansIQ — Türkiye'nin Tarafsız Finansal Danışmanı

> BTK Akademi & Google & Girişimcilik Vakfı — Hackathon 2026

🌐 Canlı Demo: https://finansiq.streamlit.app

## 🎯 Proje Hakkında

FinansIQ, Türkiye'deki bireylerin enflasyon, kur krizi ve yüksek faiz ortamında doğru finansal kararlar almasına yardımcı olan yapay zeka destekli kişisel finansal danışman platformudur.

Hiçbir bankadan komisyon almaz. Yalnızca kullanıcının çıkarı için çalışır.

## 🚀 Özellikler

- **Kişisel Profil ve Risk Analizi** — Finansal okuryazarlık testi ile kişiye özel risk profili
- **Canlı Piyasa Verileri** — TCMB, FED, döviz, altın, BIST100 anlık takip
- **Enflasyon Düzeltmeli Hedef** — Gerçekçi hedef hesaplama (bugünkü değil, gelecekteki fiyat)
- **Portföy Önerisi** — Modern Portfolio Theory ile kişiye özel yatırım dağılımı
- **Senaryo Laboratuvarı** — "Dolar 50 TL olursa?" gibi senaryoları simüle et
- **Harcama Analizi** — CSV yükle veya manuel giriş ile harcama takibi
- **Proaktif Alarm Sistemi** — TCMB/FED kararlarında otomatik uyarı
- **Finansal Asistan** — RAG destekli Gemini tabanlı sohbet
- **PDF Rapor** — Grafik ve analizleri içeren profesyonel rapor

## 🤖 Teknik Mimari

- **LLM:** Google Gemini 2.5 Flash
- **Agent Framework:** LangGraph (5 Agent)
- **RAG:** LangChain + ChromaDB
- **Arayüz:** Streamlit
- **Veri:** yfinance, TCMB API
- **PDF:** ReportLab + Plotly + Kaleido
- **Veritabanı:** SQLite

## 🏗️ Kurulum

```bash
# Repoyu klonla
git clone https://github.com/Titanoboa13/finansiq.git
cd finansiq

# Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate

# Kütüphaneleri yükle
pip install -r requirements.txt

# API anahtarını ayarla
# .streamlit/secrets.toml dosyasına ekle:
# GEMINI_API_KEY = "your_api_key"

# Uygulamayı başlat
streamlit run app.py
```

## 📁 Proje Yapısı

finansiq/
├── agents/          # LangGraph agent'ları
├── pages/           # Streamlit sayfa bileşenleri
├── utils/           # Yardımcı modüller
├── database/        # SQLite veritabanı katmanı
├── data/            # Yerel veri depolama
└── app.py           # Ana uygulama

## 👤 Geliştirici

**Ergin Şen** — Data Scientist  
[LinkedIn](https://linkedin.com/in/ergin-sen) | [GitHub](https://github.com/Titanoboa13)

---
*BTK Akademi Hackathon 2026 — Finans / E-Ticaret Teması*


