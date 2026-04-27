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
    return df

@st.cache_data(ttl=600)
def load_gsheet_data(sheet_id, sheet_name=None):
    if not sheet_id: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    if sheet_name: url += f"&sheet={sheet_name.replace(' ', '+')}"
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

def ai_smart_column_search(df, target_keywords):
    """Mencari nama kolom asli berdasarkan kecocokan keyword (Case-Insensitive)."""
    cleaned_cols = {col: str(col).strip().replace('\n', ' ').upper() for col in df.columns}
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
    st.info("Sistem Pemantauan Stok dan Transaksi.")

# --- PAGE 2: STOCK AKTUAL (AI AUTO-MAPPING) ---
elif page == "Page 2: Stock Aktual":
    st.title("📦 Perbandingan Stock Aktual (AI Table)")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        main_df = None
        
        for site in sel_pltd:
            df = load_gsheet_data(PLTD_IDS.get(site))
            if not df.empty:
                # 🤖 AI Mencari Kolom yang Sesuai
                c_kode = ai_smart_column_search(df, ['KODE', 'PART NUMBER'])
                c_nama = ai_smart_column_search(df, ['NAMA MATERIAL', 'DESCRIPTION', 'NAMA BARANG'])
                c_qty  = ai_smart_column_search(df, ['QTY', 'STOCK', 'SISA', 'AKTUAL'])
                
                if c_kode and c_nama and c_qty:
                    # Ambil hanya 3 kolom yang ditemukan
                    df_sub = df[[c_kode, c_nama, c_qty]].copy()
                    
                    # Standarisasi Nama Kolom Kunci agar bisa di-Merge
                    df_sub = df_sub.rename(columns={
                        c_kode: "KODE MATERIAL",
                        c_nama: "NAMA MATERIAL",
                        c_qty: f"STOK_{site.upper()}"
                    })
                    
                    # Membersihkan data dari baris kosong
                    df_sub = df_sub.dropna(subset=["KODE MATERIAL"])
                    
                    if main_df is None:
                        main_df = df_sub
                    else:
                        # Join otomatis ke samping berdasarkan Kode & Nama
                        main_df = pd.merge(main_df, df_sub, on=["KODE MATERIAL", "NAMA MATERIAL"], how='outer')
                else:
                    st.warning(f"⚠️ AI tidak menemukan kolom lengkap di {site}. Pastikan ada kolom Kode, Nama, dan Qty.")
            else:
                st.error(f"❌ Gagal memuat data dari {site}.")
        
        if main_df is not None:
            # Mengisi data kosong dengan 0 agar tabel rapi
            st.dataframe(main_df.fillna(0), use_container_width=True, hide_index=True)

# --- PAGE 3: ANALISA ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose")
    if not sel_pltd:
        st.info("👋 Pilih PLTD di sidebar.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI TARIKAN")
        if not df_stok.empty and not df_harga.empty:
            c_s = ai_smart_column_search(df_stok, ['KODE', 'PART NUMBER'])
            c_h = ai_smart_column_search(df_harga, ['KODE', 'PART NUMBER'])
            if c_s and c_h:
                df_merged = pd.merge(df_stok, df_harga, left_on=c_s, right_on=c_h, how='left')
                st.success(f"🤖 Data Terhubung via {c_s}")
                st.dataframe(df_merged, use_container_width=True)
            else: st.error("Kolom Kode tidak ditemukan.")

# --- PAGE 4: MONITORING ---
elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Monitoring Transaksi PR/MR")
    if not (sel_proj or sel_year or sel_stat or sel_site):
        st.info("👋 Pilih filter di sidebar.")
        st.stop()
    
    df_f = df_raw.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
    if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Order", len(df_f))
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    st.subheader("📈 Tren Permintaan")
    trend = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    st.plotly_chart(px.line(trend, x='Tgl_Str', y='Requests', markers=True, text='Requests', color_discrete_sequence=[TEMA_BIRU]), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏢 Top Site Request")
        ts = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(ts, x='WH TUJUAN', y='QTY', text_auto='.2s', color_discrete_sequence=[TEMA_BIRU]), use_container_width=True)
    with c2:
        st.subheader("🔝 Top Requested Items")
        ti = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(ti, x='ITEM NAME', y='QTY', text_auto='.2s', color_discrete_sequence=['#4B8BBE']), use_container_width=True)

    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']], use_container_width=True, hide_index=True)
