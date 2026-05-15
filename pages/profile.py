import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import save_profile, get_profile
from agents.profile_agent import LITERACY_QUESTIONS, calculate_literacy_score, run_profile_agent

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

def show_profile():
    st.markdown("""
    <div class='main-header'>
        <h1>👤 Finansal Profilim</h1>
        <p>Kişiselleştirilmiş öneriler için profilini oluştur</p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.user['id']
    existing_profile = get_profile(user_id)

    if 'profile_step' not in st.session_state:
        st.session_state.profile_step = 1
    if 'literacy_answers' not in st.session_state:
        st.session_state.literacy_answers = {}
    if 'literacy_result' not in st.session_state:
        st.session_state.literacy_result = None
    if 'financial_info' not in st.session_state:
        st.session_state.financial_info = {}

    # --- İLERLEME ÇUBUĞU ---
    steps = ["Finansal Bilgiler", "Okuryazarlık Testi", "Sonuç"]
    progress = (st.session_state.profile_step - 1) / (len(steps) - 1)
    st.progress(progress)

    col1, col2, col3 = st.columns(3)
    for i, (col, step) in enumerate(zip([col1, col2, col3], steps), 1):
        with col:
            if i < st.session_state.profile_step:
                st.markdown(f"✅ **{step}**")
            elif i == st.session_state.profile_step:
                st.markdown(f"🔵 **{step}**")
            else:
                st.markdown(f"⚪ {step}")

    st.divider()

    # --- ADIM 1: FİNANSAL BİLGİLER ---
    if st.session_state.profile_step == 1:
        st.markdown("### 💰 Finansal Bilgilerini Gir")
        st.info("Bu bilgiler yalnızca sana özel öneriler üretmek için kullanılır.")

        col1, col2 = st.columns(2)
        with col1:
            monthly_income = st.number_input(
                "Aylık Net Gelir (₺)",
                min_value=0, max_value=10000000,
                value=int(existing_profile.get('monthly_income', 0)) if existing_profile else 0,
                step=1000,
                help="Aylık elinize geçen net maaş veya gelir"
            )
            total_savings = st.number_input(
                "Toplam Birikim (₺)",
                min_value=0, max_value=100000000,
                value=int(existing_profile.get('total_savings', 0)) if existing_profile else 0,
                step=5000,
                help="Şu an sahip olduğunuz toplam birikim"
            )
            goal_amount = st.number_input(
                "Hedef Tutar (₺) — Bugünkü Değer",
                min_value=0, max_value=100000000,
                value=int(existing_profile.get('goal_amount', 0)) if existing_profile else 0,
                step=10000,
                help="Hedefinizin bugünkü fiyatı (enflasyon düzeltmesi otomatik yapılır)"
            )

        with col2:
            monthly_expenses = st.number_input(
                "Aylık Sabit Giderler (₺)",
                min_value=0, max_value=10000000,
                value=int(existing_profile.get('monthly_expenses', 0)) if existing_profile else 0,
                step=500,
                help="Kira, fatura, kredi gibi sabit giderler"
            )
            financial_goal = st.selectbox(
                "Finansal Hedef",
                ["Konut Alımı", "Araç Alımı", "Emeklilik", "Çocuk Eğitimi", "Seyahat", "Diğer"],
                index=0,
                help="Ana finansal hedefiniz nedir?"
            )
            goal_years = st.slider(
                "Hedefe Ulaşmak İstediğin Süre (Yıl)",
                min_value=1, max_value=30,
                value=int(existing_profile.get('goal_years', 5)) if existing_profile else 5
            )

        st.markdown("---")

        if monthly_income > 0 and total_savings >= 0 and goal_amount > 0:
            monthly_saving = monthly_income - monthly_expenses
            saving_rate = (monthly_saving / monthly_income * 100) if monthly_income > 0 else 0

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Aylık Tasarruf Potansiyeli", f"{monthly_saving:,.0f} ₺")
            with col_b:
                st.metric("Tasarruf Oranı", f"%{saving_rate:.1f}")
            with col_c:
                st.metric("Hedef Süre", f"{goal_years} yıl")

        if st.button("Devam Et →", type="primary", use_container_width=True):
            if monthly_income > 0 and goal_amount > 0:
                st.session_state.financial_info = {
                    'monthly_income': monthly_income,
                    'monthly_expenses': monthly_expenses,
                    'total_savings': total_savings,
                    'financial_goal': financial_goal,
                    'goal_amount': goal_amount,
                    'goal_years': goal_years,
                }
                st.session_state.profile_step = 2
                st.rerun()
            else:
                st.error("Lütfen aylık gelir ve hedef tutarını girin.")

    # --- ADIM 2: OKURYAZARLIK TESTİ ---
    elif st.session_state.profile_step == 2:
        st.markdown("### 📚 Finansal Okuryazarlık Testi")
        st.info("Bu test sana en uygun yatırım profilini belirlemek için kullanılır. Doğru/yanlış cevap önemli değil, dürüst ol.")

        with st.form("literacy_test"):
            answers = {}
            for i, q in enumerate(LITERACY_QUESTIONS):
                st.markdown(f"**{i+1}. {q['question']}**")
                options = q['options']
                answer = st.radio(
                    f"Soru {i+1}",
                    options,
                    key=f"q_{q['id']}",
                    label_visibility="collapsed"
                )
                answers[str(q['id'])] = answer[0] if answer else ""
                if i < len(LITERACY_QUESTIONS) - 1:
                    st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                back = st.form_submit_button("← Geri", use_container_width=True)
            with col2:
                submit = st.form_submit_button("Sonuçları Gör →", type="primary", use_container_width=True)

            if back:
                st.session_state.profile_step = 1
                st.rerun()

            if submit:
                st.session_state.literacy_answers = answers
                result = calculate_literacy_score(answers)
                st.session_state.literacy_result = result
                st.session_state.profile_step = 3
                st.rerun()

    # --- ADIM 3: SONUÇ ---
    elif st.session_state.profile_step == 3:
        result = st.session_state.literacy_result
        financial_info = st.session_state.financial_info

        if not result:
            st.error("Test sonucu bulunamadı.")
            st.session_state.profile_step = 2
            st.rerun()

        st.markdown("### 🎯 Profil Sonuçların")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='value'>{result['score']}/{result['total']}</div>
                <div class='label'>Finansal Okuryazarlık Skoru</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            risk_colors = {
                "Muhafazakâr": "#68D391",
                "Dengeli": "#63B3ED",
                "Agresif": "#FC8181"
            }
            color = risk_colors.get(result['risk_profile'], '#63B3ED')
            st.markdown(f"""
            <div class='metric-card'>
                <div class='value' style='color:{color};'>{result['risk_profile']}</div>
                <div class='label'>Risk Profili</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='value'>{result['level_description']}</div>
                <div class='label'>Finansal Seviye</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        with st.expander("📋 Test Sonuçlarını Gör"):
            for r in result['results']:
                icon = "✅" if r['is_correct'] else "❌"
                st.markdown(f"{icon} **{r['question']}**")
                if not r['is_correct']:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;💡 {r['explanation']}")

        # Profili kaydet
        profile_data = {
            **financial_info,
            'risk_profile': result['risk_profile'],
            'literacy_score': result['score'],
            'communication_level': result['communication_level'],
        }

        # Gemini analizi
        with st.spinner("🤖 Gemini profilini analiz ediyor..."):
            api_key = get_api_key()
            gemini_summary = run_profile_agent(profile_data, api_key)

        st.markdown("### 🤖 Gemini'nin Profil Değerlendirmesi")
        if gemini_summary:
            st.markdown(gemini_summary)
        else:
            st.info("Gemini değerlendirmesi yüklenemedi.")

        if st.button("✅ Profili Kaydet ve Devam Et", type="primary", use_container_width=True):
            save_profile(user_id, profile_data)
            st.session_state.profile = profile_data
            st.session_state.profile_step = 1
            st.session_state.literacy_answers = {}
            st.session_state.literacy_result = None
            st.session_state.financial_info = {}
            st.success("Profil kaydedildi!")
            st.session_state.page = 'dashboard'
            st.rerun()

        if st.button("← Testi Tekrar Yap", use_container_width=True):
            st.session_state.profile_step = 2
            st.rerun()