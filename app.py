import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from gspread_dataframe import get_as_dataframe
import requests
import io
import re

# ======================== PAGE CONFIG ========================
st.set_page_config(page_title="Dashboard PLTD Bach", page_icon="⚡", layout="wide")

# ======================== STYLING ========================
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    [data-testid="stSidebarNav"] span { color: #FFFFFF !important; }
    [data-testid="stSidebarNav"] a { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0A2540; }
    .stPlotlyChart { background: white; border-radius: 10px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    [data-testid="stDataFrame"] { background: white; border-radius: 10px; padding: 8px; }
    .stButton>button { background-color: #1F4E79; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #2A6DA1; color: white; }
</style>
""", unsafe_allow_html=True)

# ======================== DATA SOURCES ========================
PLTD_SHEETS = {
    'Pemaron': '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli': '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan': '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika': '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    'Bobong': '1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM',
    'Merawang': '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir': '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Lueng Bata': '1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g',
    'Ulee Kareng': '1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU',
    'Waena': '10NKbFUi0SVh1784OQnSU0ULhWzL6_AK7XLY-8EgKbG8',
    'Sambelia': '1-8uGvDwZnciEgAXBbogkYWdHQcEClcwuln-hbaR0UAc',
    'Timika 2': '17FR17wxkeVgd0_GElV59ugetL8nutqiYwQRyY6FqIVE',
    'Wamena': '14ieCIQwEXf4hZ-RsOeLIMyKi5qEJLtQBwTz35b9JXxs',
}
MASTER_PLTD_ID = '1FsaZyKs3DgJlyZkx5qqpBotNK8Z6C8GOrNeJv3I8AJA'
MASTER_CIKANDE_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'
DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"

# ======================== PREVENTIVE DETECTION ========================
# Data dari user: Nama Material, Kode Material
PREVENTIVE_TABLE = [
    ("Oil Filter", "LF3325"),
    ("Oil Filter By pass", "LF777"),
    ("Element Water Separator", "2020PM V30-C"),
    ("Fuel Filter", "FS1006"),
    ("Water Filter", "WF2076"),
    ("Cylinder head cover gasket", "3629140"),
    ("Air Filter Element", "AF872"),
    ("Air Filter Element", "AF25278"),
    ("Air Filter Element (Free)", "AF25278"),
    ("Air Filter Element (Aksa)", "AHO1135"),
    ("V-BELT Fan Radiator", "5413003"),
    ("V-BELT (Aksa)", "3015257"),
    ("V-BELT Alternator", "5412990"),
    ("V-BELT Alternator", "5PK889"),
    ("V-BELT Alternator", "21-3107"),
    ("V-BELT Alternator", "25471145"),
    ("V-BELT Fan Radiator", "23PK2032"),
    ("V-BELT Fan Radiator", "21-3110"),
    ("V-BELT Fan Radiator", "25477108"),
    ("Oli Shell (Drum)", "Rimula R4 X 15W-40"),
    ("Oli Shell (IBC)", "Rimula R4 X 15W-40"),
]

# Normalisasi: kumpulan keyword dari nama material preventive (lowercase)
PREVENTIVE_NAME_KEYWORDS = {
    "oil filter", "element water separator", "fuel filter", "water filter",
    "cylinder head cover gasket", "air filter element", "v-belt",
    "oli shell", "rimula", "v belt"
}

# Normalisasi: kode preventive (lowercase, tanpa spasi)
def _norm(s):
    return re.sub(r'\s+', '', str(s).lower())

PREVENTIVE_CODES_NORM = set()
for _, code in PREVENTIVE_TABLE:
    # Split multi-code
    for part in re.split(r'\s*/\s*', code):
        PREVENTIVE_CODES_NORM.add(_norm(part))

def is_preventive(kode_material, nama_material=""):
    """Deteksi apakah material termasuk Preventive."""
    if not kode_material and not nama_material:
        return False
    kode_norm = _norm(kode_material) if kode_material else ""
    nama_norm = _norm(nama_material) if nama_material else ""

    # 1) Cek kode: apakah ada bagian kode yang cocok dengan PREVENTIVE_CODES_NORM
    if kode_norm:
        # Split kode jika mengandung /
        for part in re.split(r'\s*/\s*', kode_norm):
            part = part.strip()
            if part in PREVENTIVE_CODES_NORM:
                return True
        # Cek substring (misal kode mengandung "LF3325" tapi ada tambahan)
        for pc in PREVENTIVE_CODES_NORM:
            if len(pc) >= 3 and pc in kode_norm:
                return True

    # 2) Cek nama material terhadap keyword preventive
    if nama_norm:
        for kw in PREVENTIVE_NAME_KEYWORDS:
            if kw in nama_norm:
                return True

    return False

# ======================== GSPREAD CLIENT ========================
@st.cache_resource
def get_gspread_client():
    creds = dict(st.secrets["gcp_service_account"])
    if creds.get('private_key'):
        creds['private_key'] = creds['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(creds)

# ======================== LOADERS ========================
@st.cache_data(ttl=600)
def load_stock_all():
    """Kolom: C = nama, D = kode, I = qty"""
    client = get_gspread_client()
    rows = []
    for pltd, sid in PLTD_SHEETS.items():
        try:
            sh = client.open_by_key(sid)
            data = sh.sheet1.get_all_values()
            if len(data) < 2:
                continue
            for r in data[1:]:
                if len(r) < 9:
                    continue
                nama = r[2].strip() if len(r) > 2 else ''
                kode = r[3].strip() if len(r) > 3 else ''
                qty_str = r[8].strip() if len(r) > 8 else '0'
                try:
                    qty = float(qty_str.replace(',', ''))
                except:
                    qty = 0.0
                if kode or nama:
                    rows.append((pltd, kode, nama, qty))
        except:
            pass
    df = pd.DataFrame(rows, columns=['PLTD', 'Kode Material', 'Nama Material', 'Qty'])
    if not df.empty:
        df['Jenis'] = df.apply(lambda r: 'Preventive' if is_preventive(r['Kode Material'], r['Nama Material']) else 'Corrective', axis=1)
        # Pastikan duplikat dibersihkan
        df = df.drop_duplicates(subset=['PLTD', 'Kode Material', 'Nama Material'], keep='last')
    return df

@st.cache_data(ttl=600)
def load_master_data():
    client = get_gspread_client()
    sh = client.open_by_key(MASTER_PLTD_ID)
    df1, df2 = None, None
    try:
        df1 = get_as_dataframe(sh.worksheet('Master data 1'), evaluate_formulas=True)
        df1.columns = df1.columns.str.strip()
        rename1 = {'Nama Material':'nama_material','Kode Material':'kode_material',
                   'Nama PLTD':'pltd','Harga D365':'harga',
                   'Kebutuhan Perbulan Sesuai CF PM':'keb_pm',
                   'Kebutuhan Perbulan Sesuai Aktual FC':'keb_aktual'}
        df1.rename(columns={k:v for k,v in rename1.items() if k in df1.columns}, inplace=True)
    except:
        pass
    try:
        df2 = get_as_dataframe(sh.worksheet('Master data 2'), evaluate_formulas=True)
        df2.columns = df2.columns.str.strip()
        rename2 = {'Nama PLTD':'pltd','Durasi Kirim Darat+Laut (Hari)':'durasi_kirim'}
        df2.rename(columns={k:v for k,v in rename2.items() if k in df2.columns}, inplace=True)
        if 'durasi_kirim' in df2.columns:
            df2['durasi_kirim'] = pd.to_numeric(df2['durasi_kirim'], errors='coerce').fillna(14)
    except:
        pass
    return df1, df2

@st.cache_data(ttl=600)
def load_stok_cikande():
    """Baca sheet 'Sheet1' dari master Cikande, ambil kolom U (index 20)"""
    client = get_gspread_client()
    try:
        sh = client.open_by_key(MASTER_CIKANDE_ID)
        ws = sh.worksheet('Sheet1')
        data = ws.get_all_values()
        if len(data) < 2:
            return pd.DataFrame()
        # Baris pertama header, kolom U = index 20
        rows = []
        for r in data[1:]:
            if len(r) > 20:
                # Coba baca beberapa kolom untuk identifikasi
                # Asumsikan: A=No, B=Kode, C=Nama, ... U=Qty Cikande
                kode = r[1].strip() if len(r) > 1 else ''
                nama = r[2].strip() if len(r) > 2 else ''
                qty_str = r[20].strip() if len(r) > 20 else '0'
                try:
                    qty = float(qty_str.replace(',', ''))
                except:
                    qty = 0.0
                if kode or nama:
                    rows.append({'Kode Material': kode, 'Nama Material': nama, 'Qty Cikande': qty})
        return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"Gagal membaca stok Cikande: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_delivery():
    try:
        resp = requests.get(DELIVERY_URL, headers={'User-Agent':'Mozilla/5.0'}, timeout=20)
        return pd.read_excel(io.BytesIO(resp.content))
    except:
        return pd.DataFrame()

# ======================== HALAMAN ========================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    df = load_stock_all()
    if df.empty:
        st.warning("Data belum tersedia.")
        return
    c1,c2,c3 = st.columns(3)
    c1.metric("PLTD", df['PLTD'].nunique())
    c2.metric("Total Stok", f"{df['Qty'].sum():,.0f}")
    prev_ct = (df['Jenis'] == 'Preventive').sum()
    corr_ct = (df['Jenis'] == 'Corrective').sum()
    c3.metric("Preventive / Corrective", f"{prev_ct} / {corr_ct}")

    st.markdown("---")
    st.info("Gunakan menu sidebar untuk navigasi. Pilih filter untuk melihat data.")
    pltd_coords = {
        'Pemaron':(-8.16,114.68),'Mangoli':(-1.88,125.37),'Tayan':(-0.03,110.10),
        'Timika':(-4.56,136.89),'Bobong':(-1.95,124.39),'Merawang':(-1.95,105.96),
        'Air Anyir':(-1.94,106.11),'Padang Manggar':(-2.14,106.14),'Krueng Raya':(5.60,95.53),
        'Lueng Bata':(5.55,95.33),'Ulee Kareng':(5.55,95.33),'Waena':(-2.61,140.56),
        'Sambelia':(-8.40,116.67),'Timika 2':(-4.56,136.89),'Wamena':(-4.09,138.94)
    }
    loc = df[['PLTD']].drop_duplicates()
    loc['lat'] = loc['PLTD'].map(lambda x: pltd_coords.get(x, (None, None))[0])
    loc['lon'] = loc['PLTD'].map(lambda x: pltd_coords.get(x, (None, None))[1])
    st.map(loc.dropna(subset=['lat']), latitude='lat', longitude='lon', zoom=4, height=350)

def page_stock():
    st.title("📦 Stok Material PLTD")
    df = load_stock_all()
    if df.empty:
        st.warning("Data belum tersedia.")
        return

    st.sidebar.header("Filter Stok")
    pltd_opts = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opts, default=[])
    jenis_opts = ['Preventive', 'Corrective']
    sel_jenis = st.sidebar.multiselect("Jenis Material", jenis_opts, default=[])

    filtered = df.copy()
    if sel_pltd:
        filtered = filtered[filtered['PLTD'].isin(sel_pltd)]
    if sel_jenis:
        filtered = filtered[filtered['Jenis'].isin(sel_jenis)]

    prev_df = filtered[filtered['Jenis'] == 'Preventive']
    corr_df = filtered[filtered['Jenis'] == 'Corrective']

    def tampil_pivot(data, judul, warna="blue"):
        if data.empty:
            st.info(f"Tidak ada data {judul} dengan filter tersebut.")
            return
        st.subheader(f"{'🔵' if warna=='blue' else '🟠'} Material {judul}")
        pivot = data.pivot_table(
            index=['Kode Material', 'Nama Material'],
            columns='PLTD', values='Qty', aggfunc='sum', fill_value=0
        )
        pivot['Total'] = pivot.sum(axis=1)
        pivot = pivot.reset_index()
        # Susun ulang kolom: Kode Material, Nama Material, ..., Total
        cols_order = ['Kode Material', 'Nama Material'] + [c for c in pivot.columns if c not in ('Kode Material', 'Nama Material')]
        pivot = pivot[cols_order]

        # column_config: pin 2 kolom pertama
        cfg = {
            'Kode Material': st.column_config.TextColumn(pinned=True),
            'Nama Material': st.column_config.TextColumn(pinned=True),
        }
        st.dataframe(pivot, column_config=cfg, use_container_width=True, hide_index=True)

    tampil_pivot(prev_df, "Preventive", "blue")
    tampil_pivot(corr_df, "Corrective", "orange")

    st.markdown("---")
    st.subheader("🚚 Status Pengiriman (Outstanding)")
    deliv = load_delivery()
    if not deliv.empty:
        # Hanya yang outstanding: belum delivered/cancel
        if 'STATUS' in deliv.columns:
            outstanding = deliv[~deliv['STATUS'].isin(['DELIVERED', 'CANCEL', 'COMPLETED'])]
            if not outstanding.empty:
                mapping = {'IN TRANSIT':'Proses Kirim','SHIPPED':'Proses Kirim',
                           'PO':'Proses Import/Pembelian','PROCUREMENT':'Proses Import/Pembelian'}
                outstanding['Kategori'] = outstanding['STATUS'].map(mapping).fillna('Lainnya')
                st.dataframe(outstanding, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Tidak ada pengiriman outstanding. Semua sudah delivered.")
        else:
            st.dataframe(deliv, use_container_width=True, hide_index=True)
    else:
        st.info("Data pengiriman belum tersedia.")

    st.markdown("---")
    st.subheader("🏢 Stok Gudang Cikande")
    df_cikande = load_stok_cikande()
    if not df_cikande.empty:
        st.dataframe(df_cikande, use_container_width=True, hide_index=True)
    else:
        st.info("Data gudang Cikande belum tersedia. Pastikan sheet 'Sheet1' sudah dibagikan ke service account.")

def page_analisis():
    st.title("📊 Analisis Kebutuhan & Lead Time")
    df = load_stock_all()
    if df.empty:
        st.warning("Data stok belum tersedia.")
        return
    master1, master2 = load_master_data()

    # Gabung dengan master1
    if master1 is not None and 'pltd' in master1.columns and 'kode_material' in master1.columns:
        df = df.merge(
            master1[['pltd', 'kode_material', 'harga', 'keb_pm', 'keb_aktual']],
            left_on=['PLTD', 'Kode Material'],
            right_on=['pltd', 'kode_material'],
            how='left',
            suffixes=('', '_m1')
        )
        # Buang kolom duplikat
        for c in ['pltd', 'kode_material']:
            if c in df.columns:
                df.drop(columns=[c], inplace=True)
    for col in ['harga', 'keb_pm', 'keb_aktual']:
        if col not in df.columns:
            df[col] = np.nan

    if master2 is not None and 'pltd' in master2.columns and 'durasi_kirim' in master2.columns:
        df = df.merge(master2[['pltd', 'durasi_kirim']], left_on='PLTD', right_on='pltd', how='left')
        if 'pltd' in df.columns:
            df.drop(columns=['pltd'], inplace=True, errors='ignore')
    else:
        df['durasi_kirim'] = 14

    df['durasi_kirim'] = df['durasi_kirim'].fillna(14)
    df['keb_efektif'] = df['keb_aktual'].fillna(df['keb_pm']).fillna(0)
    df['keb_harian'] = df['keb_efektif'] / 30.5
    df['sisa_hari'] = np.where(df['keb_harian'] > 0, df['Qty'] / df['keb_harian'], 9999)
    dur = df['durasi_kirim']
    df['Status'] = np.where(df['sisa_hari'] < dur, '🔴 Critical Reorder',
                    np.where(df['sisa_hari'] < 1.5 * dur, '🟡 Warning', '🟢 Aman'))
    df['Propose Kirim'] = np.ceil(np.maximum(0, (df['keb_harian'] * dur) - df['Qty']))

    st.sidebar.header("Filter Analisis")
    pltd_opts = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opts, default=[])
    sel_jenis = st.sidebar.multiselect("Jenis", ['Preventive', 'Corrective'], default=[])
    sel_status = st.sidebar.multiselect("Status", ['🔴 Critical Reorder', '🟡 Warning', '🟢 Aman'], default=[])

    if sel_pltd:
        df = df[df['PLTD'].isin(sel_pltd)]
    if sel_jenis:
        df = df[df['Jenis'].isin(sel_jenis)]
    if sel_status:
        df = df[df['Status'].isin(sel_status)]

    cols = ['PLTD', 'Kode Material', 'Nama Material', 'Jenis', 'Qty',
            'keb_pm', 'keb_aktual', 'sisa_hari', 'durasi_kirim', 'Status', 'Propose Kirim']
    if 'harga' in df.columns:
        cols.insert(-1, 'harga')
    st.subheader("📋 Tabel Kebutuhan")
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.subheader("⏳ Alert Status")
    if not df.empty:
        st.bar_chart(df['Status'].value_counts())

    pm = df[df['Jenis'] == 'Preventive']
    if not pm.empty:
        mat = st.selectbox("Timeline Material PM", pm['Nama Material'].unique())
        row = pm[pm['Nama Material'] == mat].iloc[0]
        st.metric("Sisa Hari Stok", f"{row['sisa_hari']:.0f}")
        st.progress(min(row['sisa_hari'] / row['durasi_kirim'], 1.0))

def page_pemakaian():
    st.title("🔥 Pemakaian Material")
    st.info("Segera hadir.")

def page_transaksi():
    st.title("📊 Transaksi Project")
    st.info("Segera hadir.")

# ======================== NAVIGASI ========================
home_pg = st.Page(home, title="Beranda", icon="🏠", default=True)
stock_pg = st.Page(page_stock, title="Stok PLTD", icon="📦")
analisis_pg = st.Page(page_analisis, title="Analisis Stok", icon="📊")
pakai_pg = st.Page(page_pemakaian, title="Pemakaian", icon="🔥")
trans_pg = st.Page(page_transaksi, title="Transaksi Project", icon="🚚")

pg = st.navigation([home_pg, stock_pg, analisis_pg, pakai_pg, trans_pg])
pg.run()
