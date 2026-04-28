import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_master_sheets, load_stock_per_pltd, PLTD_COORDS

st.set_page_config(page_title="Pemakaian Material", layout="wide")
st.title("🔥 Analisis Pemakaian Material & Peta Sebaran")

master = load_master_sheets()
df_pemakaian = master['pemakaian']
df_stock = load_stock_per_pltd()

if df_pemakaian.empty:
    st.warning("Data pemakaian (sheet Gabungan) tidak tersedia.")
    st.stop()

# Pastikan kolom standard ada: asumsikan pemakaian punya 'Tanggal', 'PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Biaya', 'No Transaksi'
# Adaptasi nama kolom fleksibel
df = df_pemakaian.copy()
df.columns = df.columns.str.strip()
# Coba identifikasi kolom penting
col_map = {}
for col in df.columns:
    if 'tanggal' in col.lower(): col_map['Tanggal'] = col
    elif 'pltd' in col.lower() or 'site' in col.lower(): col_map['PLTD'] = col
    elif 'kode' in col.lower() and 'material' in col.lower(): col_map['Kode Material'] = col
    elif 'nama' in col.lower() and 'material' in col.lower(): col_map['Nama Material'] = col
    elif 'qty' in col.lower() or 'quantity' in col.lower(): col_map['Qty'] = col
    elif 'biaya' in col.lower() or 'total' in col.lower() or 'cost' in col.lower(): col_map['Biaya'] = col
    elif 'transaksi' in col.lower() or 'doc' in col.lower() or 'no' in col.lower(): col_map['No Transaksi'] = col

if 'Tanggal' not in col_map:
    st.error("Kolom Tanggal tidak ditemukan. Periksa sheet Gabungan.")
    st.stop()

df['Tanggal'] = pd.to_datetime(df[col_map['Tanggal']], errors='coerce')
df = df.dropna(subset=['Tanggal'])
df['PLTD'] = df[col_map['PLTD']] if 'PLTD' in col_map else 'Tidak Diketahui'
df['Kode Material'] = df[col_map['Kode Material']] if 'Kode Material' in col_map else '-'
df['Nama Material'] = df[col_map['Nama Material']] if 'Nama Material' in col_map else '-'
df['Qty'] = pd.to_numeric(df[col_map['Qty']], errors='coerce').fillna(0)
df['Biaya'] = pd.to_numeric(df[col_map['Biaya']], errors='coerce').fillna(0) if 'Biaya' in col_map else 0
df['No Transaksi'] = df[col_map['No Transaksi']].astype(str) if 'No Transaksi' in col_map else ''
# Flag Need Consume
df['Consume Status'] = df['No Transaksi'].apply(lambda x: 'Need Consume' if x.strip() in ['', 'nan', 'None'] else 'Consumed')

# Filter
st.sidebar.header("Filter")
pltd_list = sorted(df['PLTD'].unique())
selected_pltd = st.sidebar.multiselect("PLTD", pltd_list, default=pltd_list)
kode_list = sorted(df['Kode Material'].unique())
selected_kode = st.sidebar.multiselect("Kode Material", kode_list, default=kode_list)
nama_list = sorted(df['Nama Material'].unique())
selected_nama = st.sidebar.multiselect("Nama Material", nama_list, default=nama_list)
jenis_opt = ['Preventive', 'Corrective']
selected_jenis = st.sidebar.multiselect("Jenis Material", jenis_opt, default=jenis_opt)
consume_opt = ['Consumed', 'Need Consume']
selected_consume = st.sidebar.multiselect("Status Consume", consume_opt, default=consume_opt)

# Filter data
df_f = df.copy()
if selected_pltd: df_f = df_f[df_f['PLTD'].isin(selected_pltd)]
if selected_kode: df_f = df_f[df_f['Kode Material'].isin(selected_kode)]
if selected_nama: df_f = df_f[df_f['Nama Material'].isin(selected_nama)]
if selected_jenis:
    # butuh join dengan df_stock untuk jenis, atau gunakan mapping
    df_stock_map = df_stock[['Kode Material', 'Jenis']].drop_duplicates()
    df_f = df_f.merge(df_stock_map, on='Kode Material', how='left')
    df_f = df_f[df_f['Jenis'].isin(selected_jenis)]
if selected_consume: df_f = df_f[df_f['Consume Status'].isin(selected_consume)]

# KPI
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Qty Pemakaian", f"{df_f['Qty'].sum():,.0f}")
kpi2.metric("Total Biaya", f"Rp {df_f['Biaya'].sum():,.0f}")
kpi3.metric("Transaksi Need Consume", len(df_f[df_f['Consume Status']=='Need Consume']))

# Top 10 Material & Top 10 Site
col1, col2 = st.columns(2)
with col1:
    st.subheader("🔝 Top 10 Material by Qty")
    top_mat = df_f.groupby('Nama Material')['Qty'].sum().nlargest(10)
    st.bar_chart(top_mat)
with col2:
    st.subheader("🏢 Top 10 Site by Qty")
    top_site = df_f.groupby('PLTD')['Qty'].sum().nlargest(10)
    st.bar_chart(top_site)

# Tabel detail Need Consume
st.subheader("⚠️ Highlight Need Consume")
need = df_f[df_f['Consume Status'] == 'Need Consume']
st.dataframe(need[['Tanggal', 'PLTD', 'Kode Material', 'Nama Material', 'Qty', 'No Transaksi']],
             use_container_width=True, hide_index=True)

# Peta sebaran dengan indikator warna (ambil stok kritis dari page 3, tapi di sini simplifikasi)
st.subheader("📍 Peta Sebaran PLTD & Status Stok")
if not df_stock.empty:
    # Dapatkan status kritis sederhana dari stok (qty == 0 atau rendah)
    df_stock_map = df_stock.groupby('PLTD')['Qty'].sum().reset_index()
    df_stock_map['status'] = df_stock_map['Qty'].apply(lambda x: '🔴 Kritis' if x < 10 else '🟢 Aman')
    df_stock_map['lat'] = df_stock_map['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[0])
    df_stock_map['lon'] = df_stock_map['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[1])
    df_stock_map = df_stock_map.dropna(subset=['lat'])
    color_map = {'🔴 Kritis': 'red', '🟢 Aman': 'green'}
    fig = px.scatter_mapbox(df_stock_map, lat='lat', lon='lon', color='status',
                            color_discrete_map=color_map,
                            hover_name='PLTD', hover_data=['Qty'],
                            zoom=4, height=500)
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Data stok tidak tersedia untuk peta.")