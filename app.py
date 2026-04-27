import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import numpy as np

# --- 1. KONFIGURASI HALAMAN & STYLE ---
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

# --- 2. DATABASE LINK (Google Sheets & SharePoint) ---
PLTD_IDS = {
    "Pemaron": "1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI",
    "Mangoli": "1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s",
    "Tayan": "1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo",
    "Timika": "1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04",
    "Bobong": "1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM",
    "Merawang": "1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8",
    "Air Anyir": "10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o",
    "Padang Manggar": "1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s",
    "Krueng Raya": "1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s",
    "Lueng Bata": "1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g",
    "Ulee Kareng": "1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU"
}

ID_GABUNGAN_D365 = "1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs"
URL_OPS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

# --- 3. DATA LOADERS ---
@st.cache_data
def load_transaction_data():
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
    
    # Geodata untuk Map
    geo_data = {'ACEH': [4.69, 96.74], 'BALI': [-8.34, 115.09], 'BANGKA': [-2.13, 106.11],
                'JAKARTA': [-6.20, 106.84], 'KALBAR': [-0.27, 109.97], 'MALUKU': [-3.23, 130.14],
                'PAPUA': [-4.26, 138.08], 'SUMUT': [2.11, 99.13], 'SULSEL': [-5.14, 119.43]}
    if not df.empty and 'PROVINCE' in df.columns:
        df['lat'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[0])
        df['lon'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[1])
    return df

@st.cache_data(ttl=600)
def load_gsheet_data(sheet_id, sheet_name=None):
    if not sheet_id: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    if sheet_name: url += f"&sheet={sheet_name}"
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

df_transaksi = load_transaction_data()

# --- 4. SIDEBAR & NAVIGASI ---
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

def do_reset():
    st.session_state.reset_counter += 1

with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Pilih Halaman", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    st.subheader("Filter Dashboard")
    c = st.session_state.reset_counter
    
    # Filter Bersih (Default Kosong)
    if page == "Page 4: Monitoring Transaksi":
        sel_proj = st.multiselect("Project", df_transaksi['PROJECT'].unique() if not df_transaksi.empty else [], default=[], key=f'p_{c}')
        sel_year = st.multiselect("Tahun", sorted(df_transaksi['Tahun'].unique(), reverse=True) if not df_transaksi.empty else [], default=[], key=f'y_{c}')
        sel_stat = st.multiselect("Status", sorted(df_transaksi['STATUS'].unique()) if not df_transaksi.empty else [], key=f's_{c}')
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()), default=[], key=f'pltd_{c}')
        sel_jenis = st.selectbox("Jenis Material", ["Semua", "Preventive", "Corrective"], key=f'jns_{c}')

    st.divider()
    st.button("🔄 Clear All Filters", on_click=do_reset, use_container_width=True)

# --- PAGE 1: MENU UTAMA ---
if page == "Page 1: Menu Utama":
    st.title("🚛 Logistics Command Center - Bach")
    col1, col2 = st.columns(2)
    with col1:
        st.info("### Cek Stock Material\nPantau posisi stok terkini di setiap site PLTD.")
    with col2:
        st.info("### Monitoring Transaksi\nDashboard real-time PR/MR dari SharePoint.")

# --- PAGE 2: STOCK AKTUAL (Google Sheets) ---
elif page == "Page 2: Stock Aktual":
    st.title("📦 Stock Material PLTD Aktual")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar untuk melihat stok.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        st.dataframe(df_stok, use_container_width=True)

# --- PAGE 3: ANALISA & PROPOSE ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose Pengiriman")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar untuk analisa kebutuhan.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI+TARIKAN")
        if not df_stok.empty and not df_harga.empty:
            df_merged = pd.merge(df_stok, df_harga, on='Kode Material', how='left')
            st.dataframe(df_merged, use_container_width=True)

# --- PAGE 4: MONITORING TRANSAKSI (Logic dari Koding Anda) ---
elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Monitoring Transaksi PR/MR")
    
    if not (sel_proj or sel_year or sel_stat):
        st.info("👋 Silakan pilih filter di samping kiri untuk menampilkan data transaksi.")
        st.stop()

    df_f = df_transaksi.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]

    # KPI Top
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Order", f"{len(df_f)}")
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    # Visualisasi Tren & Top Item
    st.plotly_chart(px.line(df_f.groupby('Tgl_Str').size().reset_index(name='Requests'), x='Tgl_Str', y='Requests', markers=True), use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(8).reset_index(), x='WH TUJUAN', y='QTY', color='QTY'), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(8).reset_index(), x='ITEM NAME', y='QTY'), use_container_width=True)

    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], use_container_width=True, hide_index=True)

    st.subheader("📍 Area Operasional")
    st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3)
