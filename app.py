import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, register_user, login_user, get_profile

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="FinansIQ",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VERİTABANI BAŞLAT ---
init_db()

# --- SESSION STATE BAŞLAT ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'portfolio_result' not in st.session_state:
    st.session_state.portfolio_result = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'market_data' not in st.session_state:
    st.session_state.market_data = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# --- API KEY ---
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

# --- STİL ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 2rem;
        margin: 0;
        font-weight: 800;
    }
    .main-header p {
        color: #A0AEC0;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-card .value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1A1A2E;
    }
    .metric-card .label {
        font-size: 0.75rem;
        color: #718096;
        margin-top: 0.2rem;
    }
    .alarm-card {
        background: #FFF8E1;
        border-left: 4px solid #F6AD55;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .alarm-card.high {
        background: #FFF5F5;
        border-left-color: #FC8181;
    }
    .success-card {
        background: #F0FFF4;
        border-left: 4px solid #68D391;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] {
        background: #1A1A2E;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- GİRİŞ / KAYIT SAYFASI ---
def show_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size:3rem; color:#0F3460; font-weight:900;'>💎 FinansIQ</h1>
            <p style='color:#718096; font-size:1.1rem;'>Türkiye'nin Tarafsız Finansal Danışmanı</p>
            <p style='color:#A0AEC0; font-size:0.85rem;'>Hiçbir bankadan komisyon almıyoruz. Sadece senin çıkarın için çalışıyoruz.</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

        with tab_login:
            st.markdown("### Hoş Geldin")
            email = st.text_input("E-posta", key="login_email", placeholder="ornek@email.com")
            password = st.text_input("Şifre", type="password", key="login_password", placeholder="••••••••")

            if st.button("Giriş Yap", use_container_width=True, type="primary", key="login_btn"):
                if email and password:
                    result = login_user(email, password)
                    if result['success']:
                        st.session_state.user = result['user']
                        profile = get_profile(result['user']['id'])
                        st.session_state.profile = profile
                        st.session_state.page = 'dashboard' if profile else 'profile_setup'
                        st.rerun()
                    else:
                        st.error(result['error'])
                else:
                    st.warning("Lütfen tüm alanları doldurun.")

        with tab_register:
            st.markdown("### Hesap Oluştur")
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Ad", key="reg_name", placeholder="Ahmet")
            with col_b:
                surname = st.text_input("Soyad", key="reg_surname", placeholder="Yılmaz")

            reg_email = st.text_input("E-posta", key="reg_email", placeholder="ornek@email.com")
            reg_password = st.text_input("Şifre", type="password", key="reg_password", placeholder="En az 6 karakter")

            col_c, col_d = st.columns(2)
            with col_c:
                age = st.number_input("Yaş", min_value=18, max_value=100, value=30, key="reg_age")
            with col_d:
                city = st.selectbox("Şehir", [
                    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
                    "Adana", "Konya", "Gaziantep", "Mersin", "Diğer"
                ], key="reg_city")

            if st.button("Kayıt Ol", use_container_width=True, type="primary", key="register_btn"):
                if name and surname and reg_email and reg_password:
                    if len(reg_password) < 6:
                        st.error("Şifre en az 6 karakter olmalıdır.")
                    else:
                        result = register_user(name, surname, reg_email, reg_password, age, city)
                        if result['success']:
                            st.success("Hesabınız oluşturuldu! Giriş yapabilirsiniz.")
                        else:
                            st.error(result['error'])
                else:
                    st.warning("Lütfen tüm alanları doldurun.")

# --- SIDEBAR ---
def show_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style='padding: 1rem 0; color: white;'>
            <h2 style='color: white; font-size: 1.5rem; margin:0;'>💎 FinansIQ</h2>
            <p style='color: #A0AEC0; font-size: 0.8rem; margin: 0.3rem 0 0 0;'>
                Merhaba, {st.session_state.user.get('name', '')} 👋
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        pages = {
            "🏠 Ana Sayfa": "dashboard",
            "👤 Profilim": "profile_setup",
            "📈 Senaryo Lab": "scenarios",
            "💳 Harcama Analizi": "expenses",
            "🤖 Finansal Asistan": "chat",
            "📄 Rapor İndir": "report",
        }

        for label, page_key in pages.items():
            is_active = st.session_state.page == page_key
            if st.button(
                label,
                use_container_width=True,
                key=f"nav_{page_key}",
                type="primary" if is_active else "secondary"
            ):
                st.session_state.page = page_key
                st.rerun()

        st.divider()

        if st.button("🚪 Çıkış Yap", use_container_width=True, key="logout_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- ANA YÖNLENDIRME ---
def main():
    if st.session_state.user is None:
        show_auth_page()
    else:
        show_sidebar()
        page = st.session_state.page

        if page == 'dashboard':
            from pages.dashboard import show_dashboard
            show_dashboard()
        elif page == 'profile_setup':
            from pages.profile import show_profile
            show_profile()
        elif page == 'scenarios':
            from pages.scenarios import show_scenarios
            show_scenarios()
        elif page == 'expenses':
            from pages.expenses import show_expenses
            show_expenses()
        elif page == 'chat':
            from pages.chat import show_chat
            show_chat()
        elif page == 'report':
            from pages.report import show_report
            show_report()
        else:
            from pages.dashboard import show_dashboard
            show_dashboard()

if __name__ == "__main__":
    main()