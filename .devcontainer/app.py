import streamlit as st
import pandas as pd
from st_pages import Page, show_pages  # optional, untuk navigasi eksplisit
from utils import load_stock_per_pltd, load_delivery_data, load_project_data

st.set_page_config(page_title="Dashboard PLTD Bach", layout="wide")
st.title("⚡ Dashboard Monitoring Stok & Logistik PLTD")
st.markdown("Ringkasan Cepat – Klik menu di sidebar untuk detail.")

# Load data ringkasan (gunakan cache dari utils)
st.cache_data.clear()  # optional, clear saat refresh halaman utama
df_stock = load_stock_per_pltd()
df_deliv = load_delivery_data()
# df_project = load_project_data()  # kalau mau

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total PLTD", len(df_stock['PLTD'].unique()) if not df_stock.empty else 0)
with col2:
    total_stock = df_stock['Qty'].sum() if not df_stock.empty else 0
    st.metric("Total Stok Material", f"{total_stock:,.0f}")
with col3:
    # Contoh: hitung material kritis (akan diperbaiki di page 3, sementara placeholder)
    st.metric("Material Perlu Reorder", "Coming soon")

st.markdown("---")
st.subheader("Navigasi Halaman")
cols = st.columns(4)
with cols[0]:
    st.page_link("pages/2_Stock_PLTD.py", label="📦 Stok PLTD", icon="📦")
with cols[1]:
    st.page_link("pages/3_Analisis_Stok.py", label="📊 Analisis Stok", icon="📊")
with cols[2]:
    st.page_link("pages/4_Pemakaian.py", label="🔥 Pemakaian", icon="🔥")
with cols[3]:
    st.page_link("pages/5_Transaksi_Project.py", label="🚚 Transaksi Project", icon="🚚")

st.markdown("---")
# Tampilkan peta lokasi PLTD sebagai preview kecil
if not df_stock.empty:
    coords = df_stock[['PLTD']].drop_duplicates()
    coords['lat'] = coords['PLTD'].apply(lambda x: get_pltd_coordinates(x)[0])
    coords['lon'] = coords['PLTD'].apply(lambda x: get_pltd_coordinates(x)[1])
    valid = coords.dropna(subset=['lat'])
    if not valid.empty:
        st.subheader("📍 Lokasi PLTD")
        st.map(valid, latitude='lat', longitude='lon', zoom=4)