import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, register_user, login_user, get_profile

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinansIQ",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── DB & SESSION ─────────────────────────────────────────────────────────────
init_db()

for _k, _v in {
    'user': None, 'profile': None, 'portfolio_result': None,
    'chat_history': [], 'market_data': None, 'page': 'login'
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── hide auto-generated multi-page links ─── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
    background: #0F1923 !important;
    border-right: 1px solid #1E2D3D;
}
[data-testid="stSidebar"] .stMarkdown { color: #CBD5E1; }
[data-testid="stSidebar"] hr { border-color: #1E2D3D !important; }

/* ─── BUTTONS: default (secondary) ─── */
.stButton > button {
    background-color: #1E2D3D !important;
    color: #CBD5E1 !important;
    border: 1px solid #2D3F50 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background-color: #0D9488 !important;
    color: #FFFFFF !important;
    border-color: #0D9488 !important;
}

/* ─── BUTTONS: primary / active ─── */
.stButton > button[kind="primary"] {
    background-color: #0D9488 !important;
    color: #FFFFFF !important;
    border: 1px solid #0D9488 !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #0F766E !important;
    border-color: #0F766E !important;
}

/* ─── LOGOUT BUTTON (last stButton in sidebar) ─── */
[data-testid="stSidebar"] [data-testid="stButton"]:last-child button {
    background-color: #1A0A0A !important;
    color: #FCA5A5 !important;
    border-color: #7F1D1D !important;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-child button:hover {
    background-color: #DC2626 !important;
    color: #FFFFFF !important;
    border-color: #DC2626 !important;
}

/* ─── PAGE SECTION HEADER (all pages) ─── */
.main-header {
    background: #FFFFFF;
    border-left: 4px solid #0D9488;
    border-radius: 10px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.main-header h1 {
    color: #0F172A !important;
    font-size: 1.8rem;
    margin: 0;
    font-weight: 800;
}
.main-header p {
    color: #64748B;
    margin: 0.25rem 0 0 0;
    font-size: 0.88rem;
}

/* ─── DASHBOARD WELCOME HEADER ─── */
.fiq-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.2rem 1.8rem;
    background: #FFFFFF;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    border-left: 4px solid #0D9488;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.fiq-header h2 {
    color: #0F172A !important;
    font-size: 1.5rem;
    margin: 0;
    font-weight: 800;
}
.fiq-header p {
    color: #64748B;
    margin: 0.25rem 0 0 0;
    font-size: 0.85rem;
}

/* ─── METRIC CARDS ─── */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.metric-card .value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #0F172A;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 0.2rem;
}

/* ─── ALARM CARDS ─── */
.alarm-card {
    background: #FFFFFF;
    border-left: 4px solid #F59E0B;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0;
    font-size: 0.88rem;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.alarm-card.high { border-left-color: #EF4444; }

/* ─── SUCCESS CARD ─── */
.success-card {
    background: #F0FDF4;
    border-left: 4px solid #22C55E;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    color: #14532D !important;
}

/* ─── TYPOGRAPHY ─── */
h3 { color: #0F172A !important; font-weight: 700 !important; }
h4 { color: #0F172A !important; font-weight: 600 !important; }

/* ─── STREAMLIT ALERT OVERRIDE ─── */
div[data-testid="stAlert"] {
    background-color: #F1F5F9 !important;
    border-left: 4px solid #0D9488 !important;
    color: #0F172A !important;
    border-radius: 8px !important;
}
div[data-testid="stAlert"] svg { color: #0D9488 !important; }

/* ─── LAYOUT ─── */
.main .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# LOGIN PAGE — two-column split with animated left panel
# ═══════════════════════════════════════════════════════════
def show_auth_page():
    # Centered narrow card layout — no columns, no image, no CSS tricks
    st.markdown(
        "<style>"
        "[data-testid='stSidebar']{display:none!important;}"
        "[data-testid='collapsedControl']{display:none!important;}"
        ".block-container{max-width:480px!important;padding-top:80px!important;}"
        "</style>",
        unsafe_allow_html=True
    )

    # Logo
    st.markdown(
        "<div style='text-align:center;margin-bottom:8px;'>"
        "<svg width='64' height='64' viewBox='0 0 64 64'>"
        "<circle cx='32' cy='32' r='30' fill='#0F1923' stroke='#0D9488' stroke-width='2.5'/>"
        "<text x='32' y='44' text-anchor='middle' font-size='36' font-weight='900' "
        "fill='#0D9488' font-family='Arial'>F</text>"
        "</svg></div>",
        unsafe_allow_html=True
    )

    # Title and slogan
    st.markdown("<h2 style='text-align:center;color:#0F172A;margin:0;'>FinansIQ</h2>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#0D9488;font-style:italic;margin-bottom:32px;'>"
        "Akıllı Kararlar, Güçlü Yarınlar.</p>",
        unsafe_allow_html=True
    )

    # Login / register tabs — logic unchanged
    tab_login, tab_register = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

    with tab_login:
        email = st.text_input("E-posta", key="login_email",
                              placeholder="ornek@email.com")
        password = st.text_input("Şifre", type="password",
                                 key="login_password", placeholder="••••••••")
        if st.button("Giriş Yap", use_container_width=True,
                     type="primary", key="login_btn"):
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
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Ad", key="reg_name", placeholder="Ahmet")
        with col_b:
            surname = st.text_input("Soyad", key="reg_surname",
                                    placeholder="Yılmaz")
        reg_email = st.text_input("E-posta", key="reg_email",
                                  placeholder="ornek@email.com")
        reg_password = st.text_input("Şifre", type="password",
                                     key="reg_password",
                                     placeholder="En az 6 karakter")
        col_c, col_d = st.columns(2)
        with col_c:
            age = st.number_input("Yaş", min_value=18, max_value=100,
                                  value=30, key="reg_age")
        with col_d:
            city = st.selectbox("Şehir", [
                "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
                "Adana", "Konya", "Gaziantep", "Mersin", "Diğer"
            ], key="reg_city")
        if st.button("Kayıt Ol", use_container_width=True,
                     type="primary", key="register_btn"):
            if name and surname and reg_email and reg_password:
                if len(reg_password) < 6:
                    st.error("Şifre en az 6 karakter olmalıdır.")
                else:
                    result = register_user(name, surname, reg_email,
                                           reg_password, age, city)
                    if result['success']:
                        st.success("Hesabınız oluşturuldu! Giriş yapabilirsiniz.")
                    else:
                        st.error(result['error'])
            else:
                st.warning("Lütfen tüm alanları doldurun.")


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
def show_sidebar():
    user = st.session_state.user
    name = user.get('name', '')
    surname = user.get('surname', '')

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:1.5rem 0 0.8rem 0;">
            <svg width="64" height="64" viewBox="0 0 96 96"
                 xmlns="http://www.w3.org/2000/svg" style="margin-bottom:0.2rem;">
                <circle cx="48" cy="48" r="46" fill="#0F1923"
                        stroke="#0D9488" stroke-width="2.5"/>
                <circle cx="48" cy="48" r="40" fill="none"
                        stroke="rgba(13,148,136,0.20)" stroke-width="1.5"/>
                <text x="48" y="68" text-anchor="middle" font-size="52"
                      font-weight="900" fill="#0D9488"
                      font-family="Arial Black, Arial, sans-serif">F</text>
            </svg>
            <p style="color:#475569;font-size:0.72rem;margin:0.45rem 0 0.3rem 0;
                      font-style:italic;">
                Akıllı Kararlar, Güçlü Yarınlar.
            </p>
            <p style="color:#E2E8F0;font-size:0.88rem;margin:0;font-weight:600;">
                Merhaba, {name} {surname}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        pages = [
            ("👤 Profilim",          "profile_setup"),
            ("🏠 Ana Sayfa",         "dashboard"),
            ("📈 Senaryo Lab",       "scenarios"),
            ("💳 Harcama Analizi",   "expenses"),
            ("🤖 Finansal Asistan",  "chat"),
            ("📄 Rapor İndir",       "report"),
        ]

        for label, page_key in pages:
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


# ═══════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════
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
