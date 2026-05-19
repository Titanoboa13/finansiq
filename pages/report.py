import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_profile, get_expenses
from agents.portfolio_agent import run_portfolio_agent
from agents.orchestrator import generate_financial_advice
from utils.pdf_generator import generate_pdf_report

def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def show_report():
    user_id = st.session_state.user['id']
    user = st.session_state.user
    api_key = get_api_key()

    profile = get_profile(user_id)
    if not profile:
        st.warning("⚠️ Önce finansal profilini oluşturman gerekiyor.")
        if st.button("👤 Profile Git", type="primary"):
            st.session_state.page = 'profile_setup'
            st.rerun()
        return

    st.markdown("""
    <div class='main-header'>
        <h1>📄 Finansal Rapor</h1>
        <p>Kişisel finansal planını PDF olarak indir</p>
    </div>
    """, unsafe_allow_html=True)

    # Rapor önizleme
    st.markdown("### 📋 Rapor İçeriği")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background:#FFFFFF;border-radius:10px;padding:1.2rem;
                    border:1px solid #E2E8F0;border-left:4px solid #0D9488;
                    box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
            <h4 style='color:#0F172A;margin:0 0 0.8rem 0;'>📊 Raporda Neler Var?</h4>
            <ul style='color:#64748B;margin:0;padding-left:1.2rem;line-height:1.9;'>
                <li>Finansal profil özeti ve risk skoru</li>
                <li>Portföy önerisi (pasta grafik dahil)</li>
                <li>Enflasyon düzeltmeli hedef analizi</li>
                <li>5 yıllık birikim projeksiyonu (grafik dahil)</li>
                <li>Harcama analizi (varsa)</li>
                <li>Gemini kişisel tavsiyeleri</li>
                <li>Yasal uyarı ve imza</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background:#FFFFFF;border-radius:10px;padding:1.2rem;
                    border:1px solid #E2E8F0;border-left:4px solid #0D9488;
                    box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
            <h4 style='color:#0F172A;margin:0 0 0.8rem 0;'>👤 Profil Özeti</h4>
            <table style='width:100%;color:#64748B;font-size:0.9rem;line-height:2;'>
                <tr><td><b style='color:#0F172A;'>İsim:</b></td>
                    <td>{user.get('name')} {user.get('surname')}</td></tr>
                <tr><td><b style='color:#0F172A;'>Risk Profili:</b></td>
                    <td>{profile.get('risk_profile')}</td></tr>
                <tr><td><b style='color:#0F172A;'>Hedef:</b></td>
                    <td>{profile.get('financial_goal')}</td></tr>
                <tr><td><b style='color:#0F172A;'>Süre:</b></td>
                    <td>{profile.get('goal_years')} yıl</td></tr>
                <tr><td><b style='color:#0F172A;'>Birikim:</b></td>
                    <td>{profile.get('total_savings', 0):,.0f} ₺</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # PDF oluştur butonu
    st.markdown("### 📥 Raporu Oluştur ve İndir")
    st.info("Rapor oluşturma işlemi 15-30 saniye sürebilir. Gemini kişisel tavsiyeler üretiyor.")

    if st.button("🚀 PDF Raporu Oluştur", type="primary", use_container_width=True):
        with st.spinner(""):
            steps = [
                "📊 Piyasa verileri çekiliyor...",
                "💼 Portföy analiz ediliyor...",
                "🎯 Hedef hesaplanıyor...",
                "🤖 Gemini kişisel tavsiyeler üretiyor...",
                "📄 PDF oluşturuluyor...",
                "🎨 Grafikler PDF'e ekleniyor..."
            ]
            placeholder = st.empty()
            import time

            for step in steps[:-2]:
                placeholder.info(step)
                time.sleep(0.5)

            # Portföy analizi
            if st.session_state.portfolio_result is None:
                portfolio_result = run_portfolio_agent(profile, api_key)
                st.session_state.portfolio_result = portfolio_result
            else:
                portfolio_result = st.session_state.portfolio_result

            placeholder.info(steps[-2])

            # Gemini tavsiyeleri
            gemini_advice = generate_financial_advice(profile, portfolio_result, api_key)

            placeholder.info(steps[-1])
            time.sleep(0.3)

            # Harcama analizi
            expenses = get_expenses(user_id)
            expense_analysis = {}
            if expenses:
                from agents.expense_agent import run_expense_agent
                expense_result = run_expense_agent(expenses, profile, api_key)
                expense_analysis = expense_result['analysis']

            try:
                pdf_bytes = generate_pdf_report(
                    user_data=user,
                    profile_data=profile,
                    portfolio=portfolio_result['portfolio'],
                    projection_data=portfolio_result['projection']['projection_by_year'],
                    goal_analysis=portfolio_result['goal_analysis'],
                    expense_analysis=expense_analysis,
                    gemini_advice=gemini_advice
                )
                st.session_state['report_pdf_bytes'] = pdf_bytes
                st.session_state['report_pdf_filename'] = (
                    f"FinansIQ_Rapor_{user.get('name')}_{user.get('surname')}.pdf"
                )
                placeholder.success("✅ Rapor hazır!")
            except Exception as e:
                st.session_state.pop('report_pdf_bytes', None)
                st.session_state.pop('report_pdf_filename', None)
                placeholder.error(f"PDF oluşturulurken hata: {str(e)}")
                st.error("Lütfen tekrar deneyin.")

    if 'report_pdf_bytes' in st.session_state:
        st.download_button(
            label="📥 Finansal Planımı İndir (PDF)",
            data=st.session_state['report_pdf_bytes'],
            file_name=st.session_state.get(
                'report_pdf_filename',
                f"FinansIQ_Rapor_{user.get('name', '')}_{user.get('surname', '')}.pdf",
            ),
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
        st.markdown("""
        <div class='success-card'>
            ✅ Raporun hazır! <b>"Finansal Planımı İndir"</b> butonuna tıklayarak indirebilirsin.
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Rapor hakkında bilgi
    st.markdown("""
    <div style='background:#FFFBEB;border-radius:10px;padding:1rem;
                border:1px solid #FDE68A;border-left:4px solid #F59E0B;'>
        <p style='color:#78350F;font-size:0.85rem;margin:0;'>
            ⚠️ <b>Yasal Uyarı:</b> FinansIQ tarafından oluşturulan bu rapor yatırım tavsiyesi
            niteliği taşımamaktadır. Yatırım kararlarınızı vermeden önce lisanslı bir
            finansal danışmana başvurmanız önerilir.
        </p>
    </div>
    """, unsafe_allow_html=True)