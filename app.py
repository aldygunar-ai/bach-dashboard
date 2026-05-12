import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
import re

# ========================= CONFIG =========================
st.set_page_config(
    page_title="Dashboard PLTD Bach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================= CORPORATE BLUE THEME =========================
st.markdown("""
<style>
    /* Main Theme */
    .main { background-color: #F8FAFC; }
    .stApp { background-color: #F8FAFC; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0A2540 !important;
        color: #E0F2FE !important;
    }
    [data-testid="stSidebar"] * {
        color: #E0F2FE !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #BAE6FD !important;
    }

    /* Header */
    .header {
        background: linear-gradient(90deg, #0A2540, #1E40AF);
        padding: 2rem 0;
        border-radius: 0 0 16px 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.15);
    }

    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #1E40AF;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748B;
    }

    /* Cards */
    .stPlotlyChart, .stDataFrame {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        padding: 8px;
    }

    h1, h2, h3 {
        color: #0A2540 !important;
        font-weight: 700;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #1E40AF;
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #3B82F6;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA FUNCTIONS (Copy dari kode lama kamu) ====================
# Taruh semua fungsi kamu di sini (load_all, extract_kode_from_product_id, norm, hitung_sisa_bulan, dll)
# Saya tidak menulis ulang semuanya agar tidak terlalu panjang.

# ========================= PAGES =========================
def home():
    st.markdown("""
    <div class="header">
        <h1 style="text-align:center; margin:0; font-size:2.8rem;">⚡ Dashboard PLTD Bach</h1>
        <p style="text-align:center; margin:10px 0 0 0; opacity:0.9; font-size:1.1rem;">
            Monitoring Stok & Logistik Pembangkit Listrik Tenaga Diesel
        </p>
    </div>
    """, unsafe_allow_html=True)

    data = load_all()
    df = data.get('stock', pd.DataFrame())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PLTD", df['PLTD'].nunique())
    with col2:
        st.metric("Total Stok Material", f"{df['Qty'].sum():,}")
    with col3:
        st.metric("Preventive", (df['Jenis']=='Preventive').sum())
    with col4:
        st.metric("Corrective", (df['Jenis']=='Corrective').sum())

    st.subheader("📍 Lokasi PLTD")
    # Map code kamu tetap sama...

# Contoh page_stock yang sudah di-improve
def page_stock():
    st.title("📦 Stok Material PLTD")
    data = load_all()
    df = data['stock'].copy()

    # Filter di sidebar (sudah ada di kode lama)

    tab1, tab2, tab3 = st.tabs(["🟦 Preventive", "🟠 Corrective", "⏳ Sisa Stok (Bulan)"])

    with tab1:
        # Isi dengan kode Preventive kamu
        st.dataframe(...)  # sesuaikan

    with tab2:
        # Corrective

    with tab3:
        # Sisa Bulan dengan highlight merah

# Lanjutkan untuk page lain...

# ========================= NAVIGATION =========================
pg = st.navigation([
    st.Page(home, title="🏠 Beranda", icon="🏠", default=True),
    st.Page(page_stock, title="📦 Stok Material", icon="📦"),
    st.Page(page_analisis, title="📊 Analisis Pemakaian", icon="📈"),
    st.Page(page_propose, title="📋 Propose Order", icon="📦"),
    st.Page(page_transaksi, title="🚚 Transaksi Project", icon="🚚"),
])
pg.run()
