import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- FİNANSAL BİLGİ TABANI ---
FINANCIAL_KNOWLEDGE_BASE = """
# TÜRKİYE FİNANSAL REHBERİ

## TCMB VE PARA POLİTİKASI
Türkiye Cumhuriyet Merkez Bankası (TCMB), para politikasını belirleyen temel kurumdur.
Politika faizi, enflasyonla mücadelede ana araçtır. Faiz artışı enflasyonu düşürür ancak büyümeyi yavaşlatır.
Faiz artışı hisse senetlerini olumsuz, tahvil ve mevduatı olumlu etkiler.
Faiz indirimi ise büyümeyi destekler, borçlanmayı ucuzlatır ancak enflasyon riskini artırır.
TCMB'nin bağımsızlığı, piyasa güveni açısından kritik öneme sahiptir.

## FED VE KÜRESEL ETKİ
ABD Merkez Bankası (FED) kararları Türkiye'yi doğrudan etkiler.
FED faiz artışı → Dolar güçlenir → Dolar/TL yükselir → Türkiye'de ithalat pahalanır → Enflasyon artar.
FED faiz indirimi → Gelişen piyasalara para akışı artar → TL değer kazanabilir.
FED kararları sonrası dolar/TL genellikle 2-3 hafta içinde %2-5 hareket eder.
FOMC toplantıları yılda 8 kez yapılır ve küresel piyasaları etkiler.

## ENFLASYON VE KORUNMA YÖNTEMLERİ
Türkiye'de enflasyon son yıllarda yüksek seyretmiştir.
Enflasyona karşı en etkili korunma araçları: altın, döviz, gayrimenkul ve BIST hisseleri.
Mevduat faizi enflasyonun altında kalırsa reel kayıp oluşur.
Enflasyon dönemlerinde nakit tutmak değer kaybına yol açar.
TL mevduat yerine döviz mevduatı veya altın hesabı tercih edilebilir.

## ALTIN YATIRIMI
Altın, küresel belirsizlik dönemlerinde güvenli liman olarak görülür.
Türkiye'de gram altın fiyatı hem ons altın fiyatından hem de dolar/TL kurundan etkilenir.
Altın birikimde fiziksel, gram altın hesabı veya altın fonu seçenekleri mevcuttur.
Uzun vadede altın enflasyona karşı koruma sağlar.
Altın yatırımında likidite yüksektir, hızla nakde çevrilebilir.

## DÖVİZ YATIRIMI
Döviz tutmak TL'nin değer kaybına karşı koruma sağlar.
Dolar ve Euro en likit döviz araçlarıdır.
Döviz hesabı, dövizli mevduat veya döviz fonu seçenekleri mevcuttur.
Kur riski çift yönlüdür: TL değer kazanırsa döviz yatırımı zarar edebilir.
Portföyde döviz ağırlığı risk profiline göre belirlenmelidir.

## BORSA İSTANBUL (BIST)
BIST100, Türkiye'nin en büyük 100 şirketinin hisselerinden oluşan endekstir.
Hisse senedi yatırımı uzun vadede enflasyonun üzerinde getiri potansiyeli sunar.
Kısa vadede yüksek volatilite riski taşır.
Faiz artışları genellikle borsa için olumsuz, faiz indirimleri olumludur.
Sektör çeşitlendirmesi riski azaltır.
Temettü hisseleri düzenli gelir sağlar.

## DEVLET TAHVİLİ VE BONO
Devlet tahvilleri düşük riskli, sabit getirili yatırım araçlarıdır.
Faiz oranları yükselince tahvil fiyatları düşer, faizler düşünce tahvil fiyatları yükselir.
Enflasyona endeksli tahviller (TÜFE+) enflasyona karşı koruma sağlar.
Eurobond: döviz cinsinden devlet tahvili, kur riskini azaltır.

## MEVDUAT VE FAİZ
TL mevduat, bankalarda belirli süre için tutulan paradır.
Mevduat faizi TCMB politika faizine paralel hareket eder.
BDDK güvencesi kapsamında 250.000 TL'ye kadar mevduat güvence altındadır.
Enflasyonun altında kalan mevduat faizi reel kayba yol açar.
Katılım bankası hesapları faizsiz alternatif sunar.

## KRİPTO PARA RİSKLERİ
Kripto paralar yüksek volatiliteye sahip spekülatif yatırım araçlarıdır.
Bitcoin, Ethereum gibi kripto paralar %80'e varan değer kayıpları yaşayabilir.
Türkiye'de kripto para alım satımından elde edilen kazançlar vergilendirilmektedir.
Kripto yatırımı toplam portföyün %5-10'unu geçmemelidir.
Merkezi olmayan yapısı hem avantaj hem risk taşır.

## VERGİ BİLGİSİ
Hisse senedi alım satım kazancı: 2 yıldan uzun elde tutulursa vergiden muaf.
Temettü geliri: %15 stopaj vergisine tabidir.
Mevduat faizi: %10-15 stopaj vergisine tabidir.
Altın alım satım kazancı: Belirli koşullarda vergiden muaf olabilir.
Döviz alım satım kazancı: Beyan yükümlülüğü bulunmaktadır.

## PORTFÖY YÖNETİMİ İLKELERİ
Çeşitlendirme: Tek bir yatırım aracına bağlı kalmamak riski azaltır.
Modern Portföy Teorisi: Farklı korelasyona sahip varlıkları bir arada tutmak toplam riski düşürür.
Düzenli yatırım (DCA): Her ay sabit miktarda yatırım yapmak maliyet ortalamasını düşürür.
Uzun vade: Kısa vadeli dalgalanmalara aldırış etmeden uzun vadeli tutmak getiriyi artırır.
Risk profili: Yatırım kararları kişinin risk toleransına uygun olmalıdır.

## KONUT YATIRIMI
Türkiye'de konut fiyatları son yıllarda yüksek enflasyon yaşamıştır.
Konut alımında kredi kullanımı aylık taksit yükü yaratır.
Kira getirisi genellikle konut değerinin %3-5'i civarındadır.
Konut likiditesi düşüktür, hızla nakde çevrilemez.
Büyükşehirlerde konut fiyatları daha hızlı artmaktadır.

## KİŞİSEL FİNANS İPUÇLARI
Acil durum fonu: 3-6 aylık gideri karşılayacak nakit rezerv bulundurulmalıdır.
Bütçe kuralı 50/30/20: Gelirin %50'si ihtiyaçlar, %30'u istekler, %20'si tasarruf.
Bileşik faiz: Uzun vadede en güçlü servet artırma aracıdır.
Borç yönetimi: Yüksek faizli borçları öncelikle kapatmak finansal sağlık için kritiktir.
Sigorta: Hayat, sağlık ve kasko sigortaları finansal risklere karşı koruma sağlar.
"""

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    api_key = os.getenv("GEMINI_API_KEY") or ""
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            pass

    

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n", " "]
    )
    chunks = splitter.split_text(FINANCIAL_KNOWLEDGE_BASE)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )

    persist_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')
    os.makedirs(persist_dir, exist_ok=True)

    _vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )

    return _vectorstore

def query_knowledge_base(query: str, k: int = 3) -> str:
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
    except Exception as e:
        return "Finansal bilgi tabanına şu an ulaşılamıyor."

def get_rag_context(query: str) -> str:
    return query_knowledge_base(query)