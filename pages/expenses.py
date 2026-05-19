import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
from database.db import get_profile, save_expenses, get_expenses
from agents.expense_agent import run_expense_agent, parse_csv_expenses, EXPENSE_CATEGORIES

def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def show_expenses():
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
        <h1>💳 Harcama Analizi</h1>
        <p>Harcamalarını analiz et, tasarruf potansiyelini keşfet</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📤 Veri Gir", "📊 Analiz", "💡 Öneriler"])

    with tab1:
        st.markdown("### Harcama Verisi Gir")

        input_method = st.radio(
            "Veri Giriş Yöntemi",
            ["📁 CSV Yükle", "✏️ Manuel Giriş"],
            horizontal=True
        )

        if input_method == "📁 CSV Yükle":
            st.info("CSV dosyanızda şu sütunlar olmalı: **Açıklama**, **Tutar**, **Tarih** (opsiyonel)")

            uploaded_file = st.file_uploader(
                "Banka ekstrenizi yükleyin",
                type=['csv'],
                help="Banka hesap hareketlerinizi CSV olarak dışa aktarın"
            )

            if uploaded_file:
                with st.spinner("CSV analiz ediliyor..."):
                    expenses = parse_csv_expenses(uploaded_file)

                if expenses:
                    st.success(f"✅ {len(expenses)} harcama kaydı başarıyla okundu.")
                    df = pd.DataFrame(expenses)
                    st.dataframe(df[['description', 'category', 'amount', 'date']].head(20), use_container_width=True)

                    if st.button("💾 Kaydet ve Analiz Et", type="primary", use_container_width=True):
                        save_expenses(user_id, expenses)
                        st.session_state.expenses = expenses
                        st.success("Harcamalar kaydedildi!")
                        st.rerun()
                else:
                    st.error("CSV dosyası okunamadı. Lütfen format kontrolü yapın.")

        else:
            st.markdown("#### Harcamalarını Manuel Gir")

            if 'manual_expenses' not in st.session_state:
                st.session_state.manual_expenses = []

            with st.form("add_expense"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    desc = st.text_input("Açıklama", placeholder="Market alışverişi")
                with col2:
                    amount = st.number_input("Tutar (₺)", min_value=0.0, step=10.0)
                with col3:
                    category = st.selectbox("Kategori", EXPENSE_CATEGORIES)

                add_btn = st.form_submit_button("➕ Ekle", use_container_width=True)

                if add_btn and desc and amount > 0:
                    st.session_state.manual_expenses.append({
                        'description': desc,
                        'amount': amount,
                        'category': category,
                        'date': ''
                    })
                    st.rerun()

            if st.session_state.manual_expenses:
                st.markdown(f"**{len(st.session_state.manual_expenses)} harcama eklendi:**")
                df = pd.DataFrame(st.session_state.manual_expenses)
                st.dataframe(df[['description', 'category', 'amount']], use_container_width=True)

                total = sum(e['amount'] for e in st.session_state.manual_expenses)
                st.metric("Toplam", f"{total:,.0f} ₺")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Kaydet ve Analiz Et", type="primary", use_container_width=True):
                        save_expenses(user_id, st.session_state.manual_expenses)
                        st.session_state.expenses = st.session_state.manual_expenses
                        st.session_state.manual_expenses = []
                        st.success("Harcamalar kaydedildi!")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Temizle", use_container_width=True):
                        st.session_state.manual_expenses = []
                        st.rerun()

    with tab2:
        expenses = get_expenses(user_id)

        if not expenses:
            st.info("Henüz harcama verisi yok. 'Veri Gir' sekmesinden harcamalarını ekle.")
            return

        with st.spinner("📊 Harcamalar analiz ediliyor..."):
            expense_result = run_expense_agent(expenses, profile, api_key)

        analysis = expense_result['analysis']

        # Özet metrikler
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Toplam Harcama</div>
                <div class='value'>{analysis['total_spent']:,.0f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Aylık Gelir</div>
                <div class='value'>{profile.get('monthly_income', 0):,.0f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            rate = analysis['savings_rate']
            rate_color = "#68D391" if rate >= 20 else "#F6AD55" if rate >= 10 else "#FC8181"
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Tasarruf Oranı</div>
                <div class='value' style='color:{rate_color};'>%{rate}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:0.85rem; color:#718096;'>Aylık Tasarruf Potansiyeli</div>
                <div class='value' style='color:#F6AD55;'>{analysis['monthly_savings_potential']:,.0f} ₺</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Kategori grafiği
        col1, col2 = st.columns([3, 2])

        with col1:
            if analysis['category_totals']:
                cats = list(analysis['category_totals'].keys())
                amounts = list(analysis['category_totals'].values())

                fig = go.Figure(data=[go.Bar(
                    x=cats,
                    y=amounts,
                    marker_color='#0D9488',
                    text=[f'{a:,.0f} ₺' for a in amounts],
                    textposition='auto',
                    textfont=dict(color='#FFFFFF'),
                )])
                fig.update_layout(
                    title=dict(text="Kategori Bazlı Harcamalar",
                               font=dict(color='#0F172A', size=14)),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(tickangle=-30, gridcolor='#E2E8F0',
                               tickfont=dict(color='#64748B')),
                    yaxis=dict(gridcolor='#E2E8F0',
                               tickfont=dict(color='#64748B')),
                    margin=dict(l=10, r=10, t=40, b=80)
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if analysis['category_totals']:
                fig2 = go.Figure(data=[go.Pie(
                    labels=list(analysis['category_totals'].keys()),
                    values=list(analysis['category_totals'].values()),
                    hole=0.42,
                    marker=dict(colors=['#0D9488','#0EA5E9','#7C3AED',
                                        '#F59E0B','#EF4444','#22C55E','#EC4899'],
                                line=dict(color='#FFFFFF', width=1)),
                    textinfo='percent',
                    textfont=dict(size=10),
                )])
                fig2.update_layout(
                    title=dict(text="Dağılım", font=dict(color='#0F172A', size=13)),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True)

        # Uyarılar
        if analysis['warnings']:
            st.markdown("### ⚠️ Dikkat Çeken Harcamalar")
            for w in analysis['warnings']:
                st.markdown(f"""
                <div class='alarm-card'>
                    <b>{w['category']}</b>: {w['spent']:,.0f} ₺ harcandı
                    (Önerilen max: {w['recommended_max']:,.0f} ₺ |
                    Fazla: <b>{w['excess']:,.0f} ₺</b> |
                    Gelirin %{w['ratio_percent']}'i)
                </div>
                """, unsafe_allow_html=True)

    with tab3:
        expenses = get_expenses(user_id)
        if not expenses:
            st.info("Önce harcama verisi girmen gerekiyor.")
            return

        with st.spinner("🤖 Gemini tasarruf önerileri üretiyor..."):
            expense_result = run_expense_agent(expenses, profile, api_key)

        analysis = expense_result['analysis']

        if analysis['annual_savings_potential'] > 0:
            st.markdown(f"""
            <div class='success-card'>
                💡 <b>Yıllık {analysis['annual_savings_potential']:,.0f} ₺ tasarruf potansiyelin var!</b>
                Bu parayı yatırıma yönlendirirsen hedefe ulaşma olasılığın artar.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🤖 Gemini'nin Tasarruf Önerileri")
        st.markdown(expense_result['gemini_comment'])

        if analysis['monthly_savings_potential'] > 0 and st.session_state.portfolio_result:
            st.markdown("---")
            st.markdown("### 📈 Bu Tasarrufu Yatırıma Yönlendirirsen?")
            from utils.calculations import calculate_projection
            extra_projection = calculate_projection(
                initial_savings=profile.get('total_savings', 0),
                monthly_contribution=analysis['monthly_savings_potential'],
                annual_return=st.session_state.portfolio_result['annual_return'],
                years=profile.get('goal_years', 5)
            )
            base_final = st.session_state.portfolio_result['projection']['final_value']
            new_final = extra_projection['final_value']

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mevcut Projeksiyon", f"{base_final:,.0f} ₺")
            with col2:
                st.metric(
                    "Tasarruf Eklenirse",
                    f"{new_final:,.0f} ₺",
                    delta=f"+{new_final - base_final:,.0f} ₺"
                )