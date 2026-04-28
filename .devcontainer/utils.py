import streamlit as st
import pandas as pd
import requests
import io
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread.exceptions import WorksheetNotFound

# ======================== GOOGLE SHEETS CONFIG =========================
PLTD_SHEETS = {
    'Pemaron':        '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli':        '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan':          '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika':         '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    'Bobong':         '1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM',
    'Merawang':       '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir':      '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya':    '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',  # sementara sama
    'Lueng Bata':     '1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g',
    'Ulee Kareng':    '1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU',
    'Waena':          '10NKbFUi0SVh1784OQnSU0ULhWzL6_AK7XLY-8EgKbG8',
    'Sambelia':       '1-8uGvDwZnciEgAXBbogkYWdHQcEClcwuln-hbaR0UAc',
    'Timika 2':       '17FR17wxkeVgd0_GElV59ugetL8nutqiYwQRyY6FqIVE',
    'Wamena':         '14ieCIQwEXf4hZ-RsOeLIMyKi5qEJLtQBwTz35b9JXxs',
}

MASTER_SHEET_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'

# SharePoint
SHAREPOINT_DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
SHAREPOINT_PROJECT_OPS = SHAREPOINT_DELIVERY_URL  # sesuai contoh page 5
SHAREPOINT_PROJECT_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

# Mapping preventive materials (kode part)
PREVENTIVE_CODES = {
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076', '3629140',
    'AF872', 'AF25278', 'AHO1135', '5413003', '3015257', '5412990',
    '5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108',
    'RIMULA R4 X 15W-40'
}

# Lokasi & durasi pengiriman
PLTD_COORDS = {
    'Pemaron':        (-8.1647, 114.6824),
    'Mangoli':        (-1.8821, 125.3732),
    'Tayan':          (-0.0324, 110.1022),
    'Timika':         (-4.5564, 136.8883),
    'Bobong':         (-1.946, 124.388),
    'Merawang':       (-1.9508, 105.9643),
    'Air Anyir':      (-1.9377, 106.1064),
    'Padang Manggar': (-2.1429, 106.1419),
    'Krueng Raya':    (5.6023, 95.5336),
    'Lueng Bata':     (5.5484, 95.3342),
    'Ulee Kareng':    (5.5475, 95.3322),
    'Waena':          (-2.6062, 140.5637),
    'Sambelia':       (-8.3973, 116.6729),
    'Timika 2':       (-4.5564, 136.8883),
    'Wamena':         (-4.0922, 138.9447)
}

DURASI_KIRIM = {
    'Pemaron': 7, 'Mangoli': 14, 'Tayan': 10, 'Timika': 14,
    'Bobong': 14, 'Merawang': 5, 'Air Anyir': 5, 'Padang Manggar': 5,
    'Krueng Raya': 7, 'Lueng Bata': 7, 'Ulee Kareng': 7, 'Waena': 14,
    'Sambelia': 7, 'Timika 2': 14, 'Wamena': 21
}

# Interval PM default (jam)
PM_INTERVAL = {
    'LF3325': 400, 'LF777': 500, '2020PM V30-C': 400, 'FS1006': 500,
    'WF2076': 500, '3629140': 400, 'AF872': 400, 'AF25278': 400,
    'AHO1135': 500, '5413003': 500, '3015257': 500, '5412990': 500,
    '5PK889': 500, '21-3107': 500, '25471145': 500, '23PK2032': 500,
    '21-3110': 500, '25477108': 500, 'RIMULA R4 X 15W-40': 750
}
DEFAULT_PM_INTERVAL = 500  # jam

# Inisialisasi gspread client
@st.cache_resource
def get_gspread_client():
    credentials = st.secrets["gcp_service_account"]
    return gspread.service_account_from_dict(credentials)

# ======================== DATA LOADER ===========================

