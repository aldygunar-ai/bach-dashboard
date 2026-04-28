import streamlit as st
import pandas as pd
from utils import (load_stock_per_pltd, load_master_sheets, load_delivery_data,
                   PREVENTIVE_CODES, get_pltd_coordinates)

st.set_page_config(page_title="Stok PLTD", layout="wide")
st.title("📦 Stock Material PLTD Aktual")

# Load data
df_stock = load_stock_per_pltd()
master = load_master_sheets()
df_cikande = master['stok_cikande']  # stok gudang Cikande
df_deliv = load_delivery_data()

# Sidebar filter
st.sidebar.header("Filter Data")
pltd_list = sorted(df_stock['PLTD'].unique()) if not df_stock.empty else []
selected_pltd = st.sidebar.multiselect("Nama PLTD", pltd_list, default=pltd_list)
kode_list = sorted(df_stock['Kode Material'].unique()) if not df_stock.empty else []
selected_kode = st.sidebar.multiselect("Kode Material", kode_list, default=kode_list)
nama_list = sorted(df_stock['Nama Material'].unique()) if not df_stock.empty else []
selected_nama = st.sidebar.multiselect("Nama Material", nama_list, default=nama_list)
jenis_options = ['Preventive', 'Corrective']
selected_jenis = st.sidebar.multiselect("Jenis Material", jenis_options, default=jenis_options)

# Apply filter
df = df_stock.copy()
if selected_pltd: df = df[df['PLTD'].isin(selected_pltd)]
if selected_kode: df = df[df['Kode Material'].isin(selected_kode)]
if selected_nama: df = df[df['Nama Material'].isin(selected_nama)]
if selected_jenis: df = df[df['Jenis'].isin(selected_jenis)]

st.subheader("🔹 Stok Aktual per PLTD")
st.dataframe(df[['PLTD', 'Kode Material', 'Nama Material', 'Type Material', 'Qty', 'Jenis']],
             use_container_width=True, hide_index=True)

# Proses Kirim vs Import/Procurement
st.subheader("🚚 Status Pengiriman (In-Transit)")
if not df_deliv.empty:
    # Olah data delivery sesuai status
    # Asumsi: kolom STATUS ada, dan kita klasifikasikan
    # Buat mapping sederhana (bisa dikustomisasi lewat sidebar)
    status_map = {
        'IN TRANSIT': 'Proses Kirim',
        'SHIPPED': 'Proses Kirim',
        'ON DELIVERY': 'Proses Kirim',
        'PO': 'Proses Import/Pembelian',
        'PROCUREMENT': 'Proses Import/Pembelian',
        'PURCHASE': 'Proses Import/Pembelian',
    }
    # Jika kolom 'STATUS' tidak ada, coba tebak dari nama kolom
    if 'STATUS' in df_deliv.columns:
        df_deliv['Kategori Pengiriman'] = df_deliv['STATUS'].map(status_map).fillna('Lainnya')
        st.write("Klasifikasi berdasarkan kolom STATUS.")
    else:
        # fallback: anggap semua sebagai proses kirim
        df_deliv['Kategori Pengiriman'] = 'Proses Kirim'
        st.info("Kolom STATUS tidak ditemukan, semua data dianggap Proses Kirim.")
    
    # Tampilkan filter kategori
    kat_list = df_deliv['Kategori Pengiriman'].unique()
    selected_kat = st.multiselect("Kategori Pengiriman", kat_list, default=kat_list)
    df_deliv_f = df_deliv[df_deliv['Kategori Pengiriman'].isin(selected_kat)]
    st.dataframe(df_deliv_f, use_container_width=True, hide_index=True)
else:
    st.warning("Data pengiriman tidak tersedia.")

# Stok Gudang Cikande
st.subheader("🏢 Stok Aktual Gudang Cikande")
if not df_cikande.empty:
    st.dataframe(df_cikande, use_container_width=True, hide_index=True)
else:
    st.info("Data gudang Cikande tidak ditemukan.")