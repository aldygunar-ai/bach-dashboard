import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Dashboard Project Bach", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #0E2F56 !important; }
    .sidebar-title {
        color: white; font-size: 20px; font-weight: 800; text-align: center;
        margin-bottom: 25px; padding: 10px; border-bottom: 1px solid #ffffff33;
    }
    [data-testid="stSidebar"] label p { color: white !important; font-weight: 500 !important; }
    [data-testid="stSidebar"] button svg, button[kind="headerNoSpacing"] svg { fill: white !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0E2F56; }
    .stPlotlyChart { background-color: white; border-radius: 12px; padding: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. LOAD DATA
URL_OPS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

@st.cache_data
def load_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res_ops = requests.get(URL_OPS, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(res_ops.content))
        df_ops['PROJECT'] = 'PROJECT PLTD'
    except: df_ops = pd.DataFrame()
    
    try:
        res_das = requests.get(URL_DAS, headers=headers, timeout=20)
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
    
    geo_data = {'ACEH': [4.69, 96.74], 'BALI': [-8.34, 115.09], 'BANGKA': [-2.13, 106.11],
                'JAKARTA': [-6.20, 106.84], 'KALBAR': [-0.27, 109.97], 'MALUKU': [-3.23, 130.14],
                'PAPUA': [-4.26, 138.08], 'SUMUT': [2.11, 99.13], 'SULSEL': [-5.14, 119.43]}
    df['lat'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[0])
    df['lon'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[1])
    return df

df_raw = load_data()

# --- 3. SIDEBAR & LOGIKA RESET (VERSI PERBAIKAN TOTAL) ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    
    # Inisialisasi default jika belum ada di session_state
    if 'sel_proj' not in st.session_state:
        st.session_state.sel_proj = list(df_raw['PROJECT'].unique())
    if 'sel_year' not in st.session_state:
        st.session_state.sel_year = ["2026"]
    if 'sel_month' not in st.session_state:
        st.session_state.sel_month = []
    if 'sel_stat' not in st.session_state:
        st.session_state.sel_stat = []
    if 'sel_site' not in st.session_state:
        st.session_state.sel_site = []

    # Pasang widget dengan session_state
    sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique(), key='sel_proj')
    sel_year = st.multiselect("Tahun", sorted(df_raw['Tahun'].unique(), reverse=True), key='sel_year')
    sel_month = st.multiselect("Bulan", df_raw['Bulan'].unique(), key='sel_month')
    sel_stat = st.multiselect("Status", sorted(df_raw['STATUS'].unique()), key='sel_stat')
    sel_site = st.multiselect("Site (WH Tujuan)", sorted(df_raw['WH TUJUAN'].dropna().unique()), key='sel_site')
    
    st.divider()
    
    # Tombol Reset yang membersihkan isi dropdown secara fisik
    if st.button("🔄 Clear All Filters", use_container_width=True):
        st.session_state.sel_proj = []
        st.session_state.sel_year = []
        st.session_state.sel_month = []
        st.session_state.sel_stat = []
        st.session_state.sel_site = []
        st.rerun()

# APLIKASI FILTER
df_f = df_raw[df_raw['PROJECT'].isin(sel_proj)]
if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
if sel_month: df_f = df_f[df_f['Bulan'].isin(sel_month)]
if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

# --- 4. DASHBOARD CONTENT ---
st.title("📊 Dashboard Project Bach") # Judul Baru

# KPI ROW
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Order", f"{len(df_f)}")
m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

st.markdown("---")

# ROW 1: TREN HARIAN
st.subheader("📈 Tren Permintaan Harian")
trend_data = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
fig_tr = px.line(trend_data, x='Tgl_Str', y='Requests', markers=True, text='Requests', color_discrete_sequence=['#0E2F56'])
fig_tr.update_traces(textposition="top center")
fig_tr.update_layout(height=350, margin=dict(t=30, b=20, l=0, r=0))
st.plotly_chart(fig_tr, use_container_width=True)

st.markdown("---")

# ROW 2: TOP SITE & TOP ITEM
c_site, c_item = st.columns(2)
with c_site:
    st.subheader("🏢 Top Site Request (QTY)")
    top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(8).reset_index()
    fig_site = px.bar(top_site, x='WH TUJUAN', y='QTY', text_auto=',', color='QTY', color_continuous_scale='Blues')
    fig_site.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_site, use_container_width=True)

with c_item:
    st.subheader("🔝 Top Requested Items")
    top_item = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(8).reset_index()
    fig_item = px.bar(top_item, x='ITEM NAME', y='QTY', text_auto=',', color_discrete_sequence=['#4B8BBE'])
    fig_item.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_item, use_container_width=True)

st.markdown("---")

# ROW 3: TABLES
st.subheader("⚠️ Highlight Outstanding")
df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
st.dataframe(df_out[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']], use_container_width=True, hide_index=True)

st.subheader("📋 Detail Movement Record")
st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], use_container_width=True, hide_index=True)

st.markdown("---")

# ROW 4: MAP (PALING BAWAH)
st.subheader("📍 Area Operasional Project")
st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3, height=400)
