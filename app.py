import streamlit as st
import pandas as pd
import requests
import io

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA HAFALAN PREVENTIVE ---
LIST_KODE_PREVENTIVE = [
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076', '3629140', 
    'AF872', 'AF25278', 'AHO1135', '5413003', '3015257', '5412990',
    '5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108',
    'RIMULA R4 X 15W-40'
]

# --- 3. DATABASE LINK ---
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

# --- 4. HELPER FUNCTIONS ---
@st.cache_data(ttl=600)
def load_gsheet_data(sheet_id):
    if not sheet_id: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Menu Dashboard", ["Page 1: Menu Utama", "Page 2: Stock Aktual"])
    st.divider()
    sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()))

# --- 6. LOGIKA HALAMAN ---

if page == "Page 1: Menu Utama":
    st.title("🚛 Dashboard Project Bach")
    st.info("Pilih PLTD di sidebar untuk melihat perbandingan stok.")

elif page == "Page 2: Stock Aktual":
    st.title("📦 Perbandingan Stock Aktual (Normalized)")
    
    if not sel_pltd:
        st.info("👋 Silakan pilih PLTD di sidebar.")
    else:
        all_dfs = []
        for site in sel_pltd:
            df = load_gsheet_data(PLTD_IDS.get(site))
            if not df.empty:
                try:
                    # Ambil A=0(Kode), C=2(Nama), D=3(Type), I=8(Qty)
                    df_sub = df.iloc[:, [0, 2, 3, 8]].copy()
                    df_sub.columns = ['KODE', 'NAMA MATERIAL', 'TYPE MATERIAL', 'QTY']
                    
                    # --- NORMALISASI DATA (KUNCI AGAR TIDAK BERANTAKAN) ---
                    df_sub['KODE'] = df_sub['KODE'].astype(str).str.strip().str.upper()
                    df_sub['NAMA MATERIAL'] = df_sub['NAMA MATERIAL'].astype(str).str.strip().str.upper()
                    df_sub['TYPE MATERIAL'] = df_sub['TYPE MATERIAL'].astype(str).str.strip().str.upper()
                    df_sub['QTY'] = pd.to_numeric(df_sub['QTY'], errors='coerce').fillna(0)
                    
                    # Klasifikasi Berdasarkan Hafalan
                    def classify_logic(row):
                        kode_val = str(row['KODE'])
                        if not kode_val or kode_val == 'NAN' or kode_val == '':
                            return 'CORRECTIVE'
                        if any(p.upper() in kode_val for p in LIST_KODE_PREVENTIVE):
                            return 'PREVENTIVE'
                        return 'CORRECTIVE'
                    
                    df_sub['KATEGORI'] = df_sub.apply(classify_logic, axis=1)
                    df_sub['PLTD'] = site.upper()
                    all_dfs.append(df_sub)
                except:
                    st.error(f"Gagal memproses kolom di {site}.")

        if all_dfs:
            df_final = pd.concat(all_dfs, ignore_index=True)
            
            # Pivot Table: Menggabungkan data yang Nama & Type-nya sama
            df_pivot = df_final.pivot_table(
                index=['KODE', 'NAMA MATERIAL', 'TYPE MATERIAL', 'KATEGORI'],
                columns='PLTD',
                values='QTY',
                aggfunc='sum'
            ).reset_index().fillna(0)

            # Bagian Tabel PM
            st.subheader("🛠️ KELOMPOK: PREVENTIVE MAINTENANCE")
            df_p = df_pivot[df_pivot['KATEGORI'] == 'PREVENTIVE'].drop(columns=['KATEGORI', 'KODE'])
            if not df_p.empty:
                st.dataframe(df_p, use_container_width=True, hide_index=True)
            else:
                st.write("Tidak ada data Preventive.")

            st.markdown("---")

            # Bagian Tabel CM
            st.subheader("🆘 KELOMPOK: CORRECTIVE MAINTENANCE")
            df_c = df_pivot[df_pivot['KATEGORI'] == 'CORRECTIVE'].drop(columns=['KATEGORI', 'KODE'])
            if not df_c.empty:
                st.dataframe(df_c, use_container_width=True, hide_index=True)
            else:
                st.write("Tidak ada data Corrective.")
        else:
            st.warning("Data tidak tersedia.")