@st.cache_data(ttl=600)
def load_stock_per_pltd():
    """Membaca stok dari semua sheet PLTD (kolom B,C,D,I = kode, nama, type, qty)"""
    client = get_gspread_client()
    all_data = []
    for pltd, sheet_id in PLTD_SHEETS.items():
        try:
            sh = client.open_by_key(sheet_id)
            ws = sh.sheet1  # asumsi sheet pertama
            # Ambil semua data sebagai list of list
            data = ws.get_all_values()
            if not data or len(data) < 2:
                continue
            # Asumsi baris pertama header; kita ambil kolom B(1),C(2),D(3),I(8)
            # Jika header tidak sesuai, bisa adaptasi
            header = data[0]
            # Cari indeks kolom yang mungkin: 'Kode Material', 'Nama Material', 'Type', 'Qty'
            # Fallback: pakai posisi absolut kalau tidak ada header
            # Pendekatan: kita paksa ambil dari posisi absolut untuk aman
            for row in data[1:]:
                if len(row) < 9:
                    continue
                kode = row[1] if len(row) > 1 else ''
                nama = row[2] if len(row) > 2 else ''
                tipe = row[3] if len(row) > 3 else ''
                qty_str = row[8] if len(row) > 8 else '0'
                try:
                    qty = float(qty_str.replace(',', ''))
                except:
                    qty = 0.0
                if kode or nama:
                    all_data.append({
                        'PLTD': pltd,
                        'Kode Material': kode.strip(),
                        'Nama Material': nama.strip(),
                        'Type Material': tipe.strip(),
                        'Qty': qty
                    })
        except Exception as e:
            st.warning(f"Gagal baca {pltd}: {e}")
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['Jenis'] = df['Kode Material'].apply(
            lambda x: 'Preventive' if str(x).strip() in PREVENTIVE_CODES else 'Corrective')
    return df

@st.cache_data(ttl=600)
def load_master_sheets():
    """Membaca sheet Gabungan, Sheet1, DARI TARIKAN dari master spreadsheet"""
    client = get_gspread_client()
    sh = client.open_by_key(MASTER_SHEET_ID)
    result = {}
    try:
        ws = sh.worksheet('Gabungan')
        result['pemakaian'] = get_as_dataframe(ws, evaluate_formulas=True)
    except WorksheetNotFound:
        result['pemakaian'] = pd.DataFrame()
    try:
        ws = sh.worksheet('Sheet1')
        result['stok_cikande'] = get_as_dataframe(ws, evaluate_formulas=True)
    except:
        result['stok_cikande'] = pd.DataFrame()
    try:
        ws = sh.worksheet('DARI TARIKAN')
        result['harga'] = get_as_dataframe(ws, evaluate_formulas=True)
    except:
        result['harga'] = pd.DataFrame()
    return result

@st.cache_data(ttl=600)
def load_delivery_data():
    """Data transaksi PR MR dari SharePoint (On Delivery)"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(SHAREPOINT_DELIVERY_URL, headers=headers, timeout=20)
        df = pd.read_excel(io.BytesIO(resp.content))
        return df
    except Exception as e:
        st.error(f"Gagal memuat data pengiriman: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_project_data():
    """Untuk page 5 – OPS dan DAS"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    df_ops, df_das = pd.DataFrame(), pd.DataFrame()
    try:
        res_ops = requests.get(SHAREPOINT_PROJECT_OPS, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(res_ops.content))
        df_ops['PROJECT'] = 'PROJECT PLTD'
    except: pass
    try:
        res_das = requests.get(SHAREPOINT_PROJECT_DAS, headers=headers, timeout=20)
        df_das = pd.read_excel(io.BytesIO(res_das.content))
        df_das['PROJECT'] = 'PROJECT DAS'
    except: pass
    df = pd.concat([df_ops, df_das], ignore_index=True)
    if not df.empty and 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
        df['Tahun'] = df['TANGGAL'].dt.year.astype(str)
        df['Bulan'] = df['TANGGAL'].dt.strftime('%B')
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    return df

def get_pltd_coordinates(pltd_name):
    return PLTD_COORDS.get(pltd_name, (None, None))

def get_duration(pltd_name):
    return DURASI_KIRIM.get(pltd_name, 14)

def get_pm_interval(kode_material):
    return PM_INTERVAL.get(str(kode_material).strip(), DEFAULT_PM_INTERVAL)