import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import numpy as np

# --- 1. KONFIGURASI HALAMAN & STYLE (ASLI DARI ANDA) ---
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

# --- 2. DATABASE LINK (SharePoint & Google Sheets) ---
URL_OPS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

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
    if sheet_name: url += f"&sheet={sheet_name.replace(' ', '+')}"
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

df_raw = load_transaction_data()

# --- 4. SIDEBAR & LOGIKA RESET ---
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

def do_reset():
    st.session_state.reset_counter += 1

with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Menu Dashboard", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    c = st.session_state.reset_counter
    
    if page == "Page 4: Monitoring Transaksi":
        # FILTER ASLI PAGE 4 (JANGAN DIUBAH)
        sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique() if not df_raw.empty else [], key=f'p_{c}')
        sel_year = st.multiselect("Tahun", sorted(df_raw['Tahun'].unique(), reverse=True) if not df_raw.empty else [], key=f'y_{c}')
        sel_month = st.multiselect("Bulan", df_raw['Bulan'].unique() if not df_raw.empty else [], key=f'm_{c}')
        sel_stat = st.multiselect("Status", sorted(df_raw['STATUS'].unique()) if not df_raw.empty else [], key=f's_{c}')
        sel_site = st.multiselect("Site (WH Tujuan)", sorted(df_raw['WH TUJUAN'].dropna().unique()) if not df_raw.empty else [], key=f'st_{c}')
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()), default=[], key=f'pltd_{c}')

    st.divider()
    st.button("🔄 Clear All Filters", on_click=do_reset, use_container_width=True)

# --- PAGE 1: MENU UTAMA ---
if page == "Page 1: Menu Utama":
    st.title("🚛 Dashboard Project Bach")
    st.info("Selamat datang. Pilih menu di samping untuk melihat data.")
    col1, col2 = st.columns(2)
    with col1:
        st.success("### Page 2 & 3\nMonitoring Stok & Analisa (Google Sheets)")
    with col2:
        st.warning("### Page 4\nMonitoring Transaksi PR/MR (SharePoint)")

# --- PAGE 2: STOCK AKTUAL ---
elif page == "Page 2: Stock Aktual":
    st.title("📦 Stock Material PLTD")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        if not df_stok.empty:
            # HANYA NAMA, KODE, SISA STOCK
            df_stok.columns = [c.strip() for c in df_stok.columns]
            cols = [c for c in df_stok.columns if any(x in c.upper() for x in ['KODE MATERIAL', 'NAMA MATERIAL', 'SISA STOCK'])]
            st.dataframe(df_stok[cols] if cols else df_stok, use_container_width=True, hide_index=True)
        else: st.error("Data tidak tersedia.")

# --- PAGE 3: ANALISA & PROPOSE (FIX KEYERROR) ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose Pengiriman")
    if not sel_pltd:
        st.info("👋 Pilih PLTD di sidebar.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI TARIKAN")
        if not df_stok.empty and not df_harga.empty:
            df_stok.columns = [c.strip() for c in df_stok.columns]
            df_harga.columns = [c.strip() for c in df_harga.columns]
            c_left = next((c for c in df_stok.columns if 'KODE' in c.upper()), None)
            c_right = next((c for c in df_harga.columns if 'KODE' in c.upper()), None)
            if c_left and c_right:
                df_merged = pd.merge(df_stok, df_harga, left_on=c_left, right_on=c_right, how='left')
                st.dataframe(df_merged, use_container_width=True)
            else: st.error("Kolom Kode Material tidak ditemukan.")

# --- PAGE 4: MONITORING TRANSAKSI (ASLI DARI ANDA - JANGAN DIUBAH) ---
elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Dashboard Project Bach")
    
    if not (sel_proj or sel_year or sel_month or sel_stat or sel_site):
        st.info("👋 Selamat Datang! Silakan pilih filter di samping kiri untuk menampilkan data.")
        st.stop()

    df_f = df_raw.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_month: df_f = df_f[df_f['Bulan'].isin(sel_month)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
    if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

    # KPI Top
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Order", f"{len(df_f)}")
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    st.markdown("---")
    st.subheader("📈 Tren Permintaan Harian")
    trend_data = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    st.plotly_chart(px.line(trend_data, x='Tgl_Str', y='Requests', markers=True, text='Requests', color_discrete_sequence=['#0E2F56']), use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏢 Top Site Request (QTY)")
        top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(8).reset_index()
        st.plotly_chart(px.bar(top_site, x='WH TUJUAN', y='QTY', text_auto=',', color='QTY', color_continuous_scale='Blues'), use_container_width=True)
    with c2:
        st.subheader("🔝 Top Requested Items")
        top_item = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(8).reset_index()
        st.plotly_chart(px.bar(top_item, x='ITEM NAME', y='QTY', text_auto=',', color_discrete_sequence=['#4B8BBE']), use_container_width=True)

    st.markdown("---")
    st.subheader("⚠️ Highlight Outstanding")
    df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
    st.dataframe(df_out[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']], use_container_width=True, hide_index=True)

    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📍 Area Operasional Project")
    st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3, height=400)
