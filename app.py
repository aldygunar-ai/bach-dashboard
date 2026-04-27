import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- 1. KONFIGURASI & STYLE ---
st.set_page_config(page_title="Dashboard Project Bach", layout="wide")

TEMA_BIRU = "#0E2F56"

st.markdown(f"""
    <style>
    .main {{ background-color: #F8F9FA; }}
    [data-testid="stSidebar"] {{ background-color: {TEMA_BIRU} !important; }}
    .sidebar-title {{
        color: white; font-size: 20px; font-weight: 800; text-align: center;
        margin-bottom: 25px; padding: 10px; border-bottom: 1px solid #ffffff33;
    }}
    [data-testid="stSidebar"] label p {{ color: white !important; font-weight: 500 !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px; font-weight: 800; color: {TEMA_BIRU}; }}
    .stPlotlyChart {{ background-color: white; border-radius: 12px; padding: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE LINK ---
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

# --- 3. HELPER FUNCTIONS ---
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
    # Geo Data
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

def ai_smart_column_search(df, target_keywords):
    """Mencari kolom dengan membersihkan nama kolom terlebih dahulu."""
    cleaned_cols = {col: col.strip().replace('\n', ' ').upper() for col in df.columns}
    for original, cleaned in cleaned_cols.items():
        if any(kw.upper() in cleaned for kw in target_keywords):
            return original
    return None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Menu Dashboard", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    if page == "Page 4: Monitoring Transaksi":
        df_raw = load_transaction_data()
        sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique() if not df_raw.empty else [])
        sel_year = st.multiselect("Tahun", sorted(df_raw['Tahun'].unique(), reverse=True) if not df_raw.empty else [])
        sel_stat = st.multiselect("Status", sorted(df_raw['STATUS'].unique()) if not df_raw.empty else [])
        sel_site = st.multiselect("Site (WH Tujuan)", sorted(df_raw['WH TUJUAN'].dropna().unique()) if not df_raw.empty else [])
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()))

# --- PAGE 1: MENU UTAMA ---
if page == "Page 1: Menu Utama":
    st.title("🚛 Dashboard Project Bach")
    st.info("Gunakan navigasi di sisi kiri untuk memantau stok dan transaksi.")
    col1, col2 = st.columns(2)
    with col1: st.success("📦 **Stok Aktual:** Cek ketersediaan sparepart per PLTD.")
    with col2: st.warning("📊 **Monitoring Transaksi:** Pantau PR/MR dan pengiriman.")

# --- PAGE 2: STOCK AKTUAL (TABS UNTUK MULTI-SELECT) ---
elif page == "Page 2: Stock Aktual":
    st.title("📦 Stock Material PLTD (Kolom C, D, I)")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        # Gunakan TABS agar tidak memanjang ke bawah
        tabs = st.tabs([f"📍 {site}" for site in sel_pltd])
        for i, site in enumerate(sel_pltd):
            with tabs[i]:
                df = load_gsheet_data(PLTD_IDS.get(site))
                if not df.empty:
                    try:
                        # Mengambil kolom C (index 2), D (index 3), I (index 8)
                        df_view = df.iloc[:, [2, 3, 8]]
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    except Exception:
                        st.error(f"Format kolom di {site} tidak sesuai.")
                else: st.error("Data tidak ditemukan.")

# --- PAGE 3: ANALISA & PROPOSE (AI SMART SEARCH) ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose Pengiriman")
    if not sel_pltd:
        st.info("👋 Pilih minimal satu PLTD di sidebar.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI TARIKAN")
        
        if not df_stok.empty and not df_harga.empty:
            # AI mencari kolom Kode di kedua df
            c_stok = ai_smart_column_search(df_stok, ['KODE', 'PART NUMBER'])
            c_harga = ai_smart_column_search(df_harga, ['KODE', 'PART NUMBER'])
            
            if c_stok and c_harga:
                df_merged = pd.merge(df_stok, df_harga, left_on=c_stok, right_on=c_harga, how='left')
                st.success(f"🤖 AI Berhasil memetakan kolom '{c_stok}' dan '{c_harga}'")
                st.dataframe(df_merged, use_container_width=True)
            else:
                st.error("🤖 AI Gagal menemukan kolom Kode Material. Pastikan ada kolom bernama 'KODE' atau 'PART NUMBER'.")
        else: st.warning("Data belum tersedia.")

# --- PAGE 4: MONITORING TRANSAKSI (RESTORASI TOTAL) ---
elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Monitoring Transaksi PR/MR")
    if not (sel_proj or sel_year or sel_stat or sel_site):
        st.info("👋 Pilih filter di sidebar untuk memuat dashboard.")
        st.stop()

    df_f = df_raw.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
    if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

    # KPI TOP
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Order", f"{len(df_f)}")
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    # Grafik Tren (Garis Biru + Angka)
    st.subheader("📈 Tren Permintaan Harian")
    trend = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    fig_tr = px.line(trend, x='Tgl_Str', y='Requests', markers=True, text='Requests', color_discrete_sequence=[TEMA_BIRU])
    fig_tr.update_traces(textposition="top center")
    st.plotly_chart(fig_tr, use_container_width=True)

    # Top Site & Top Material
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏢 Top Site Request (QTY)")
        top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_site = px.bar(top_site, x='WH TUJUAN', y='QTY', text_auto='.2s', color_discrete_sequence=[TEMA_BIRU])
        st.plotly_chart(fig_site, use_container_width=True)
    with c2:
        st.subheader("🔝 Top Requested Items")
        top_item = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_item = px.bar(top_item, x='ITEM NAME', y='QTY', text_auto='.2s', color_discrete_sequence=['#4B8BBE'])
        st.plotly_chart(fig_item, use_container_width=True)

    # Tabel Detail
    st.subheader("⚠️ Highlight Outstanding (Belum Terkirim)")
    df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
    st.dataframe(df_out[['TANGGAL', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']], use_container_width=True, hide_index=True)

    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], use_container_width=True, hide_index=True)

    # Peta
    st.subheader("📍 Sebaran Lokasi Request")
    st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3)
