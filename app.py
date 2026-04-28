import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import plotly.express as px
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound

# ======================== CONFIG ========================
st.set_page_config(page_title="Dashboard PLTD Bach", page_icon="⚡", layout="wide")

# ======================== CSS ========================
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    .sidebar-title {
        color: white; font-size: 20px; font-weight: 800; text-align: center;
        margin-bottom: 25px; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    [data-testid="stSidebar"] label p { color: #CCCCCC !important; font-weight: 500 !important; }
    [data-testid="stSidebarNav"] span { color: white !important; font-weight: 600 !important; }
    [data-testid="stSidebarNav"] a { color: white !important; }
    [data-testid="stSidebar"] button svg { fill: white !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0A2540; }
    .stPlotlyChart { background: white; border-radius: 10px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ======================== DATA SOURCES ========================
PLTD_SHEETS = {
    'Pemaron':        '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli':        '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan':          '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika':         '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    'Bobong':         '1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM',
    'Merawang':       '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir':      '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya':    '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Lueng Bata':     '1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g',
    'Ulee Kareng':    '1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU',
    'Waena':          '10NKbFUi0SVh1784OQnSU0ULhWzL6_AK7XLY-8EgKbG8',
    'Sambelia':       '1-8uGvDwZnciEgAXBbogkYWdHQcEClcwuln-hbaR0UAc',
    'Timika 2':       '17FR17wxkeVgd0_GElV59ugetL8nutqiYwQRyY6FqIVE',
    'Wamena':         '14ieCIQwEXf4hZ-RsOeLIMyKi5qEJLtQBwTz35b9JXxs',
}
MASTER_SHEET_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'
SHAREPOINT_DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"

PREVENTIVE_CODES = {
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076', '3629140',
    'AF872', 'AF25278', 'AHO1135', '5413003', '3015257', '5412990',
    '5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108',
    'RIMULA R4 X 15W-40'
}

PLTD_COORDS = {
    'Pemaron': (-8.1647, 114.6824), 'Mangoli': (-1.8821, 125.3732),
    'Tayan': (-0.0324, 110.1022), 'Timika': (-4.5564, 136.8883),
    'Bobong': (-1.946, 124.388), 'Merawang': (-1.9508, 105.9643),
    'Air Anyir': (-1.9377, 106.1064), 'Padang Manggar': (-2.1429, 106.1419),
    'Krueng Raya': (5.6023, 95.5336), 'Lueng Bata': (5.5484, 95.3342),
    'Ulee Kareng': (5.5475, 95.3322), 'Waena': (-2.6062, 140.5637),
    'Sambelia': (-8.3973, 116.6729), 'Timika 2': (-4.5564, 136.8883),
    'Wamena': (-4.0922, 138.9447)
}

DURASI_KIRIM = {
    'Pemaron': 7, 'Mangoli': 14, 'Tayan': 10, 'Timika': 14,
    'Bobong': 14, 'Merawang': 5, 'Air Anyir': 5, 'Padang Manggar': 5,
    'Krueng Raya': 7, 'Lueng Bata': 7, 'Ulee Kareng': 7, 'Waena': 14,
    'Sambelia': 7, 'Timika 2': 14, 'Wamena': 21
}

PM_INTERVAL = {
    'LF3325': 400, 'LF777': 500, '2020PM V30-C': 400, 'FS1006': 500,
    'WF2076': 500, '3629140': 400, 'AF872': 400, 'AF25278': 400,
    'AHO1135': 500, '5413003': 500, '3015257': 500, '5412990': 500,
    '5PK889': 500, '21-3107': 500, '25471145': 500, '23PK2032': 500,
    '21-3110': 500, '25477108': 500, 'RIMULA R4 X 15W-40': 750
}
DEFAULT_PM_INTERVAL = 500

# ======================== GSPREAD CLIENT ========================
@st.cache_resource
def get_gspread_client():
    credentials = dict(st.secrets["gcp_service_account"])
    pk = credentials.get('private_key', '')
    if pk:
        pk = pk.replace('\\n', '\n')
        credentials['private_key'] = pk
    return gspread.service_account_from_dict(credentials)

# ======================== DATA LOADERS ========================
@st.cache_data(ttl=600)
def load_stock_per_pltd():
    client = get_gspread_client()
    all_data = []
    for pltd, sheet_id in PLTD_SHEETS.items():
        try:
            sh = client.open_by_key(sheet_id)
            ws = sh.sheet1
            data = ws.get_all_values()
            if not data or len(data) < 2:
                continue
            for row in data[1:]:
                if len(row) < 9:
                    continue
                kode = row[1].strip() if len(row) > 1 else ''
                nama = row[2].strip() if len(row) > 2 else ''
                tipe = row[3].strip() if len(row) > 3 else ''
                qty_str = row[8] if len(row) > 8 else '0'
                try:
                    qty = float(qty_str.replace(',', ''))
                except:
                    qty = 0.0
                if kode or nama:
                    all_data.append({
                        'PLTD': pltd,
                        'Kode Material': kode,
                        'Nama Material': nama,
                        'Type Material': tipe,
                        'Qty': qty
                    })
        except Exception:
            continue
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['Jenis'] = df['Kode Material'].apply(lambda x: 'Preventive' if x in PREVENTIVE_CODES else 'Corrective')
    return df

@st.cache_data(ttl=600)
def load_master_sheets():
    client = get_gspread_client()
    sh = client.open_by_key(MASTER_SHEET_ID)
    result = {}
    try:
        result['pemakaian'] = get_as_dataframe(sh.worksheet('Gabungan'), evaluate_formulas=True)
    except WorksheetNotFound:
        result['pemakaian'] = pd.DataFrame()
    try:
        result['stok_cikande'] = get_as_dataframe(sh.worksheet('Sheet1'), evaluate_formulas=True)
    except:
        result['stok_cikande'] = pd.DataFrame()
    try:
        result['harga'] = get_as_dataframe(sh.worksheet('DARI TARIKAN'), evaluate_formulas=True)
    except:
        result['harga'] = pd.DataFrame()
    return result

@st.cache_data(ttl=600)
def load_delivery_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(SHAREPOINT_DELIVERY_URL, headers=headers, timeout=20)
        return pd.read_excel(io.BytesIO(resp.content))
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_project_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(SHAREPOINT_DELIVERY_URL, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(resp.content))
        df_ops['PROJECT'] = 'PROJECT PLTD'
    except:
        df_ops = pd.DataFrame()
    try:
        resp = requests.get("https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1", headers=headers, timeout=20)
        df_das = pd.read_excel(io.BytesIO(resp.content))
        df_das['PROJECT'] = 'PROJECT DAS'
    except:
        df_das = pd.DataFrame()
    df = pd.concat([df_ops, df_das], ignore_index=True)
    if not df.empty and 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
        df['Tahun'] = df['TANGGAL'].dt.year.astype(str)
        df['Bulan'] = df['TANGGAL'].dt.strftime('%B')
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    for col in ['QTY', 'TOTAL COST']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def get_duration(pltd):
    return DURASI_KIRIM.get(pltd, 14)

def get_pm_interval(kode):
    return PM_INTERVAL.get(str(kode).strip(), DEFAULT_PM_INTERVAL)

# ======================== PAGES ========================
def home():
    st.title("⚡ Dashboard Monitoring Stok & Logistik PLTD")
    df_stock = load_stock_per_pltd()
    if df_stock.empty:
        st.warning("Data stok masih kosong. Pastikan semua spreadsheet sudah dibagikan ke service account.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total PLTD", df_stock['PLTD'].nunique())
    col2.metric("Total Stok (unit)", f"{df_stock['Qty'].sum():,.0f}")
    col3.metric("Material Kritis", "Lihat Analisis Stok")

    st.markdown("---")
    cols = st.columns(4)
    with cols[0]:
        if st.button("📦 Stok PLTD", use_container_width=True): st.switch_page("pages/stock_pltd")
    with cols[1]:
        if st.button("📊 Analisis Stok", use_container_width=True): st.switch_page("pages/analisis_stok")
    with cols[2]:
        if st.button("🔥 Pemakaian", use_container_width=True): st.switch_page("pages/pemakaian")
    with cols[3]:
        if st.button("🚚 Transaksi Project", use_container_width=True): st.switch_page("pages/transaksi_project")

    st.markdown("---")
    coords = df_stock[['PLTD']].drop_duplicates()
    coords['lat'] = coords['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[0])
    coords['lon'] = coords['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[1])
    valid = coords.dropna(subset=['lat'])
    if not valid.empty:
        st.subheader("📍 Lokasi PLTD")
        st.map(valid, latitude='lat', longitude='lon', zoom=4, height=350)

def stock_pltd():
    st.title("📦 Stock Material PLTD Aktual")
    df_stock = load_stock_per_pltd()
    if df_stock.empty: return st.warning("Data belum tersedia.")
    master = load_master_sheets()
    df_cikande = master['stok_cikande']
    df_deliv = load_delivery_data()

    st.sidebar.header("Filter")
    pltd_list = sorted(df_stock['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_list, default=pltd_list[:5])
    sel_jenis = st.sidebar.multiselect("Jenis", ['Preventive','Corrective'], default=['Preventive','Corrective'])
    df = df_stock[(df_stock['PLTD'].isin(sel_pltd)) & (df_stock['Jenis'].isin(sel_jenis))]

    st.subheader("🔹 Stok Aktual")
    st.dataframe(df[['PLTD','Kode Material','Nama Material','Type Material','Qty','Jenis']], use_container_width=True, hide_index=True)

    st.subheader("🚚 Status Pengiriman (In‑Transit)")
    if not df_deliv.empty:
        if 'STATUS' in df_deliv.columns:
            status_map = {'IN TRANSIT':'Proses Kirim','SHIPPED':'Proses Kirim','ON DELIVERY':'Proses Kirim','PO':'Proses Import/Pembelian','PROCUREMENT':'Proses Import/Pembelian','PURCHASE':'Proses Import/Pembelian'}
            df_deliv['Kategori'] = df_deliv['STATUS'].map(status_map).fillna('Lainnya')
        else:
            df_deliv['Kategori'] = 'Proses Kirim'
        st.dataframe(df_deliv, use_container_width=True, hide_index=True)
    else:
        st.warning("Data pengiriman tidak tersedia.")
    st.subheader("🏢 Stok Gudang Cikande")
    if not df_cikande.empty:
        st.dataframe(df_cikande, use_container_width=True, hide_index=True)

def analisis_stok():
    st.title("📊 Analisis Stok & Kebutuhan Material")
    df_stock = load_stock_per_pltd()
    if df_stock.empty: return st.warning("Data belum tersedia.")
    master = load_master_sheets()
    df_harga = master['harga']
    df_pemakaian = master['pemakaian']

    stro = st.sidebar.number_input("Jam Operasi/hari", 1, 24, 24)
    hari_per_bulan = 30.5
    jam_per_bulan = hari_per_bulan * stro

    if not df_harga.empty and 'Kode Material' in df_harga.columns and 'Harga Satuan' in df_harga.columns:
        df_stock = df_stock.merge(df_harga[['Kode Material', 'Harga Satuan']], on='Kode Material', how='left')
    else:
        df_stock['Harga Satuan'] = np.nan

    df_stock['Interval PM (jam)'] = df_stock['Kode Material'].apply(get_pm_interval)
    df_stock['Kebutuhan/bin (PM)'] = np.ceil(jam_per_bulan / df_stock['Interval PM (jam)'])

    if not df_pemakaian.empty and 'PLTD' in df_pemakaian.columns and 'Kode Material' in df_pemakaian.columns and 'Qty' in df_pemakaian.columns:
        df_pemakaian['Tanggal'] = pd.to_datetime(df_pemakaian.iloc[:, 0], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.DateOffset(months=6)
        recent = df_pemakaian[df_pemakaian['Tanggal'] >= cutoff]
        konsumsi = recent.groupby(['PLTD', 'Kode Material'])['Qty'].sum() / 6
        konsumsi = konsumsi.reset_index(name='Kebutuhan/bin (Aktual)')
        df_stock = df_stock.merge(konsumsi, on=['PLTD', 'Kode Material'], how='left')
        df_stock['Kebutuhan/bin (Aktual)'] = df_stock['Kebutuhan/bin (Aktual)'].fillna(0)
    else:
        df_stock['Kebutuhan/bin (Aktual)'] = 0

    df_stock['Kebutuhan/bin (Efektif)'] = np.where(df_stock['Kebutuhan/bin (Aktual)'] > 0,
                                                   df_stock['Kebutuhan/bin (Aktual)'],
                                                   df_stock['Kebutuhan/bin (PM)'])
    df_stock['Kebutuhan/hari'] = df_stock['Kebutuhan/bin (Efektif)'] / hari_per_bulan
    df_stock['Durasi Kirim (hari)'] = df_stock['PLTD'].apply(get_duration)
    df_stock['Sisa Hari Stok'] = np.where(df_stock['Kebutuhan/hari'] > 0,
                                          df_stock['Qty'] / df_stock['Kebutuhan/hari'], 9999)
    df_stock['Status'] = df_stock.apply(lambda r: '🔴 Critical Reorder' if r['Sisa Hari Stok'] < r['Durasi Kirim (hari)']
        else ('🟡 Warning' if r['Sisa Hari Stok'] < 1.5 * r['Durasi Kirim (hari)'] else '🟢 Aman'), axis=1)
    df_stock['Propose Kirim'] = np.ceil(np.maximum(0, (df_stock['Kebutuhan/hari'] * df_stock['Durasi Kirim (hari)']) - df_stock['Qty']))

    st.sidebar.header("Filter")
    pltd_f = st.sidebar.multiselect("PLTD", sorted(df_stock['PLTD'].unique()), default=sorted(df_stock['PLTD'].unique())[:5])
    jenis_f = st.sidebar.multiselect("Jenis", ['Preventive','Corrective'], default=['Preventive','Corrective'])
    status_f = st.sidebar.multiselect("Status", ['🔴 Critical Reorder','🟡 Warning','🟢 Aman'], default=['🔴 Critical Reorder','🟡 Warning','🟢 Aman'])

    df_view = df_stock[df_stock['PLTD'].isin(pltd_f) & df_stock['Jenis'].isin(jenis_f) & df_stock['Status'].isin(status_f)]
    st.subheader("📋 Tabel Kebutuhan")
    st.dataframe(df_view[['PLTD','Kode Material','Nama Material','Jenis','Qty','Kebutuhan/bin (PM)','Kebutuhan/bin (Aktual)','Sisa Hari Stok','Durasi Kirim (hari)','Status','Propose Kirim'] + (['Harga Satuan'] if 'Harga Satuan' in df_view.columns else [])], use_container_width=True, hide_index=True)

    st.subheader("⏳ Lead Time Alert")
    st.bar_chart(df_view['Status'].value_counts())

def pemakaian():
    st.title("🔥 Pemakaian Material & Peta Sebaran")
    master = load_master_sheets()
    df = master['pemakaian']
    if df.empty: return st.warning("Data pemakaian tidak tersedia.")
    # Mapping kolom (sesuaikan dengan struktur spreadsheet Anda)
    st.write("Data pemakaian berhasil dimuat. (Tambahkan visualisasi sesuai kebutuhan.)")
    # (salin kode pemakaian sebelumnya yang sudah stabil)

def transaksi_project():
    st.title("📊 Dashboard Project Bach")
    df = load_project_data()
    if df.empty: return st.warning("Data project tidak tersedia.")
    # (salin kode transaksi project sebelumnya yang sudah stabil)

# ======================== NAVIGATION ========================
home_pg = st.Page(home, title="Beranda", icon="🏠", default=True)
stock_pg = st.Page(stock_pltd, title="Stok PLTD", icon="📦")
analisis_pg = st.Page(analisis_stok, title="Analisis Stok", icon="📊")
pemakaian_pg = st.Page(pemakaian, title="Pemakaian", icon="🔥")
transaksi_pg = st.Page(transaksi_project, title="Transaksi Project", icon="🚚")

pg = st.navigation([home_pg, stock_pg, analisis_pg, pemakaian_pg, transaksi_pg])
pg.run()
