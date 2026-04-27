import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
from difflib import get_close_matches

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

# --- 3. FUNGSI PENDUKUNG ---
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

def ai_find_column(df, target_name):
    """Mencari kolom dengan kemiripan nama (AI-like fuzzy search)."""
    cols = df.columns.tolist()
    # Prioritas 1: Cek kata kunci 'KODE'
    match = [c for c in cols if target_name.upper() in c.upper()]
    if match: return match[0]
    # Prioritas 2: Fuzzy matching
    close_match = get_close_matches(target_name, cols, n=1, cutoff=0.3)
    return close_match[0] if close_match else None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Navigasi", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    if page == "Page 4: Monitoring Transaksi":
        df_raw = load_transaction_data()
        sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique() if not df_raw.empty else [])
        sel_stat = st.multiselect("Status", sorted(df_raw['STATUS'].unique()) if not df_raw.empty else [])
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()))

# --- PAGE 2: STOCK (KOLOM C, D, I) ---
if page == "Page 2: Stock Aktual":
    st.title("📦 Stock Material (Kolom C, D, I)")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        for site in sel_pltd:
            with st.expander(f"📍 LOKASI: {site.upper()}", expanded=True):
                df = load_gsheet_data(PLTD_IDS.get(site))
                if not df.empty:
                    # Mengambil kolom C (indeks 2), D (indeks 3), dan I (indeks 8)
                    try:
                        df_sub = df.iloc[:, [2, 3, 8]]
                        st.dataframe(df_sub, use_container_width=True, hide_index=True)
                    except IndexError:
                        st.warning(f"Format kolom di sheet {site} tidak sesuai (kurang dari 9 kolom).")
                else: st.error(f"Gagal memuat data {site}")

# --- PAGE 3: ANALISA (AI COLUMN SCANNER) ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa Integrasi Data")
    if not sel_pltd:
        st.info("👋 Pilih PLTD di sidebar.")
    else:
        df_stok = load_gsheet_data(PLTD_IDS.get(sel_pltd[0]))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI TARIKAN")
        
        if not df_stok.empty and not df_harga.empty:
            # AI Scanner mencari kolom 'Kode Material'
            c_left = ai_find_column(df_stok, "Kode Material")
            c_right = ai_find_column(df_harga, "Kode Material")
            
            if c_left and c_right:
                df_merged = pd.merge(df_stok, df_harga, left_on=c_left, right_on=c_right, how='left')
                st.success(f"🤖 AI Berhasil memasangkan kolom: '{c_left}' ↔ '{c_right}'")
                st.dataframe(df_merged, use_container_width=True)
            else:
                st.error("🤖 AI Gagal menemukan kolom Kode Material. Pastikan kolom tersedia di kedua file.")
        else: st.warning("Data tidak lengkap.")

# --- PAGE 4: MONITORING (VERSI SEBELUMNYA) ---
elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Monitoring Transaksi PR/MR")
    df_f = load_transaction_data()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]

    if df_f.empty:
        st.warning("Tidak ada data untuk filter ini.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Request", len(df_f))
        m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
        m3.metric("Total Cost", f"Rp {df_f['TOTAL COST'].sum():,.0f}")

        st.subheader("📈 Tren Permintaan")
        st.plotly_chart(px.line(df_f.groupby('Tgl_Str').size().reset_index(name='Count'), x='Tgl_Str', y='Count', markers=True), use_container_width=True)

        st.subheader("📋 Detail Data")
        st.dataframe(df_f[['TANGGAL', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']], use_container_width=True, hide_index=True)

# --- PAGE 1: MENU UTAMA ---
else:
    st.title("🚛 Logistics Dashboard")
    st.info("Pilih menu di sidebar untuk mulai.")
