"""
Personal Finance Dashboard — Streamlit versiyasi
====================================================
Ishga tushirish:
    streamlit run app.py

Talab qilinadigan kutubxonalar:
    pip install streamlit pandas numpy plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# SAHIFA SOZLAMALARI
# ============================================================
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
)

# ============================================================
# MA'LUMOTLARNI YUKLASH (yoki yaratish, agar fayl bo'lmasa)
# ============================================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("personal_finance.csv")
    except FileNotFoundError:
        # Agar CSV topilmasa, shu yerda yaratamiz
        np.random.seed(42)
        n_people, months = 50, pd.date_range('2024-01-01', '2025-12-01', freq='MS')
        occupations = ['Engineer', 'Teacher', 'Doctor', 'Designer', 'Manager', 'Student', 'Freelancer']
        base_income = {'Engineer': 4500, 'Teacher': 2800, 'Doctor': 6000, 'Designer': 3500,
                        'Manager': 5000, 'Student': 1200, 'Freelancer': 3000}
        categories = {
            'Rent': (0.25, 0.35), 'Groceries': (0.10, 0.15), 'Transport': (0.05, 0.10),
            'Entertainment': (0.03, 0.08), 'Utilities': (0.04, 0.07),
            'Healthcare': (0.02, 0.06), 'Education': (0.0, 0.05), 'Shopping': (0.03, 0.09),
        }
        rows = []
        for pid in range(1, n_people + 1):
            occ = np.random.choice(occupations)
            age = np.random.randint(22, 60)
            base = max(np.random.normal(base_income[occ], 500), 800)
            for month in months:
                income = base * np.random.uniform(0.95, 1.08)
                exp = {c: income * np.random.uniform(lo, hi) for c, (lo, hi) in categories.items()}
                total_exp = sum(exp.values())
                savings = income - total_exp
                for cat, amt in exp.items():
                    rows.append({
                        'person_id': pid, 'age': age, 'occupation': occ,
                        'month': month.strftime('%Y-%m'), 'income': round(income, 2),
                        'expense_category': cat, 'expense_amount': round(amt, 2),
                        'total_expense': round(total_exp, 2), 'savings': round(savings, 2),
                        'savings_rate': round(savings / income * 100, 2),
                    })
        df = pd.DataFrame(rows)
    return df


df = load_data()
df_unique = df.drop_duplicates(subset=['person_id', 'month'])

# ============================================================
# SIDEBAR — FILTRLAR
# ============================================================
st.sidebar.header("🔍 Filtrlar")

occupations_list = sorted(df['occupation'].unique())
selected_occupations = st.sidebar.multiselect(
    "Kasb tanlang", occupations_list, default=occupations_list
)

months_list = sorted(df['month'].unique())
month_range = st.sidebar.select_slider(
    "Oy oralig'i", options=months_list, value=(months_list[0], months_list[-1])
)

age_min, age_max = int(df['age'].min()), int(df['age'].max())
age_range = st.sidebar.slider("Yosh oralig'i", age_min, age_max, (age_min, age_max))

# Filtrlarni qo'llash
mask = (
    df['occupation'].isin(selected_occupations) &
    (df['month'] >= month_range[0]) & (df['month'] <= month_range[1]) &
    (df['age'] >= age_range[0]) & (df['age'] <= age_range[1])
)
filtered = df[mask]
filtered_unique = filtered.drop_duplicates(subset=['person_id', 'month'])

st.sidebar.markdown("---")
st.sidebar.caption(f"📊 {filtered['person_id'].nunique()} kishi tanlandi")

# ============================================================
# SARLAVHA
# ============================================================
st.title("💰 Personal Finance Dashboard")
st.caption("Daromad, xarajat va jamg'arma tendensiyalarini tahlil qiluvchi interaktiv panel")

# ============================================================
# ASOSIY KO'RSATKICHLAR (4 ta metric karta)
# ============================================================
col1, col2, col3, col4 = st.columns(4)

avg_income = filtered_unique['income'].mean()
avg_expense = filtered_unique['total_expense'].mean()
avg_savings = filtered_unique['savings'].mean()
avg_rate = filtered_unique['savings_rate'].mean()

col1.metric("O'rtacha daromad", f"${avg_income:,.0f}")
col2.metric("O'rtacha xarajat", f"${avg_expense:,.0f}")
col3.metric("O'rtacha jamg'arma", f"${avg_savings:,.0f}")
col4.metric("Jamg'arma darajasi", f"{avg_rate:.1f}%")

st.markdown("---")

# ============================================================
# 1-QATOR: DAROMAD-XARAJAT TREND + KATEGORIYA
# ============================================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Daromad vs Xarajat (oylik trend)")
    monthly = filtered_unique.groupby('month').agg(
        Daromad=('income', 'sum'),
        Xarajat=('total_expense', 'sum'),
        Jamgarma=('savings', 'sum')
    ).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly['month'], y=monthly['Daromad'],
                                    name='Daromad', line=dict(color='#3FC98C', width=3)))
    fig_trend.add_trace(go.Scatter(x=monthly['month'], y=monthly['Xarajat'],
                                    name='Xarajat', line=dict(color='#E8A23D', width=3)))
    fig_trend.update_layout(height=380, margin=dict(t=20, b=20),
                             legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🥧 Xarajat kategoriyalari")
    cat_summary = filtered.groupby('expense_category')['expense_amount'].sum().reset_index()
    fig_pie = px.pie(cat_summary, names='expense_category', values='expense_amount', hole=0.5)
    fig_pie.update_layout(height=380, margin=dict(t=20, b=20), showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# ============================================================
# 2-QATOR: JAMG'ARMA TREND + KASB TAQQOSLASH
# ============================================================
col_left2, col_right2 = st.columns([1, 1])

with col_left2:
    st.subheader("💵 Jamg'arma dinamikasi")
    fig_savings = px.area(monthly, x='month', y='Jamgarma', color_discrete_sequence=['#5FB3E8'])
    fig_savings.update_layout(height=350, margin=dict(t=20, b=20))
    st.plotly_chart(fig_savings, use_container_width=True)

with col_right2:
    st.subheader("👔 Kasb bo'yicha o'rtacha daromad")
    occ_summary = filtered_unique.groupby('occupation').agg(
        avg_income=('income', 'mean'),
        avg_savings_rate=('savings_rate', 'mean')
    ).reset_index().sort_values('avg_income', ascending=True)

    fig_occ = px.bar(occ_summary, x='avg_income', y='occupation', orientation='h',
                      color_discrete_sequence=['#3FC98C'])
    fig_occ.update_layout(height=350, margin=dict(t=20, b=20),
                           xaxis_title="O'rtacha daromad ($)", yaxis_title="")
    st.plotly_chart(fig_occ, use_container_width=True)

st.markdown("---")

# ============================================================
# JADVAL (Excel-day, qidirish + saralash Streamlit'da bepul!)
# ============================================================
st.subheader("📋 Barcha ma'lumotlar")

search = st.text_input("🔍 Qidirish (kasb, ID...)", "")

table_view = filtered_unique[
    ['person_id', 'age', 'occupation', 'month', 'income', 'total_expense', 'savings', 'savings_rate']
].rename(columns={
    'person_id': 'ID', 'age': 'Yosh', 'occupation': 'Kasb', 'month': 'Oy',
    'income': 'Daromad', 'total_expense': 'Xarajat', 'savings': 'Jamg\'arma',
    'savings_rate': 'Jamg\'arma %'
})

if search:
    table_view = table_view[
        table_view['Kasb'].str.contains(search, case=False) |
        table_view['ID'].astype(str).str.contains(search) |
        table_view['Oy'].str.contains(search)
    ]

st.dataframe(
    table_view.sort_values(['ID', 'Oy']),
    use_container_width=True,
    height=400,
    column_config={
        "Daromad": st.column_config.NumberColumn(format="$%.0f"),
        "Xarajat": st.column_config.NumberColumn(format="$%.0f"),
        "Jamg'arma": st.column_config.NumberColumn(format="$%.0f"),
        "Jamg'arma %": st.column_config.NumberColumn(format="%.1f%%"),
    }
)

st.caption(f"{len(table_view)} ta qator ko'rsatilmoqda")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Personal Finance Dashboard · Streamlit + Plotly bilan yaratilgan · 2026")
