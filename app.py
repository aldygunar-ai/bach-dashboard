import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
import re

# ========================= CONFIG & THEME =========================
st.set_page_config(
    page_title="Dashboard PLTD Bach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CORPORATE BLUE THEME ======================
st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .stApp { background-color: #F8FAFC; }
    
    [data-testid="stSidebar"] {
        background-color: #0A2540 !important;
    }
    [data-testid="stSidebar"] * { color: #E0F2FE !important; }
    
    .header {
        background: linear-gradient(90deg, #0A2540, #1E40AF);
        padding: 2.5rem 0;
        border-radius: 0 0 16px 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(10, 37, 64, 0.2);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 29px !important;
        font-weight: 700;
        color: #1E40AF;
    }
    
    h1, h2, h3 { color: #0A2540 !important; }
    
    .stPlotlyChart, .stDataFrame {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    .stButton>button {
        background-color: #1E40AF;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== SEMUA FUNGSI LAMA KAMU ======================
# Paste semua fungsi di bawah ini (load_all, extract_kode..., norm, hitung_sisa_bulan, dll)
# ... (copy dari kode asli kamu)

# ====================== PAGES ======================
def home():
    st.markdown("""
    <div class="header">
        <h1 style="text-align:center; margin:0; font-size:3rem;">⚡ Dashboard PLTD Bach</h1>
        <p style="text-align:center; margin-top:10px; opacity:0.95; font-size:1.2rem;">
            Monitoring Stok & Logistik Pembangkit Listrik Tenaga Diesel
        </p>
    </div>
    """, unsafe_allow_html=True)

    data = load_all()
    df = data.get('stock', pd.DataFrame())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total PLTD", df['PLTD'].nunique() if not df.empty else 0)
    c2.metric("Total Stok", f"{df['Qty'].sum():,}" if not df.empty else 0)
    c3.metric("Preventive", (df['Jenis']=='Preventive').sum() if not df.empty else 0)
    c4.metric("Corrective", (df['Jenis']=='Corrective').sum() if not df.empty else 0)

    st.subheader("📍 Peta Lokasi PLTD")
    # Masukkan kode map kamu di sini


def page_stock():
    st.title("📦 Stok Material PLTD")
    data = load_all()
    df = data['stock'].copy()

    if df.empty:
        st.warning("Data stok belum tersedia.")
        return

    # Filter di sidebar (bisa pakai kode lama kamu)

    tab1, tab2, tab3 = st.tabs(["🟦 Material Preventive", "🟠 Material Corrective", "⏳ Sisa Stok dalam Bulan"])

    with tab1:
        st.subheader("Material Preventive")
        # Isi dengan kode Preventive kamu
        prev = df[df['Jenis'] == 'Preventive']
        if not prev.empty:
            st.dataframe(prev, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Material Corrective")
        corr = df[df['Jenis'] == 'Corrective']
        if not corr.empty:
            st.dataframe(corr, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Sisa Stok Preventive (Bulan)")
        m1 = data.get('m1')
        if m1 is not None:
            sisa_df = hitung_sisa_bulan(df[df['Jenis']=='Preventive'], m1)
            if not sisa_df.empty:
                st.dataframe(sisa_df, use_container_width=True, hide_index=True)
            else:
                st.info("Data sisa bulan tidak tersedia.")
        else:
            st.info("Master Data 1 belum tersedia.")


def page_analisis():
    st.title("📊 Analisis Pemakaian Material")
    # Isi dengan kode page_analisis kamu
    st.info("Halaman Analisis Pemakaian sedang di-load...")


def page_propose():
    st.title("📋 Propose Order Material")
    # Isi dengan kode page_propose kamu
    st.info("Halaman Propose Order sedang di-load...")


def page_transaksi():
    st.title("🚚 Transaksi Project")
    # Isi dengan kode page_transaksi kamu
    st.info("Halaman Transaksi Project sedang di-load...")


# ====================== NAVIGATION ======================
pg = st.navigation([
    st.Page(home, title="🏠 Beranda", icon="🏠", default=True),
    st.Page(page_stock, title="📦 Stok Material", icon="📦"),
    st.Page(page_analisis, title="📊 Analisis", icon="📈"),
    st.Page(page_propose, title="📋 Propose Order", icon="📋"),
    st.Page(page_transaksi, title="🚚 Transaksi", icon="🚚"),
])
pg.run()
