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
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))


def show_dashboard():
    user = st.session_state.user
    user_id = user['id']
    api_key = get_api_key()
    _name = user.get('name', '')
    _surname = user.get('surname', '')

    profile = get_profile(user_id)
    if not profile:
        st.warning("⚠️ Henüz finansal profilin oluşturulmamış.")
        if st.button("👤 Profil Oluştur", type="primary"):
            st.session_state.page = 'profile_setup'
            st.rerun()
        return

    st.session_state.profile = profile

    # ── WELCOME HEADER ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='fiq-header'>
        <svg width="48" height="48" viewBox="0 0 96 96"
             xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
            <circle cx="48" cy="48" r="46" fill="#0F1923"
                    stroke="#0D9488" stroke-width="2.5"/>
            <text x="48" y="68" text-anchor="middle" font-size="52"
                  font-weight="900" fill="#0D9488"
                  font-family="Arial Black, Arial, sans-serif">F</text>
        </svg>
        <div>
            <h2>Hoş Geldin, {_name} {_surname}</h2>
            <p>Sana son dönemin önemli alarmlarını aşağıda sıraladım.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── MARKET WATCHER ────────────────────────────────────────────────────────
    run_market_watcher(user_id, profile, api_key)

    # ── ALARMS ───────────────────────────────────────────────────────────────
    unread = get_alarms(user_id, unread_only=True)
    all_alarms = get_alarms(user_id, unread_only=False)
    display_alarms = (unread if unread else all_alarms)[:3]

    st.markdown("### 🔔 Piyasa Alarmları")
    if display_alarms:
        for alarm in display_alarms:
            msg = alarm.get('message', '')
            if not msg:
                continue
            severity = "high" if any(w in msg for w in ['🚨', '⚠️']) else ""
            col_msg, col_btn = st.columns([6, 1])
            with col_msg:
                st.markdown(f"""
                <div class='alarm-card {severity}'>
                    {msg}
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("Simüle Et", key=f"sim_{alarm['id']}"):
                    st.session_state.page = 'scenarios'
                    st.rerun()
        if unread:
            mark_alarms_read(user_id)
    else:
        st.markdown("""
        <div class='alarm-card'>
            📭 Şu an aktif piyasa alarmı bulunmuyor.
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # ── LIVE MARKET DATA ──────────────────────────────────────────────────────
    with st.spinner("📡 Piyasa verileri güncelleniyor..."):
        market_data = get_all_market_data()
        st.session_state.market_data = market_data

    status_msg = get_data_status_message(market_data)
    if status_msg:
        st.warning(status_msg)

    st.markdown("### 📊 Canlı Piyasa")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    metrics = [
        (col1, "💵 USD/TL",     market_data['usd_try']['value'],        "₺"),
        (col2, "💶 EUR/TL",     market_data['eur_try']['value'],        "₺"),
        (col3, "🥇 Altın",      market_data['gold_gram_try']['value'],  "₺/gr"),
        (col4, "📈 BIST100",    market_data['bist100']['value'],        ""),
        (col5, "🏦 TCMB Faiz",  market_data['tcmb_rate']['value'],     "%"),
        (col6, "🔥 Enflasyon",  market_data['inflation_rate']['value'], "%"),
    ]

    for col, label, value, unit in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.72rem; color:#64748B;'>{label}</div>
                <div class='value' style='font-size:1.05rem; color:#0D9488;'>
                    {value:,.2f} {unit}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(
        f"<p style='color:#94A3B8;font-size:0.75rem;margin-top:0.5rem;'>"
        f"Son güncelleme: {market_data['fetched_at']}</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── PORTFOLIO ANALYSIS ────────────────────────────────────────────────────
    st.markdown("### 💼 Portföy Analizi")

    if st.session_state.portfolio_result is None:
        with st.spinner(""):
            steps_placeholder = st.empty()
            for step in [
                "📊 Piyasa verileri çekiliyor...",
                "💼 Portföy analiz ediliyor...",
                "🎯 Hedef analizi yapılıyor...",
                "📈 Projeksiyon hesaplanıyor...",
                "🤖 Gemini öneriler üretiyor...",
            ]:
                steps_placeholder.info(step)
                import time; time.sleep(0.3)

            portfolio_result = run_portfolio_agent(profile, api_key)
            st.session_state.portfolio_result = portfolio_result
            steps_placeholder.success("✅ Analiz tamamlandı!")
            import time; time.sleep(0.5)
            steps_placeholder.empty()

    result = st.session_state.portfolio_result
    col1, col2 = st.columns([1, 1])

    with col1:
        portfolio = result['portfolio']
        labels = list(portfolio.keys())
        values = [v * 100 for v in portfolio.values()]
        colors = ['#0D9488', '#0EA5E9', '#7C3AED', '#F59E0B', '#EF4444']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.42,
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12),
        )])
        fig.update_layout(
            title=dict(text="Önerilen Portföy Dağılımı",
                       font=dict(color='#0F172A', size=14)),
            showlegend=True,
            legend=dict(font=dict(color='#0F172A', size=11)),
            height=500,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        goal_prob = result['goal_probability']
        goal_analysis = result['goal_analysis']
        prob = goal_prob['probability']
        prob_color = "#22C55E" if prob >= 70 else "#F59E0B" if prob >= 40 else "#EF4444"

        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:1rem;'>
            <div style='font-size:0.85rem;color:#64748B;'>Hedefe Ulaşma Olasılığı</div>
            <div style='font-size:2.5rem;font-weight:800;color:{prob_color};'>%{prob}</div>
            <div style='font-size:0.8rem;color:#94A3B8;'>
                {profile.get('financial_goal')} • {profile.get('goal_years')} yıl
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:1rem;'>
            <div style='font-size:0.85rem;color:#64748B;'>Bugünkü Hedef</div>
            <div style='font-size:1.2rem;font-weight:700;color:#0F172A;'>
                {goal_analysis['current_amount']:,.0f} ₺
            </div>
            <div style='font-size:0.75rem;color:#EF4444;'>
                → {goal_analysis['future_amount']:,.0f} ₺
                ({goal_analysis.get('years', profile.get('goal_years', 5))} yıl sonra,
                enflasyon dahil)
            </div>
        </div>
        """, unsafe_allow_html=True)

        if goal_prob['monthly_extra_needed'] > 0:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem;color:#64748B;'>Ek Aylık Tasarruf İhtiyacı</div>
                <div style='font-size:1.2rem;font-weight:700;color:#F59E0B;'>
                    {goal_prob['monthly_extra_needed']:,.0f} ₺
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='success-card'>
                ✅ Mevcut birikim planıyla hedefe ulaşabilirsin!
            </div>
            """, unsafe_allow_html=True)

    if result.get('gemini_explanation'):
        with st.expander("🤖 Gemini'nin Portföy Açıklaması"):
            st.markdown(result['gemini_explanation'])

    st.divider()

    # ── 5-YEAR PROJECTION CHART ───────────────────────────────────────────────
    st.markdown("### 📈 5 Yıllık Birikim Projeksiyonu")

    projection = result['projection']
    goal_analysis = result['goal_analysis']

    years  = [p['year']  for p in projection['projection_by_year']]
    values = [p['value'] for p in projection['projection_by_year']]
    goal_line = [goal_analysis['future_amount']] * len(years)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=years, y=values,
        mode='lines+markers',
        name='Portföy Projeksiyonu',
        line=dict(color='#0D9488', width=3),
        marker=dict(size=8, color='#0D9488'),
        fill='tozeroy',
        fillcolor='rgba(13,148,136,0.07)'
    ))
    fig2.add_trace(go.Scatter(
        x=years, y=goal_line,
        mode='lines',
        name=f'Hedef ({profile.get("financial_goal")})',
        line=dict(color='#EF4444', width=2, dash='dash')
    ))
    fig2.update_layout(
        xaxis_title="Yıl",
        yaxis_title="Değer (₺)",
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0, y=1, font=dict(color='#0F172A', size=12)),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor='#E2E8F0', tickformat='d', dtick=1,
                   color='#64748B', tickfont=dict(color='#64748B')),
        yaxis=dict(gridcolor='#E2E8F0', color='#64748B',
                   tickfont=dict(color='#64748B'))
    )
    st.plotly_chart(fig2, use_container_width=True)

    if st.button("🔄 Analizi Yenile", use_container_width=True):
        st.session_state.portfolio_result = None
        st.rerun()
