import streamlit as st
import pandas as pd
import numpy as np
from utils import (load_stock_per_pltd, load_master_sheets, load_delivery_data,
                   get_duration, get_pm_interval, PREVENTIVE_CODES)

st.set_page_config(page_title="Analisis Stok", layout="wide")
st.title("📊 Analisis Stok & Kebutuhan Material")

# Load data
df_stock = load_stock_per_pltd()
master = load_master_sheets()
df_pemakaian = master['pemakaian']   # historical consumption
df_harga = master['harga']           # price list from D365
df_deliv = load_delivery_data()

# --- Kalkulasi kebutuhan ---
# Asumsi: jam operasi 24 jam/hari untuk semua PLTD, atau kita minta input user
jam_operasi_per_hari = st.sidebar.number_input("Asumsi Jam Operasi/hari", min_value=1, max_value=24, value=24)
hari_per_bulan = 30.5
jam_per_bulan = hari_per_bulan * jam_operasi_per_hari

# Gabungkan stok dengan harga
if not df_harga.empty:
    # Sesuaikan kolom kunci: mungkin 'Kode Material' atau 'Material Code'
    if 'Kode Material' in df_harga.columns and 'Harga Satuan' in df_harga.columns:
        df_stock = df_stock.merge(df_harga[['Kode Material', 'Harga Satuan']],
                                  on='Kode Material', how='left')
    else:
        st.warning("Kolom harga tidak standar, lewati penggabungan harga.")

# Hitung kebutuhan PM
df_stock['Interval PM (jam)'] = df_stock['Kode Material'].apply(get_pm_interval)
df_stock['Kebutuhan/bin (PM)'] = np.ceil(jam_per_bulan / df_stock['Interval PM (jam)'])

# Hitung kebutuhan Aktual dari data pemakaian (jika tersedia)
if not df_pemakaian.empty:
    # Asumsi df_pemakaian memiliki PLTD, Kode Material, Tanggal, Qty
    if 'PLTD' in df_pemakaian.columns and 'Kode Material' in df_pemakaian.columns and 'Qty' in df_pemakaian.columns:
        df_pemakaian['Tanggal'] = pd.to_datetime(df_pemakaian.iloc[:, 0])  # asumsi kolom pertama tanggal
        last_6m = pd.Timestamp.now() - pd.DateOffset(months=6)
        recent = df_pemakaian[df_pemakaian['Tanggal'] >= last_6m]
        konsumsi_bulanan = recent.groupby(['PLTD', 'Kode Material'])['Qty'].sum() / 6  # rata2 per bulan
        konsumsi_bulanan = konsumsi_bulanan.reset_index()
        konsumsi_bulanan.rename(columns={'Qty': 'Kebutuhan/bin (Aktual)'}, inplace=True)
        df_stock = df_stock.merge(konsumsi_bulanan, on=['PLTD', 'Kode Material'], how='left')
        df_stock['Kebutuhan/bin (Aktual)'] = df_stock['Kebutuhan/bin (Aktual)'].fillna(0)
    else:
        df_stock['Kebutuhan/bin (Aktual)'] = 0
else:
    df_stock['Kebutuhan/bin (Aktual)'] = 0

# Pilih metode kebutuhan (PM atau Aktual, jika aktual > 0 pakai aktual)
df_stock['Kebutuhan/bin (Efektif)'] = np.where(df_stock['Kebutuhan/bin (Aktual)'] > 0,
                                               df_stock['Kebutuhan/bin (Aktual)'],
                                               df_stock['Kebutuhan/bin (PM)'])
df_stock['Kebutuhan/hari'] = df_stock['Kebutuhan/bin (Efektif)'] / hari_per_bulan

# Durasi pengiriman
df_stock['Durasi Kirim (hari)'] = df_stock['PLTD'].apply(get_duration)

# Sisa hari stok
df_stock['Sisa Hari Stok'] = np.where(df_stock['Kebutuhan/hari'] > 0,
                                      df_stock['Qty'] / df_stock['Kebutuhan/hari'],
                                      9999)  # angka besar jika tidak ada kebutuhan
# Status alert
def get_status(row):
    if row['Sisa Hari Stok'] < row['Durasi Kirim (hari)']:
        return '🔴 Critical Reorder'
    elif row['Sisa Hari Stok'] < row['Durasi Kirim (hari)'] * 1.5:
        return '🟡 Warning'
    else:
        return '🟢 Aman'

df_stock['Status'] = df_stock.apply(get_status, axis=1)

# Propose pengiriman
df_stock['Propose Kirim'] = np.maximum(0, (df_stock['Kebutuhan/hari'] * df_stock['Durasi Kirim (hari)']) - df_stock['Qty'])
df_stock['Propose Kirim'] = np.ceil(df_stock['Propose Kirim'])

# Sidebar filter
st.sidebar.header("Filter")
pltd_list = sorted(df_stock['PLTD'].unique())
selected_pltd = st.sidebar.multiselect("PLTD", pltd_list, default=pltd_list)
jenis = st.sidebar.multiselect("Jenis Material", ['Preventive', 'Corrective'], default=['Preventive', 'Corrective'])
status_filter = st.sidebar.multiselect("Status", ['🔴 Critical Reorder', '🟡 Warning', '🟢 Aman'],
                                      default=['🔴 Critical Reorder', '🟡 Warning', '🟢 Aman'])

# Filter dataframe
df_view = df_stock.copy()
if selected_pltd: df_view = df_view[df_view['PLTD'].isin(selected_pltd)]
if jenis: df_view = df_view[df_view['Jenis'].isin(jenis)]
if status_filter: df_view = df_view[df_view['Status'].isin(status_filter)]

st.subheader("📋 Tabel Analisis Kebutuhan")
cols_to_show = ['PLTD', 'Kode Material', 'Nama Material', 'Jenis', 'Qty', 'Kebutuhan/bin (PM)',
                'Kebutuhan/bin (Aktual)', 'Kebutuhan/bin (Efektif)', 'Sisa Hari Stok',
                'Durasi Kirim (hari)', 'Status', 'Propose Kirim']
# Tambahkan harga jika ada
if 'Harga Satuan' in df_view.columns:
    cols_to_show.append('Harga Satuan')
st.dataframe(df_view[cols_to_show], use_container_width=True, hide_index=True)

# Visualisasi Lead Time Alert
st.subheader("⏳ Lead Time Alert")
alert_counts = df_view['Status'].value_counts()
st.bar_chart(alert_counts)

# Timeline pemakaian PM (contoh sederhana)
st.subheader("📅 Timeline Pemakaian Material PM")
selected_material = st.selectbox("Pilih Material", df_view[df_view['Jenis']=='Preventive']['Nama Material'].unique() if not df_view.empty else [])
if selected_material:
    row = df_view[df_view['Nama Material']==selected_material].iloc[0]
    days_left = row['Sisa Hari Stok']
    durasi = row['Durasi Kirim (hari)']
    st.metric("Stok Tersisa (hari)", f"{days_left:.0f}")
    st.progress(min(days_left/durasi, 1.0), text="Stok vs Durasi Kirim")