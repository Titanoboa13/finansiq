import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
from database.db import get_profile, get_alarms, mark_alarms_read
from agents.portfolio_agent import run_portfolio_agent
from agents.market_watcher import run_market_watcher
from utils.market_data import get_all_market_data, get_data_status_message

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

def show_dashboard():
    user = st.session_state.user
    user_id = user['id']
    api_key = get_api_key()

    # Profil kontrolü
    profile = get_profile(user_id)
    if not profile:
        st.warning("⚠️ Henüz finansal profilin oluşturulmamış.")
        if st.button("👤 Profil Oluştur", type="primary"):
            st.session_state.page = 'profile_setup'
            st.rerun()
        return

    st.session_state.profile = profile

    st.markdown("""
    <div class='main-header'>
        <h1>🏠 Ana Dashboard</h1>
        <p>Finansal durumuna genel bakış</p>
    </div>
    """, unsafe_allow_html=True)

    # --- MARKET WATCHER ---
    new_alerts = run_market_watcher(user_id, profile, api_key)

    # --- ALARMLAR ---
    alarms = get_alarms(user_id, unread_only=False)
    unread = get_alarms(user_id, unread_only=True)

    if unread:
        st.markdown("### 🔔 Piyasa Alarmları")
        for alarm in unread[:3]:
            msg = alarm.get('message', '')
            if not msg:
                continue
            severity = "high" if any(w in msg for w in ['🚨', '⚠️']) else ""
            st.markdown(f"""
            <div class='alarm-card {severity}'>
                {msg}
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Simüle Et", key=f"sim_{alarm['id']}"):
                    st.session_state.page = 'scenarios'
                    st.rerun()

        mark_alarms_read(user_id)
        st.divider()

    # --- CANLI PİYASA VERİLERİ ---
    with st.spinner("📡 Piyasa verileri güncelleniyor..."):
        market_data = get_all_market_data()
        st.session_state.market_data = market_data

    status_msg = get_data_status_message(market_data)
    if status_msg:
        st.warning(status_msg)

    st.markdown("### 📊 Canlı Piyasa")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    metrics = [
        (col1, "💵 USD/TL", market_data['usd_try']['value'], "₺"),
        (col2, "💶 EUR/TL", market_data['eur_try']['value'], "₺"),
        (col3, "🥇 Altın", market_data['gold_gram_try']['value'], "₺/gr"),
        (col4, "📈 BIST100", market_data['bist100']['value'], ""),
        (col5, "🏦 TCMB Faiz", market_data['tcmb_rate']['value'], "%"),
        (col6, "🔥 Enflasyon", market_data['inflation_rate']['value'], "%"),
    ]

    for col, label, value, unit in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.75rem; color:#718096;'>{label}</div>
                <div class='value' style='font-size:1.1rem;'>{value:,.2f} {unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<p style='color:#A0AEC0; font-size:0.75rem; margin-top:0.5rem;'>Son güncelleme: {market_data['fetched_at']}</p>", unsafe_allow_html=True)
    st.divider()

    # --- PORTFÖy ANALİZİ ---
    st.markdown("### 💼 Portföy Analizi")

    if st.session_state.portfolio_result is None:
        with st.spinner(""):
            steps_placeholder = st.empty()
            status_steps = [
                "📊 Piyasa verileri çekiliyor...",
                "💼 Portföy analiz ediliyor...",
                "🎯 Hedef analizi yapılıyor...",
                "📈 Projeksiyon hesaplanıyor...",
                "🤖 Gemini öneriler üretiyor..."
            ]
            for step in status_steps:
                steps_placeholder.info(step)
                import time
                time.sleep(0.3)

            portfolio_result = run_portfolio_agent(profile, api_key)
            st.session_state.portfolio_result = portfolio_result
            steps_placeholder.success("✅ Analiz tamamlandı!")
            import time
            time.sleep(0.5)
            steps_placeholder.empty()

    result = st.session_state.portfolio_result

    col1, col2 = st.columns([1, 1])

    with col1:
        # Pasta grafik
        portfolio = result['portfolio']
        labels = list(portfolio.keys())
        values = [v * 100 for v in portfolio.values()]
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textfont_size=11,
        )])
        fig.update_layout(
            title="Önerilen Portföy Dağılımı",
            showlegend=False,
            height=320,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Hedef ve olasılık
        goal_prob = result['goal_probability']
        goal_analysis = result['goal_analysis']

        prob = goal_prob['probability']
        color = "#68D391" if prob >= 70 else "#F6AD55" if prob >= 40 else "#FC8181"

        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:1rem;'>
            <div style='font-size:0.85rem; color:#718096;'>Hedefe Ulaşma Olasılığı</div>
            <div style='font-size:2.5rem; font-weight:800; color:{color};'>%{prob}</div>
            <div style='font-size:0.8rem; color:#A0AEC0;'>{profile.get('financial_goal')} • {profile.get('goal_years')} yıl</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:1rem;'>
            <div style='font-size:0.85rem; color:#718096;'>Bugünkü Hedef</div>
            <div style='font-size:1.2rem; font-weight:700;'>{goal_analysis['current_amount']:,.0f} ₺</div>
            <div style='font-size:0.75rem; color:#FC8181;'>→ {goal_analysis['future_amount']:,.0f} ₺ ({goal_analysis.get('years', profile.get('goal_years', 5))} yıl sonra, enflasyon dahil)</div>
        </div>
        """, unsafe_allow_html=True)

        if goal_prob['monthly_extra_needed'] > 0:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Ek Aylık Tasarruf İhtiyacı</div>
                <div style='font-size:1.2rem; font-weight:700; color:#F6AD55;'>{goal_prob['monthly_extra_needed']:,.0f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='success-card'>
                ✅ Mevcut birikim planıyla hedefe ulaşabilirsin!
            </div>
            """, unsafe_allow_html=True)

    # Gemini açıklaması
    if result.get('gemini_explanation'):
        with st.expander("🤖 Gemini'nin Portföy Açıklaması"):
            st.markdown(result['gemini_explanation'])

    st.divider()

    # --- PROJEKSİYON GRAFİĞİ ---
    st.markdown("### 📈 5 Yıllık Birikim Projeksiyonu")

    projection = result['projection']
    goal_analysis = result['goal_analysis']

    years = [p['year'] for p in projection['projection_by_year']]
    values = [p['value'] for p in projection['projection_by_year']]
    goal_line = [goal_analysis['future_amount']] * len(years)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=years, y=values,
        mode='lines+markers',
        name='Portföy Projeksiyonu',
        line=dict(color='#2ECC71', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.1)'
    ))
    fig2.add_trace(go.Scatter(
        x=years, y=goal_line,
        mode='lines',
        name=f'Hedef ({profile.get("financial_goal")})',
        line=dict(color='#E74C3C', width=2, dash='dash')
    ))
    fig2.update_layout(
        xaxis_title="Yıl",
        yaxis_title="Değer (₺)",
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0, y=1),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor='#E2E8F0', tickformat='d', dtick=1),
        yaxis=dict(gridcolor='#E2E8F0')
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Portföy yenileme butonu
    if st.button("🔄 Analizi Yenile", use_container_width=True):
        st.session_state.portfolio_result = None
        st.rerun()