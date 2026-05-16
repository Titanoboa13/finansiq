import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_profile
from agents.orchestrator import run_chat_agent
from utils.market_data import get_all_market_data

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

def show_chat():
    user_id = st.session_state.user['id']
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
        <h1>🤖 Finansal Asistan</h1>
        <p>Türkiye finans piyasaları hakkında her şeyi sor</p>
    </div>
    """, unsafe_allow_html=True)

    # Piyasa verisi
    if st.session_state.market_data is None:
        with st.spinner("Piyasa verileri yükleniyor..."):
            st.session_state.market_data = get_all_market_data()
    market_data = st.session_state.market_data

    # Sohbet geçmişi başlat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Hızlı sorular
    st.markdown("#### 💡 Hızlı Sorular")
    quick_questions = [
        "Portföyüme altın eklemeli miyim?",
        "Dolar almak mantıklı mı şu an?",
        "Enflasyona karşı nasıl korunurum?",
        "BIST'e yatırım yapmalı mıyım?",
        "Acil durum fonumu nasıl oluşturmalıyım?",
        "Kripto para riski nedir?",
    ]

    cols = st.columns(3)
    for i, question in enumerate(quick_questions):
        with cols[i % 3]:
            if st.button(question, use_container_width=True, key=f"quick_{i}"):
                st.session_state.pending_question = question
                st.rerun()

    st.divider()

    # Sohbet alanı
    chat_container = st.container()

    with chat_container:
        if not st.session_state.chat_history:
            risk_profile = profile.get('risk_profile', 'Dengeli')
            comm_level = profile.get('communication_level', 'orta')
            st.markdown(f"""
            <div style='background:#EBF8FF; border-radius:12px; padding:1rem; margin-bottom:1rem; border-left:4px solid #63B3ED; color:#1A1A2E;'>
                <b>🤖 FinansIQ:</b> Merhaba {st.session_state.user.get('name', '')}! 👋<br><br>
                Risk profilin <b>{risk_profile}</b> olarak belirlendi.
                Türkiye finans piyasaları, yatırım stratejileri veya kişisel finans konularında
                sana yardımcı olmaya hazırım.<br><br>
                Ne sormak istersin?
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f"""
                <div style='background:#EBF8FF; border-radius:12px; padding:0.8rem 1rem;
             margin:0.5rem 0; margin-left:2rem; border-left:4px solid #63B3ED; color:#1A1A2E;'>
            <b>👤 Sen:</b> {msg['content']}
        </div>
                """, unsafe_allow_html=True)
            else:
                is_risky = msg.get('is_risky', False)
                border_color = "#FC8181" if is_risky else "#68D391"
                icon = "⚠️" if is_risky else "🤖"
                st.markdown(f"""
                <div style='background:#F0FFF4; border-radius:12px; padding:0.8rem 1rem;
             margin:0.5rem 0; margin-right:2rem; border-left:4px solid {border_color}; color:#1A1A2E;'>
            <b>{icon} FinansIQ:</b> {msg['content']}
                </div>
                """, unsafe_allow_html=True)

    # Bekleyen soru varsa işle
    if 'pending_question' in st.session_state and st.session_state.pending_question:
        user_message = st.session_state.pending_question
        st.session_state.pending_question = None

        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_message
        })

        with st.spinner("🤖 FinansIQ düşünüyor..."):
            response = run_chat_agent(
                message=user_message,
                chat_history=st.session_state.chat_history,
                profile_data=profile,
                market_data=market_data,
                api_key=api_key
            )

        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response['reply'],
            'is_risky': response['is_risky']
        })
        st.rerun()

    # Mesaj girişi
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Mesajın",
            placeholder="Örn: Dolar almak mantıklı mı şu an?",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col2:
        send = st.button("Gönder", type="primary", use_container_width=True)

    if send and user_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        with st.spinner("🤖 FinansIQ düşünüyor..."):
            response = run_chat_agent(
                message=user_input,
                chat_history=st.session_state.chat_history,
                profile_data=profile,
                market_data=market_data,
                api_key=api_key
            )

        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response['reply'],
            'is_risky': response['is_risky']
        })
        st.rerun()

    # Sohbeti temizle
    if st.session_state.chat_history:
        st.divider()
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()