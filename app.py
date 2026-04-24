import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# 1. KONFIGURASI HALAMAN & THEME MODERN
st.set_page_config(page_title="Bach Logistics Dashboard", layout="wide")

st.markdown("""
    <style>
    /* Global Background */
    .main { background-color: #F8F9FA; }
    
    /* Sidebar PT BACH Theme (Biru Tua) */
    [data-testid="stSidebar"] {
        background-color: #0E2F56 !important;
    }
    
    /* Header Sidebar (Teks Pengganti Logo) */
    .sidebar-title {
        color: white;
        font-size: 20px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 25px;
        padding: 10px;
        border-bottom: 1px solid #ffffff33;
    }

    /* FIX: Visibilitas Label Filter & Tombol Minimize agar Putih Terang */
    [data-testid="stSidebar"] label p {
        color: white !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] button svg, 
    button[kind="headerNoSpacing"] svg {
        fill: white !important;
    }
    
    /* Card Metric Styling */
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0E2F56; }
    
    /* Chart Container Styling */
    .stPlotlyChart { 
        background-color: white; 
        border-radius: 12px; 
        padding: 15px; 
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LOAD DATA (Koneksi ke StatusPerPLTD)
URL_OPS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

@st.cache_data
def load_data(url_ops, url_das):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Load Data Operasional -> Ubah Label jadi PROJECT PLTD
    try:
        res_ops = requests.get(url_ops, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(res_ops.content))
        df_ops['PROJECT'] = 'PROJECT PLTD' # PERUBAHAN DISINI
    except: df_ops = pd.DataFrame()
    
    # Load Data Project DAS
    try:
        res_das = requests.get(url_das, headers=headers, timeout=20)
        df_das = pd.read_excel(io.BytesIO(res_das.content))
        df_das['PROJECT'] = 'PROJECT DAS'
    except: df_das = pd.DataFrame()
    
    df = pd.concat([df_ops, df_das], ignore_index=True)
    
    if not df.empty and 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
        df['Tahun'] = df['TANGGAL'].dt.year.astype(str)
        df['Bulan'] = df['TANGGAL'].dt.strftime('%B')
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    
    # Mapping Koordinat
    geo_data = {'ACEH': [4.69, 96.74], 'BALI': [-8.34, 115.09], 'BANGKA': [-2.13, 106.11],
                'JAKARTA': [-6.20, 106.84], 'KALBAR': [-0.27, 109.97], 'MALUKU': [-3.23, 130.14],
                'PAPUA': [-4.26, 138.08], 'SUMUT': [2.11, 99.13], 'SULSEL': [-5.14, 119.43]}
    df['lat'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[0])
    df['lon'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[1])
    return df

df = load_data(URL_OPS, URL_DAS)

# --- 3. SIDEBAR: CONTROL PANEL (FILTERS) ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    
    # Filter Project (Sekarang menampilkan PROJECT PLTD & PROJECT DAS)
    sel_proj = st.multiselect("Project", df['PROJECT'].unique(), default=df['PROJECT'].unique())
    sel_year = st.multiselect("Tahun", sorted(df['Tahun'].unique(), reverse=True), default=["2026"])
    sel_month = st.multiselect("Bulan", df['Bulan'].unique())
    sel_stat = st.multiselect("Status", sorted(df['STATUS'].unique()))
    sel_site = st.multiselect("Site (WH Tujuan)", sorted(df['WH TUJUAN'].dropna().unique()))
    
    st.divider()
    if st.button("🔄 Reset Dashboard", use_container_width=True):
        st.rerun()

# EKSEKUSI FILTER
df_f = df[df['PROJECT'].isin(sel_proj)]
if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
if sel_month: df_f = df_f[df_f['Bulan'].isin(sel_month)]
if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

# --- 4. MAIN CONTENT: LOGISTICS COMMAND CENTER ---
st.title("📦 Dashboard Project Bach")

# KPI SUMMARY ROW
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Order", f"{len(df_f)}")
m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())
rate = (len(df_f[df_f['STATUS']=='DELIVERED'])/len(df_f)*100) if len(df_f)>0 else 0
m5.metric("Delivery Rate", f"{rate:.1f}%")

st.markdown("---")

# ROW 1: TREN HARIAN & PETA PELENGKAP
c_trend, c_map = st.columns([2, 1])
with c_trend:
    st.subheader("📈 Tren Permintaan Harian")
    trend_data = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    fig_tr = px.line(trend_data, x='Tgl_Str', y='Requests', markers=True, 
                     text='Requests', color_discrete_sequence=['#0E2F56'])
    fig_tr.update_traces(textposition="top center")
    fig_tr.update_layout(height=300, margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig_tr, use_container_width=True)

with c_map:
    st.subheader("📍 Area Operasional")
    st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3, height=300)

# ROW 2: TOP ANALYSIS (Interaktif & Ada Angka)
c_site, c_item = st.columns(2)
with c_site:
    st.subheader("🏢 Top Site Request (QTY)")
    top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_site = px.bar(top_site, x='QTY', y='WH TUJUAN', orientation='h', text_auto=',', 
                      color='QTY', color_continuous_scale='Blues')
    fig_site.update_layout(height=350, yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_site, use_container_width=True)

with c_item:
    st.subheader("🔝 Top Requested Items")
    top_item = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_item = px.bar(top_item, x='QTY', y='ITEM NAME', orientation='h', text_auto=',', 
                      color_discrete_sequence=['#4B8BBE'])
    fig_item.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_item, use_container_width=True)

st.markdown("---")

# ROW 3: HIGHLIGHT OUTSTANDING
st.subheader("⚠️ Highlight Outstanding (Non-Delivered)")
# Filter semua yang bukan Delivered atau Cancel
df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
st.dataframe(df_out[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']], 
             use_container_width=True, hide_index=True)

st.markdown("---")

# ROW 4: DETAIL DATA
st.subheader("📋 Detail Movement Record & Status")
st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], 
             use_container_width=True, hide_index=True)
