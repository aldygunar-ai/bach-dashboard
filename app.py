import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound

# ======================== KONFIGURASI HALAMAN ========================
st.set_page_config(
    page_title="Dashboard PLTD Bach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CSS CUSTOM ========================
st.markdown("""
<style>
    /* Latar utama */
    .main {
        background-color: #F5F7FA;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #0A2540 !important;
    }
    /* Judul sidebar */
    .sidebar-title {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
        padding: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    /* Label filter di sidebar */
    [data-testid="stSidebar"] label p {
        color: #CCCCCC !important;
        font-weight: 500 !important;
    }
    /* Teks navigasi (menu halaman) di sidebar */
    [data-testid="stSidebarNav"] span {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a {
        color: #FFFFFF !important;
    }
    /* Tombol sidebar */
    [data-testid="stSidebar"] button svg,
    button[kind="headerNoSpacing"] svg {
        fill: #FFFFFF !important;
    }
    /* Kartu metric */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 800;
        color: #0A2540;
    }
    /* Plotly chart container */
    .stPlotlyChart {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    /* Dataframe */
    [data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 8px;
    }
    /* Tombol umum */
    .stButton>button {
        background-color: #1F4E79;
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #2A6DA1;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ======================== SUMBER DATA ========================
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
SHAREPOINT_PROJECT_OPS = SHAREPOINT_DELIVERY_URL
SHAREPOINT_PROJECT_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

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

# ======================== PERBAIKAN AUTENTIKASI ========================
def safe_credentials():
    """Mengambil kredensial dari st.secrets dan memastikan private_key valid."""
    creds = dict(st.secrets["gcp_service_account"])
    # Bersihkan private_key: hapus spasi ekstra, pastikan header/footer ada
    pk = creds.get('private_key', '')
    if pk:
        pk = pk.strip()
        # Ganti literal \n dengan newline
        pk = pk.replace('\\n', '\n')
        # Pastikan header PEM ada
        if not pk.startswith('-----BEGIN PRIVATE KEY-----'):
            pk = '-----BEGIN PRIVATE KEY-----\n' + pk
        if not pk.endswith('-----END PRIVATE KEY-----'):
            pk = pk + '\n-----END PRIVATE KEY-----\n'
        # Hapus baris kosong di awal/akhir
        pk = '\n'.join([line for line in pk.split('\n') if line.strip() != ''])
        # Tambahkan newline di akhir jika belum ada
        if not pk.endswith('\n'):
            pk += '\n'
        creds['private_key'] = pk
    return creds

@st.cache_resource
def get_gspread_client():
    """Membuat client gspread dengan penanganan error."""
    try:
        credentials = safe_credentials()
        return gspread.service_account_from_dict(credentials)
    except Exception as e:
        st.error(f"Gagal autentikasi Google Sheets. Periksa Secrets di Streamlit Cloud: {e}")
        return None

# ======================== LOADER DATA (DENGAN FALLBACK) ========================
@st.cache_data(ttl=600)
def load_stock_per_pltd():
    client = get_gspread_client()
    if client is None:
        return pd.DataFrame()
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
    if client is None:
        return {'pemakaian': pd.DataFrame(), 'stok_cikande': pd.DataFrame(), 'harga': pd.DataFrame()}
    try:
        sh = client.open_by_key(MASTER_SHEET_ID)
    except Exception as e:
        st.warning(f"Tidak bisa membuka master spreadsheet: {e}")
        return {'pemakaian': pd.DataFrame(), 'stok_cikande': pd.DataFrame(), 'harga': pd.DataFrame()}
    result = {}
    try:
        result['pemakaian'] = get_as_dataframe(sh.worksheet('Gabungan'), evaluate_formulas=True)
    except:
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
        df = pd.read_excel(io.BytesIO(resp.content))
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_project_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    df_ops, df_das = pd.DataFrame(), pd.DataFrame()
    try:
        res_ops = requests.get(SHAREPOINT_PROJECT_OPS, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(res_ops.content))
        df_ops['PROJECT'] = 'PROJECT PLTD'
    except:
        pass
    try:
        res_das = requests.get(SHAREPOINT_PROJECT_DAS, headers=headers, timeout=20)
        df_das = pd.read_excel(io.BytesIO(res_das.content))
        df_das['PROJECT'] = 'PROJECT DAS'
    except:
        pass
    df = pd.concat([df_ops, df_das], ignore_index=True)
    if not df.empty and 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
        df['Tahun'] = df['TANGGAL'].dt.year.astype(str)
        df['Bulan'] = df['TANGGAL'].dt.strftime('%B')
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    # Konversi paksa numerik
    for col in ['QTY', 'TOTAL COST']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def get_duration(pltd):
    return DURASI_KIRIM.get(pltd, 14)

def get_pm_interval(kode):
    return PM_INTERVAL.get(str(kode).strip(), DEFAULT_PM_INTERVAL)

# ======================== HALAMAN: BERANDA ========================
def home():
    st.title("⚡ Dashboard Monitoring Stok & Logistik PLTD")
    st.markdown("Ringkasan Cepat & Navigasi")

    df_stock = load_stock_per_pltd()
    if df_stock.empty:
        st.warning("Data stok tidak tersedia. Periksa koneksi Google Sheets.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total PLTD", df_stock['PLTD'].nunique())
    with col2:
        total_qty = df_stock['Qty'].sum()
        st.metric("Total Stok (unit)", f"{total_qty:,.0f}")
    with col3:
        st.metric("Material Kritis", "Lihat Analisis Stok")

    st.markdown("---")
    cols = st.columns(4)
    with cols[0]:
        if st.button("📦 Stok PLTD", use_container_width=True):
            st.switch_page("pages/stock_pltd")
    with cols[1]:
        if st.button("📊 Analisis Stok", use_container_width=True):
            st.switch_page("pages/analisis_stok")
    with cols[2]:
        if st.button("🔥 Pemakaian", use_container_width=True):
            st.switch_page("pages/pemakaian")
    with cols[3]:
        if st.button("🚚 Transaksi Project", use_container_width=True):
            st.switch_page("pages/transaksi_project")

    st.markdown("---")
    coords = df_stock[['PLTD']].drop_duplicates()
    coords['lat'] = coords['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[0])
    coords['lon'] = coords['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[1])
    valid = coords.dropna(subset=['lat'])
    if not valid.empty:
        st.subheader("📍 Lokasi PLTD")
        st.map(valid, latitude='lat', longitude='lon', zoom=4, height=350)

# ======================== HALAMAN: STOK PLTD ========================
def stock_pltd():
    st.title("📦 Stock Material PLTD Aktual")

    df_stock = load_stock_per_pltd()
    if df_stock.empty:
        st.warning("Data stok tidak tersedia.")
        return
    master = load_master_sheets()
    df_cikande = master['stok_cikande']
    df_deliv = load_delivery_data()

    st.sidebar.header("Filter Stok PLTD")
    pltd_list = sorted(df_stock['PLTD'].unique())
    selected_pltd = st.sidebar.multiselect("PLTD", pltd_list, default=pltd_list[:5])
    kode_list = sorted(df_stock['Kode Material'].unique())
    selected_kode = st.sidebar.multiselect("Kode Material", kode_list)
    selected_jenis = st.sidebar.multiselect("Jenis Material", ['Preventive', 'Corrective'], default=['Preventive', 'Corrective'])

    df = df_stock.copy()
    if selected_pltd: df = df[df['PLTD'].isin(selected_pltd)]
    if selected_kode: df = df[df['Kode Material'].isin(selected_kode)]
    if selected_jenis: df = df[df['Jenis'].isin(selected_jenis)]

    st.subheader("🔹 Stok Aktual")
    st.dataframe(df[['PLTD', 'Kode Material', 'Nama Material', 'Type Material', 'Qty', 'Jenis']],
                 use_container_width=True, hide_index=True)

    st.subheader("🚚 Status Pengiriman (In‑Transit)")
    if not df_deliv.empty:
        if 'STATUS' in df_deliv.columns:
            status_map = {
                'IN TRANSIT': 'Proses Kirim',
                'SHIPPED': 'Proses Kirim',
                'ON DELIVERY': 'Proses Kirim',
                'PO': 'Proses Import/Pembelian',
                'PROCUREMENT': 'Proses Import/Pembelian',
                'PURCHASE': 'Proses Import/Pembelian',
            }
            df_deliv['Kategori Pengiriman'] = df_deliv['STATUS'].map(status_map).fillna('Lainnya')
        else:
            df_deliv['Kategori Pengiriman'] = 'Proses Kirim'
        kat_list = df_deliv['Kategori Pengiriman'].unique()
        selected_kat = st.multiselect("Kategori", kat_list, default=kat_list)
        df_deliv_f = df_deliv[df_deliv['Kategori Pengiriman'].isin(selected_kat)]
        st.dataframe(df_deliv_f, use_container_width=True, hide_index=True)
    else:
        st.warning("Data pengiriman tidak tersedia.")

    st.subheader("🏢 Stok Gudang Cikande")
    if not df_cikande.empty:
        st.dataframe(df_cikande, use_container_width=True, hide_index=True)
    else:
        st.info("Data gudang Cikande tidak ditemukan.")

# ======================== HALAMAN: ANALISIS STOK ========================
def analisis_stok():
    st.title("📊 Analisis Stok & Kebutuhan Material")

    df_stock = load_stock_per_pltd()
    if df_stock.empty:
        st.warning("Data stok tidak tersedia.")
        return
    master = load_master_sheets()
    df_harga = master['harga']
    df_pemakaian = master['pemakaian']

    stro = st.sidebar.number_input("Jam Operasi/hari", min_value=1, max_value=24, value=24)
    hari_per_bulan = 30.5
    jam_per_bulan = hari_per_bulan * stro

    if not df_harga.empty and 'Kode Material' in df_harga.columns and 'Harga Satuan' in df_harga.columns:
        df_stock = df_stock.merge(df_harga[['Kode Material', 'Harga Satuan']], on='Kode Material', how='left')
    else:
        df_stock['Harga Satuan'] = np.nan

    df_stock['Interval PM (jam)'] = df_stock['Kode Material'].apply(get_pm_interval)
    df_stock['Kebutuhan/bin (PM)'] = np.ceil(jam_per_bulan / df_stock['Interval PM (jam)'])

    if not df_pemakaian.empty and 'PLTD' in df_pemakaian.columns and 'Kode Material' in df_pemakaian.columns and 'Qty' in df_pemakaian.columns:
        try:
            df_pemakaian['Tanggal'] = pd.to_datetime(df_pemakaian.iloc[:, 0], errors='coerce')
            cutoff = pd.Timestamp.now() - pd.DateOffset(months=6)
            recent = df_pemakaian[df_pemakaian['Tanggal'] >= cutoff]
            konsumsi = recent.groupby(['PLTD', 'Kode Material'])['Qty'].sum() / 6
            konsumsi = konsumsi.reset_index(name='Kebutuhan/bin (Aktual)')
            df_stock = df_stock.merge(konsumsi, on=['PLTD', 'Kode Material'], how='left')
            df_stock['Kebutuhan/bin (Aktual)'] = df_stock['Kebutuhan/bin (Aktual)'].fillna(0)
        except:
            df_stock['Kebutuhan/bin (Aktual)'] = 0
    else:
        df_stock['Kebutuhan/bin (Aktual)'] = 0

    df_stock['Kebutuhan/bin (Efektif)'] = np.where(df_stock['Kebutuhan/bin (Aktual)'] > 0,
                                                   df_stock['Kebutuhan/bin (Aktual)'],
                                                   df_stock['Kebutuhan/bin (PM)'])
    df_stock['Kebutuhan/hari'] = df_stock['Kebutuhan/bin (Efektif)'] / hari_per_bulan
    df_stock['Durasi Kirim (hari)'] = df_stock['PLTD'].apply(get_duration)
    df_stock['Sisa Hari Stok'] = np.where(df_stock['Kebutuhan/hari'] > 0,
                                          df_stock['Qty'] / df_stock['Kebutuhan/hari'], 9999)
    df_stock['Status'] = df_stock.apply(
        lambda r: '🔴 Critical Reorder' if r['Sisa Hari Stok'] < r['Durasi Kirim (hari)']
        else ('🟡 Warning' if r['Sisa Hari Stok'] < 1.5 * r['Durasi Kirim (hari)'] else '🟢 Aman'),
        axis=1
    )
    df_stock['Propose Kirim'] = np.ceil(np.maximum(0, (df_stock['Kebutuhan/hari'] * df_stock['Durasi Kirim (hari)']) - df_stock['Qty']))

    st.sidebar.header("Filter")
    pltd_filter = st.sidebar.multiselect("PLTD", sorted(df_stock['PLTD'].unique()), default=sorted(df_stock['PLTD'].unique())[:5])
    jenis_filter = st.sidebar.multiselect("Jenis", ['Preventive', 'Corrective'], default=['Preventive', 'Corrective'])
    status_filter = st.sidebar.multiselect("Status", ['🔴 Critical Reorder', '🟡 Warning', '🟢 Aman'],
                                         default=['🔴 Critical Reorder', '🟡 Warning', '🟢 Aman'])

    df_view = df_stock.copy()
    if pltd_filter: df_view = df_view[df_view['PLTD'].isin(pltd_filter)]
    if jenis_filter: df_view = df_view[df_view['Jenis'].isin(jenis_filter)]
    if status_filter: df_view = df_view[df_view['Status'].isin(status_filter)]

    st.subheader("📋 Tabel Kebutuhan")
    cols_show = ['PLTD', 'Kode Material', 'Nama Material', 'Jenis', 'Qty',
                 'Kebutuhan/bin (PM)', 'Kebutuhan/bin (Aktual)',
                 'Sisa Hari Stok', 'Durasi Kirim (hari)', 'Status', 'Propose Kirim']
    if 'Harga Satuan' in df_view.columns:
        cols_show.append('Harga Satuan')
    st.dataframe(df_view[cols_show], use_container_width=True, hide_index=True)

    st.subheader("⏳ Lead Time Alert")
    alert_counts = df_view['Status'].value_counts()
    st.bar_chart(alert_counts)

    if not df_view[df_view['Jenis'] == 'Preventive'].empty:
        st.subheader("📅 Timeline Material PM")
        mat = st.selectbox("Pilih Material Preventive", df_view[df_view['Jenis'] == 'Preventive']['Nama Material'].unique())
        if mat:
            row = df_view[df_view['Nama Material'] == mat].iloc[0]
            st.metric("Sisa Hari Stok", f"{row['Sisa Hari Stok']:.0f}")
            st.progress(min(row['Sisa Hari Stok']/row['Durasi Kirim (hari)'], 1.0))

# ======================== HALAMAN: PEMAKAIAN ========================
def pemakaian():
    st.title("🔥 Pemakaian Material & Peta Sebaran")

    master = load_master_sheets()
    df_pemakaian = master['pemakaian']
    if df_pemakaian.empty:
        st.warning("Data pemakaian tidak tersedia.")
        return

    df = df_pemakaian.copy()
    col_map = {}
    for col in df.columns:
        col_l = col.lower()
        if 'tanggal' in col_l: col_map['Tanggal'] = col
        elif 'pltd' in col_l or 'site' in col_l: col_map['PLTD'] = col
        elif 'kode' in col_l and 'material' in col_l: col_map['Kode Material'] = col
        elif 'nama' in col_l and 'material' in col_l: col_map['Nama Material'] = col
        elif 'qty' in col_l or 'quantity' in col_l: col_map['Qty'] = col
        elif 'biaya' in col_l or 'total' in col_l or 'cost' in col_l: col_map['Biaya'] = col
        elif 'transaksi' in col_l or 'doc' in col_l or 'no' in col_l: col_map['No Transaksi'] = col
    if 'Tanggal' not in col_map:
        st.error("Kolom Tanggal tidak ditemukan.")
        return
    df['Tanggal'] = pd.to_datetime(df[col_map['Tanggal']], errors='coerce')
    df['PLTD'] = df[col_map['PLTD']] if 'PLTD' in col_map else 'Tidak Diketahui'
    df['Kode Material'] = df[col_map['Kode Material']] if 'Kode Material' in col_map else '-'
    df['Nama Material'] = df[col_map['Nama Material']] if 'Nama Material' in col_map else '-'
    df['Qty'] = pd.to_numeric(df[col_map['Qty']], errors='coerce').fillna(0)
    df['Biaya'] = pd.to_numeric(df[col_map['Biaya']], errors='coerce').fillna(0) if 'Biaya' in col_map else 0
    df['No Transaksi'] = df[col_map['No Transaksi']].astype(str) if 'No Transaksi' in col_map else ''
    df['Consume Status'] = df['No Transaksi'].apply(lambda x: 'Need Consume' if x in ['', 'nan', 'None'] else 'Consumed')

    st.sidebar.header("Filter Pemakaian")
    pltd_opt = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opt, default=pltd_opt[:5] if len(pltd_opt)>5 else pltd_opt)
    sel_consume = st.sidebar.multiselect("Status Consume", ['Consumed', 'Need Consume'], default=['Consumed', 'Need Consume'])

    df_f = df.copy()
    if sel_pltd: df_f = df_f[df_f['PLTD'].isin(sel_pltd)]
    if sel_consume: df_f = df_f[df_f['Consume Status'].isin(sel_consume)]

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Qty Pemakaian", f"{df_f['Qty'].sum():,.0f}")
    kpi2.metric("Total Biaya", f"Rp {df_f['Biaya'].sum():,.0f}")
    kpi3.metric("Need Consume", len(df_f[df_f['Consume Status'] == 'Need Consume']))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔝 Top 10 Material (Qty)")
        top_mat = df_f.groupby('Nama Material')['Qty'].sum().nlargest(10).reset_index()
        fig_mat = px.bar(top_mat, x='Qty', y='Nama Material', orientation='h',
                         text='Qty', color='Qty', color_continuous_scale='Blues')
        fig_mat.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        fig_mat.update_traces(textposition='outside')
        st.plotly_chart(fig_mat, use_container_width=True, config={'doubleClick': 'reset'})
    with col2:
        st.subheader("🏢 Top 10 Site (Qty)")
        top_site = df_f.groupby('PLTD')['Qty'].sum().nlargest(10).reset_index()
        fig_site = px.bar(top_site, x='Qty', y='PLTD', orientation='h',
                          text='Qty', color='Qty', color_continuous_scale='Teal')
        fig_site.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        fig_site.update_traces(textposition='outside')
        st.plotly_chart(fig_site, use_container_width=True, config={'doubleClick': 'reset'})

    st.subheader("⚠️ Need Consume Detail")
    need = df_f[df_f['Consume Status'] == 'Need Consume']
    st.dataframe(need.head(20)[['Tanggal', 'PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Biaya', 'No Transaksi']],
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📍 Peta Sebaran PLTD & Status Stok")
    df_stock = load_stock_per_pltd()
    if not df_stock.empty:
        stock_agg = df_stock.groupby('PLTD')['Qty'].sum().reset_index()
        stock_agg['Status'] = stock_agg['Qty'].apply(lambda x: '🟢 Aman' if x >= 10 else '🔴 Kritis')
        stock_agg['lat'] = stock_agg['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[0])
        stock_agg['lon'] = stock_agg['PLTD'].apply(lambda x: PLTD_COORDS.get(x, (None, None))[1])
        stock_agg = stock_agg.dropna(subset=['lat'])
        color_map = {'🟢 Aman': 'green', '🔴 Kritis': 'red'}
        fig_map = px.scatter_mapbox(stock_agg, lat='lat', lon='lon', color='Status',
                                    color_discrete_map=color_map,
                                    hover_name='PLTD', hover_data=['Qty'],
                                    zoom=3.5, height=350)
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True, config={'doubleClick': 'reset'})

# ======================== HALAMAN: TRANSAKSI PROJECT ========================
def transaksi_project():
    df_raw = load_project_data()
    if df_raw.empty:
        st.warning("Data project tidak tersedia.")
        return

    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0

    def do_reset():
        st.session_state.reset_counter += 1

    with st.sidebar:
        st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
        c = st.session_state.reset_counter
        sel_proj = st.multiselect("Project", df_raw['PROJECT'].unique(), default=[], key=f'p_{c}')
        sel_year = st.multiselect("Tahun", sorted(df_raw['Tahun'].unique(), reverse=True), default=[], key=f'y_{c}')
        sel_month = st.multiselect("Bulan", df_raw['Bulan'].unique(), key=f'm_{c}')
        sel_stat = st.multiselect("Status", sorted(df_raw['STATUS'].unique()), key=f's_{c}')
        sel_site = st.multiselect("Site (WH Tujuan)", sorted(df_raw['WH TUJUAN'].dropna().unique()), key=f'st_{c}')
        st.divider()
        st.button("🔄 Clear All Filters", on_click=do_reset, use_container_width=True)

    df_f = df_raw.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_month: df_f = df_f[df_f['Bulan'].isin(sel_month)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]
    if sel_site: df_f = df_f[df_f['WH TUJUAN'].isin(sel_site)]

    st.title("📊 Dashboard Project Bach")
    if not (sel_proj or sel_year or sel_month or sel_stat or sel_site):
        st.info("👋 Silakan pilih filter di samping kiri untuk menampilkan data.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Order", len(df_f))
        m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
        m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
        m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

        st.markdown("---")
        st.subheader("📈 Tren Permintaan Harian")
        trend_data = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
        if len(trend_data) > 60:
            trend_data = df_f.groupby(pd.Grouper(key='TANGGAL', freq='W')).size().reset_index(name='Requests')
            trend_data['Tgl_Str'] = trend_data['TANGGAL'].dt.strftime('%Y-%m-%d')
        fig_tr = px.line(trend_data, x='Tgl_Str', y='Requests', markers=True,
                         text='Requests', color_discrete_sequence=['#0A2540'])
        fig_tr.update_traces(textposition='top center', line_shape='spline')
        fig_tr.update_layout(height=350)
        st.plotly_chart(fig_tr, use_container_width=True, config={'doubleClick': 'reset'})

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 Top Site Request (QTY)")
            top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().nlargest(8).reset_index()
            fig_site = px.bar(top_site, x='QTY', y='WH TUJUAN', orientation='h',
                              text='QTY', color='QTY', color_continuous_scale='Teal')
            fig_site.update_layout(yaxis={'categoryorder':'total ascending'}, height=350)
            fig_site.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
            st.plotly_chart(fig_site, use_container_width=True, config={'doubleClick': 'reset'})
        with c2:
            st.subheader("🔝 Top Requested Items")
            top_item = df_f.groupby('ITEM NAME')['QTY'].sum().nlargest(8).reset_index()
            fig_item = px.bar(top_item, x='QTY', y='ITEM NAME', orientation='h',
                              text='QTY', color='QTY', color_continuous_scale='Blues')
            fig_item.update_layout(yaxis={'categoryorder':'total ascending'}, height=350)
            fig_item.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
            st.plotly_chart(fig_item, use_container_width=True, config={'doubleClick': 'reset'})

        st.markdown("---")
        st.subheader("⚠️ Highlight Outstanding")
        df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
        st.dataframe(df_out[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']].head(15),
                     use_container_width=True, hide_index=True)

        st.subheader("📋 Detail Movement Record & Status")
        st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']].head(20),
                     use_container_width=True, hide_index=True)

# ======================== DAFTAR HALAMAN ========================
home_pg = st.Page(home, title="Beranda", icon="🏠", default=True)
stock_pg = st.Page(stock_pltd, title="Stok PLTD", icon="📦")
analisis_pg = st.Page(analisis_stok, title="Analisis Stok", icon="📊")
pemakaian_pg = st.Page(pemakaian, title="Pemakaian", icon="🔥")
transaksi_pg = st.Page(transaksi_project, title="Transaksi Project", icon="🚚")

pg = st.navigation([home_pg, stock_pg, analisis_pg, pemakaian_pg, transaksi_pg])
pg.run()
