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
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    return df

@st.cache_data(ttl=600)
def load_gsheet_data(sheet_id):
    if not sheet_id: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        # Hapus kolom kosong agar tidak merusak indexing
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df
    except:
        return pd.DataFrame()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Menu Dashboard", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    if page == "Page 4: Monitoring Transaksi":
        df_raw = load_transaction_data()
        sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique() if not df_raw.empty else [])
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()))

# --- 5. LOGIKA HALAMAN ---

if page == "Page 1: Menu Utama":
    st.title("🚛 Dashboard Project Bach")
    st.info("Pilih menu di sidebar untuk memantau stok.")

elif page == "Page 2: Stock Aktual":
    st.title("📦 Perbandingan Stock Aktual")
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        full_data = []
        
        for site in sel_pltd:
            df = load_gsheet_data(PLTD_IDS.get(site))
            if not df.empty:
                try:
                    # Sesuai instruksi: Kolom C (Index 2) = Nama & Type, Kolom I (Index 8) = QTY
                    # Kita ambil kolom 0 (Kode) juga agar bisa merge dengan benar
                    df_sub = df.iloc[:, [0, 2, 8]].copy()
                    df_sub.columns = ['KODE', 'NAMA_TYPE', 'QTY']
                    
                    # Konversi QTY ke angka agar tidak error saat diproses
                    df_sub['QTY'] = pd.to_numeric(df_sub['QTY'], errors='coerce').fillna(0)
                    
                    # Identifikasi Type (Preventive / Corrective) berdasarkan isi teks di kolom C
                    df_sub['TYPE'] = df_sub['NAMA_TYPE'].apply(lambda x: 'PREVENTIVE' if 'PREVENTIVE' in str(x).upper() else 'CORRECTIVE')
                    
                    # Tambahkan identitas PLTD
                    df_sub['PLTD'] = site.upper()
                    full_data.append(df_sub)
                except Exception as e:
                    st.error(f"Format kolom di {site} tidak sesuai.")

        if full_data:
            df_combined = pd.concat(full_data, ignore_index=True)
            
            # Pivot data agar PLTD jadi header ke samping
            df_pivot = df_combined.pivot_table(
                index=['KODE', 'NAMA_TYPE', 'TYPE'], 
                columns='PLTD', 
                values='QTY', 
                aggfunc='sum'
            ).reset_index().fillna(0)

            # --- TAMPILAN SPLIT ---
            st.subheader("🛠️ Kelompok: PREVENTIVE MAINTENANCE")
            df_prev = df_pivot[df_pivot['TYPE'] == 'PREVENTIVE']
            st.dataframe(df_prev.drop(columns=['TYPE']), use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.subheader("🆘 Kelompok: CORRECTIVE MAINTENANCE")
            df_corr = df_pivot[df_pivot['TYPE'] == 'CORRECTIVE']
            st.dataframe(df_corr.drop(columns=['TYPE']), use_container_width=True, hide_index=True)
        else:
            st.warning("Tidak ada data yang dapat ditampilkan.")

elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose")
    st.info("Fitur Analisa Data.")

elif page == "Page 4: Monitoring Transaksi":
    st.title("📊 Monitoring Transaksi")
    if not df_raw.empty:
        st.dataframe(df_raw, use_container_width=True)
