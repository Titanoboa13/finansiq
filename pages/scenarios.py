import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
from database.db import get_profile
from agents.scenario_agent import run_scenario_agent, SCENARIO_DEFINITIONS
from agents.portfolio_agent import run_portfolio_agent

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY", "")

def show_scenarios():
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
        <h1>🔬 Senaryo Laboratuvarı</h1>
        <p>Farklı ekonomik senaryoları simüle et ve portföyüne etkisini gör</p>
    </div>
    """, unsafe_allow_html=True)

    # Portföy sonucu kontrolü
    if st.session_state.portfolio_result is None:
        with st.spinner("Portföy analizi yükleniyor..."):
            st.session_state.portfolio_result = run_portfolio_agent(profile, api_key)

    result = st.session_state.portfolio_result
    portfolio = result['portfolio']
    base_projection = result['projection']
    goal_analysis = result['goal_analysis']

    # Real goal amount'u profile'a ekle
    profile_with_goal = dict(profile)
    profile_with_goal['real_goal_amount'] = goal_analysis['future_amount']
    profile_with_goal['monthly_contribution'] = result.get('monthly_contribution', 0)

    # --- MEVCUT DURUM ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:0.85rem; color:#718096;'>Mevcut Birikim</div>
            <div class='value'>{profile.get('total_savings', 0):,.0f} ₺</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:0.85rem; color:#718096;'>Baz Durum Projeksiyon</div>
            <div class='value'>{base_projection['final_value']:,.0f} ₺</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        prob = result['goal_probability']['probability']
        color = "#68D391" if prob >= 70 else "#F6AD55" if prob >= 40 else "#FC8181"
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:0.85rem; color:#718096;'>Mevcut Olasılık</div>
            <div class='value' style='color:{color};'>%{prob}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- SENARYO SEÇİMİ ---
    st.markdown("### 🎛️ Senaryo Seç ve Parametreyi Ayarla")

    scenario_cols = st.columns(len(SCENARIO_DEFINITIONS))
    selected_scenario = st.session_state.get('selected_scenario', 'usd_increase')

    for col, (key, scenario) in zip(scenario_cols, SCENARIO_DEFINITIONS.items()):
        with col:
            is_selected = selected_scenario == key
            if st.button(
                f"{scenario['icon']} {scenario['label']}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                key=f"scen_{key}"
            ):
                st.session_state.selected_scenario = key
                st.rerun()

    st.markdown("---")

    scenario_def = SCENARIO_DEFINITIONS[selected_scenario]
    st.markdown(f"#### {scenario_def['icon']} {scenario_def['label']}: *{scenario_def['description']}*")

    scenario_value = st.slider(
        f"Değer ({scenario_def['unit']})",
        min_value=float(scenario_def['min']),
        max_value=float(scenario_def['max']),
        value=float(scenario_def['default']),
        step=float(scenario_def['min']),
        key=f"slider_{selected_scenario}"
    )

    if st.button("🚀 Senaryoyu Çalıştır", type="primary", use_container_width=True):
        with st.spinner(""):
            steps = [
                "📊 Senaryo hesaplanıyor...",
                "📈 Projeksiyon güncelleniyor...",
                "🤖 Gemini analiz yapıyor..."
            ]
            placeholder = st.empty()
            import time
            for step in steps:
                placeholder.info(step)
                time.sleep(0.4)

            scenario_result = run_scenario_agent(
                scenario_type=selected_scenario,
                scenario_value=scenario_value,
                portfolio=portfolio,
                profile_data=profile_with_goal,
                base_projection=base_projection,
                api_key=api_key
            )
            st.session_state.scenario_result = scenario_result
            placeholder.empty()

    # --- SENARYO SONUÇLARI ---
    if 'scenario_result' in st.session_state and st.session_state.scenario_result:
        sr = st.session_state.scenario_result
        st.divider()
        st.markdown("### 📊 Senaryo Sonuçları")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Baz Durum</div>
                <div class='value'>{sr['base_final_value']:,.0f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            change_color = "#68D391" if sr['change_amount'] >= 0 else "#FC8181"
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Bu Senaryoda</div>
                <div class='value' style='color:{change_color};'>{sr['new_final_value']:,.0f} ₺</div>
                <div style='font-size:0.8rem; color:{change_color};'>{sr['change_amount']:+,.0f} ₺ (%{sr['change_percent']:+.1f})</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            new_prob = sr['new_probability']['probability']
            prob_color = "#68D391" if new_prob >= 70 else "#F6AD55" if new_prob >= 40 else "#FC8181"
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Yeni Olasılık</div>
                <div class='value' style='color:{prob_color};'>%{new_prob}</div>
            </div>
            """, unsafe_allow_html=True)

        # Karşılaştırmalı grafik
        st.markdown("#### 📈 Baz Durum vs Senaryo Karşılaştırması")

        base_years = [p['year'] for p in base_projection['projection_by_year']]
        base_values = [p['value'] for p in base_projection['projection_by_year']]
        scen_years = [p['year'] for p in sr['projection_by_year']]
        scen_values = [p['value'] for p in sr['projection_by_year']]
        goal_line = [goal_analysis['future_amount']] * len(base_years)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=base_years, y=base_values,
            mode='lines+markers',
            name='Baz Durum',
            line=dict(color='#94A3B8', width=2, dash='dot'),
            marker=dict(size=6, color='#94A3B8')
        ))
        fig.add_trace(go.Scatter(
            x=scen_years, y=scen_values,
            mode='lines+markers',
            name=f'Senaryo: {sr["scenario_label"]}',
            line=dict(color='#0D9488', width=3),
            marker=dict(size=8, color='#0D9488')
        ))
        fig.add_trace(go.Scatter(
            x=base_years, y=goal_line,
            mode='lines',
            name='Hedef',
            line=dict(color='#EF4444', width=2, dash='dash')
        ))
        fig.update_layout(
            height=380,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0, y=1, font=dict(color='#0F172A', size=12)),
            xaxis=dict(gridcolor='#E2E8F0', title="Yıl",
                       tickformat='d', dtick=1, tickfont=dict(color='#64748B')),
            yaxis=dict(gridcolor='#E2E8F0', title="Değer (₺)",
                       tickfont=dict(color='#64748B')),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gemini yorumu
        st.markdown("#### 🤖 Gemini'nin Senaryo Yorumu")
        if sr.get('gemini_comment'):
            st.markdown(sr['gemini_comment'])
        else:
            st.info("⏳ Gemini yorumu yüklenemedi. Tekrar deneyin.")