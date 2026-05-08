import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
import re

st.set_page_config(page_title="Dashboard PLTD Bach", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    [data-testid="stSidebar"] * { color: #CCCCCC !important; }
    [data-testid="stSidebar"] label p { color: #CCCCCC !important; font-weight: 500 !important; }
    [data-testid="stSidebarNav"] span { color: #FFFFFF !important; }
    [data-testid="stSidebarNav"] a { color: #FFFFFF !important; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0A2540; }
    .stPlotlyChart { background: white; border-radius: 10px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    [data-testid="stDataFrame"] { background: white; border-radius: 10px; padding: 8px; }
    .debug-box { background: #FFF3CD; border: 1px solid #FFC107; border-radius: 8px; padding: 12px; margin: 8px 0; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATA SOURCES ====================
PLTD_SHEETS = {
    'Pemaron': '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli': '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan': '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika': '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    'Bobong': '1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM',
    'Merawang': '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir': '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',  # ⚠️ SAMA dengan Padang Manggar
    'Lueng Bata': '1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g',
    'Ulee Kareng': '1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU',
    'Waena': '10NKbFUi0SVh1784OQnSU0ULhWzL6_AK7XLY-8EgKbG8',
    'Sambelia': '1-8uGvDwZnciEgAXBbogkYWdHQcEClcwuln-hbaR0UAc',
    'Timika 2': '17FR17wxkeVgd0_GElV59ugetL8nutqiYwQRyY6FqIVE',
    'Wamena': '14ieCIQwEXf4hZ-RsOeLIMyKi5qEJLtQBwTz35b9JXxs',
}
MASTER_PLTD_ID = '1FsaZyKs3DgJlyZkx5qqpBotNK8Z6C8GOrNeJv3I8AJA'
MASTER_D365_ID = '1C7r0AUC3taKIMR1CVmIle5gm333F4r2VPo7lWeqeH8A'
MASTER_GABUNGAN_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'

# ==================== PREVENTIVE DETECTION ====================
PREVENTIVE_MAP = {
    'LF3325': 'Oil Filter',
    'LF777': 'Oil Filter By pass',
    '2020PM V30-C': 'Element Water Separator',
    'FS1006': 'Fuel Filter',
    'WF2076': 'Water Filter',
    '3629140': 'Cylinder head cover gasket',
    'AF872': 'Air Filter Element',
    'AF25278': 'Air Filter Element',
    'AF25278 (Free)': 'Air Filter Element',
    'AHO1135': 'Air Filter Element (Aksa)',
    '5413003': 'V-BELT Fan Radiator',
    '3015257': 'V-BELT (Aksa)',
    '5412990': 'V-BELT Alternator',
    '5PK889': 'V-BELT Alternator',
    '21-3107': 'V-BELT Alternator',
    '25471145': 'V-BELT Alternator',
    '23PK2032': 'V-BELT Fan Radiator',
    '21-3110': 'V-BELT Fan Radiator',
    '25477108': 'V-BELT Fan Radiator',
    'RIMULA R4 X 15W-40': 'Oli Shell',
    'WCL': 'Coolant',
}

# Multi-varian mapping: kode gabungan -> primary code
MULTI_VARIANT_MAP = {
    '5PK889 / 21-3107 / 25471145': '5PK889',
    '23PK2032 / 21-3110 / 25477108': '23PK2032',
}

NORMALIZE_NAME = {
    'AF25278': 'Air Filter Element',
    'AF872': 'Air Filter Element',
    'RIMULA R4 X 15W-40': 'Oli Shell',
    'WCL': 'Coolant',
    'ACC-Y': 'ACCU 12V N150 YUASA',
}

def norm(kode, nama):
    """Normalisasi nama material"""
    k = str(kode).strip().upper()
    
    # Cek multi-varian dulu
    if k in MULTI_VARIANT_MAP:
        primary = MULTI_VARIANT_MAP[k]
        if primary in PREVENTIVE_MAP:
            return PREVENTIVE_MAP[primary]
    
    if k in NORMALIZE_NAME:
        return NORMALIZE_NAME[k]
    for pk, pn in PREVENTIVE_MAP.items():
        if k == pk.upper():
            return pn
    
    # Deteksi Oli Shell varian (Drum vs IBC)
    nama_lower = str(nama).strip().lower()
    if 'rimula' in k.lower() or 'rimula' in nama_lower:
        if 'drum' in nama_lower or '209' in nama_lower:
            return 'Oli Shell (Drum)'
        elif 'ibc' in nama_lower or '1000' in nama_lower:
            return 'Oli Shell (IBC)'
        return 'Oli Shell'
    
    return nama

def get_primary_code(kode):
    """Ambil kode primer dari kode multi-varian"""
    k = str(kode).strip().upper()
    if k in MULTI_VARIANT_MAP:
        return MULTI_VARIANT_MAP[k]
    # Ambil kode pertama jika ada split
    parts = re.split(r'\s*/\s*', k)
    return parts[0].strip() if parts else k

def is_prev(kode):
    """Cek apakah kode termasuk preventive"""
    k = str(kode).strip().upper()
    for part in re.split(r'\s*/\s*', k):
        part = part.strip()
        if part in PREVENTIVE_MAP:
            return True
    if k in PREVENTIVE_MAP:
        return True
    return False

def is_valid(kode, nama):
    if not nama or not nama.strip():
        return False
    if re.match(r'^\d+(\.\d+)?$', nama.strip()):
        return False
    return True

# ==================== GSPREAD CLIENT ====================
@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

# ==================== LOAD ALL DATA ====================
@st.cache_data(ttl=600)
def load_all():
    cl = get_client()
    res = {
        'stock': pd.DataFrame(),
        'm1': None,
        'm2': None,
        'cik': pd.DataFrame(),
        'pemakaian': pd.DataFrame(),
        'debug_log': []  # Untuk menyimpan log debug
    }

    debug_log = []

    # STOK PLTD
    rows = []
    for pltd, sid in PLTD_SHEETS.items():
        try:
            sh = cl.open_by_key(sid)
            data = sh.sheet1.get_all_values()
            debug_log.append(f"✅ {pltd}: {len(data)-1} baris data (termasuk header)")
            if len(data) < 2:
                debug_log.append(f"⚠️ {pltd}: Data < 2 baris, skip")
                continue
            count_valid = 0
            for r in data[1:]:
                if len(r) < 9:
                    continue
                nama = r[2].strip() if len(r) > 2 else ''
                kode = r[3].strip() if len(r) > 3 else ''
                qty_s = r[8].strip() if len(r) > 8 else '0'
                if not is_valid(kode, nama):
                    continue
                try:
                    qty = float(qty_s.replace(',', '')) if qty_s else 0.0
                except:
                    qty = 0.0
                rows.append((pltd.strip().upper(), kode.upper().strip(), norm(kode, nama).strip(), qty, get_primary_code(kode)))
                count_valid += 1
            debug_log.append(f"   → {count_valid} baris valid")
        except Exception as e:
            debug_log.append(f"❌ {pltd}: GAGAL - {str(e)[:100]}")
    
    df = pd.DataFrame(rows, columns=['PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Primary Code'])
    if not df.empty:
        df['Jenis'] = df['Kode Material'].apply(lambda k: 'Preventive' if is_prev(k) else 'Corrective')
        df = df.groupby(['PLTD', 'Kode Material', 'Nama Material', 'Primary Code', 'Jenis'], as_index=False)['Qty'].sum()
    res['stock'] = df

    # MASTER DATA
    try:
        sh = cl.open_by_key(MASTER_PLTD_ID)
        debug_log.append(f"✅ Master PLTD: {len(sh.worksheets())} worksheets")
        for ws in sh.worksheets():
            t = ws.title.strip().lower()
            debug_log.append(f"   Sheet: '{ws.title}' → cocok: master1={'master' in t and '1' in t}, master2={'master' in t and '2' in t}")
            
            if ('master' in t or 'mater' in t) and '1' in t:
                try:
                    d = get_as_dataframe(ws, evaluate_formulas=True)
                    d.columns = [str(c).strip() for c in d.columns]
                    debug_log.append(f"   M1 columns: {list(d.columns)}")
                    
                    pltd_col = next((c for c in d.columns if 'pltd' in c.lower()), None)
                    kode_col = next((c for c in d.columns if 'kode' in c.lower()), None)
                    aktual_col = next((c for c in d.columns if 'aktual' in c.lower()), None)
                    pm_col = next((c for c in d.columns if 'pm' in c.lower() and 'cf' in c.lower()), None)
                    
                    if pltd_col:
                        d.rename(columns={pltd_col: 'pltd'}, inplace=True)
                    if kode_col:
                        d.rename(columns={kode_col: 'kode_material'}, inplace=True)
                    if aktual_col:
                        d.rename(columns={aktual_col: 'keb_aktual'}, inplace=True)
                    if pm_col:
                        d.rename(columns={pm_col: 'keb_pm'}, inplace=True)
                    
                    for col in ['pltd', 'kode_material']:
                        if col in d.columns:
                            d[col] = d[col].astype(str).str.strip().str.upper()
                    
                    # Tambah primary code
                    if 'kode_material' in d.columns:
                        d['primary_code'] = d['kode_material'].apply(get_primary_code)
                    
                    for col in ['keb_aktual', 'keb_pm']:
                        if col in d.columns:
                            d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0)
                    
                    # Kalau keb_pm tidak ada, pakai keb_aktual
                    if 'keb_pm' not in d.columns and 'keb_aktual' in d.columns:
                        d['keb_pm'] = d['keb_aktual']
                    
                    res['m1'] = d
                    debug_log.append(f"   M1 loaded: {len(d)} baris, PLTD unik: {d['pltd'].nunique() if 'pltd' in d.columns else 'N/A'}")
                except Exception as e:
                    debug_log.append(f"   ❌ M1 error: {str(e)[:100]}")
            
            if ('master' in t or 'mater' in t) and '2' in t:
                try:
                    d = get_as_dataframe(ws, evaluate_formulas=True)
                    d.columns = [str(c).strip() for c in d.columns]
                    pltd_col = next((c for c in d.columns if 'pltd' in c.lower()), None)
                    dur_col = next((c for c in d.columns if 'durasi' in c.lower()), None)
                    if pltd_col:
                        d.rename(columns={pltd_col: 'pltd'}, inplace=True)
                    if dur_col:
                        d.rename(columns={dur_col: 'durasi_kirim'}, inplace=True)
                    if 'pltd' in d.columns:
                        d['pltd'] = d['pltd'].astype(str).str.strip().str.upper()
                    if 'durasi_kirim' in d.columns:
                        d['durasi_kirim'] = pd.to_numeric(d['durasi_kirim'], errors='coerce').fillna(14)
                    else:
                        d['durasi_kirim'] = 14
                    res['m2'] = d
                    debug_log.append(f"   M2 loaded: {len(d)} baris")
                except Exception as e:
                    debug_log.append(f"   ❌ M2 error: {str(e)[:100]}")
    except Exception as e:
        debug_log.append(f"❌ Master PLTD GAGAL: {str(e)[:100]}")

    # CIKANDE
    try:
        sh = cl.open_by_key(MASTER_D365_ID)
        ws = sh.worksheet('Sheet1')
        data = ws.get_all_values()
        hrow = 0
        for i, row in enumerate(data[:5]):
            if 'cikande' in ' '.join([str(c).lower() for c in row]):
                hrow = i
                break
        header = [str(c).strip().lower() for c in data[hrow]]
        i_nama = next((i for i, h in enumerate(header) if 'nama' in h or 'material' in h or 'matrial' in h), 0)
        i_kode = next((i for i, h in enumerate(header) if 'kode' in h or 'seri' in h), 1)
        i_qty = next((i for i, h in enumerate(header) if 'cikande' in h), 2)
        crows = []
        for r in data[hrow + 1:]:
            if len(r) <= max(i_nama, i_kode, i_qty):
                continue
            nama = r[i_nama].strip() if i_nama < len(r) else ''
            kode = r[i_kode].strip() if i_kode < len(r) else ''
            qty_s = r[i_qty].strip() if i_qty < len(r) else '0'
            try:
                qty = float(qty_s.replace(',', '')) if qty_s else 0.0
            except:
                qty = 0.0
            if nama or kode:
                crows.append({
                    'Kode Material': kode.upper().strip(),
                    'Nama Material': norm(kode, nama).strip(),
                    'Primary Code': get_primary_code(kode),
                    'WH Cikande': qty
                })
        dc = pd.DataFrame(crows)
        if not dc.empty:
            dc = dc.groupby(['Kode Material', 'Nama Material', 'Primary Code'], as_index=False)['WH Cikande'].sum()
        res['cik'] = dc
        debug_log.append(f"✅ Cikande: {len(dc)} baris")
    except Exception as e:
        debug_log.append(f"❌ Cikande GAGAL: {str(e)[:100]}")

    # PEMAKAIAN (SHEET GABUNGAN)
    try:
        sh = cl.open_by_key(MASTER_GABUNGAN_ID)
        ws = sh.worksheet('Gabungan')
        data = ws.get_all_values()
        if len(data) >= 2:
            header_row = None
            for i, row in enumerate(data[:10]):
                row_text = ' '.join([str(c).lower() for c in row])
                if 'tanggal' in row_text and 'nama' in row_text:
                    header_row = i
                    break
            if header_row is None:
                header_row = 2
            p_rows = []
            for r in data[header_row + 1:]:
                if len(r) < 2:
                    continue
                if not any(str(c).strip() for c in r[:5]):
                    continue
                tanggal = r[0].strip() if len(r) > 0 else ''
                masuk = r[1].strip() if len(r) > 1 else '0'
                keluar = r[2].strip() if len(r) > 2 else '0'
                stok = r[3].strip() if len(r) > 3 else '0'
                keterangan = r[4].strip() if len(r) > 4 else ''
                transaksi = r[7].strip() if len(r) > 7 else ''
                nama_material = r[8].strip() if len(r) > 8 else ''
                jobtype = r[9].strip() if len(r) > 9 else ''
                gudang = r[11].strip() if len(r) > 11 else ''
                harga_raw = r[14].strip() if len(r) > 14 else '0'
                if nama_material:
                    try:
                        m = float(masuk.replace(',', '')) if masuk else 0.0
                    except:
                        m = 0.0
                    try:
                        k = float(keluar.replace(',', '')) if keluar else 0.0
                    except:
                        k = 0.0
                    try:
                        s = float(stok.replace(',', '')) if stok else 0.0
                    except:
                        s = 0.0
                    try:
                        if '.' in harga_raw and ',' not in harga_raw:
                            h = float(harga_raw.replace('.', ''))
                        elif ',' in harga_raw:
                            h = float(harga_raw.replace(',', '.'))
                        else:
                            h = float(harga_raw)
                    except:
                        h = 0.0
                    p_rows.append({
                        'Tanggal': tanggal,
                        'Nama Material': nama_material,
                        'Masuk': m,
                        'Keluar': k,
                        'Stok': s,
                        'Gudang': gudang,
                        'Keterangan': keterangan,
                        'Transaksi': transaksi,
                        'JobType': jobtype,
                        'HARGA_D365': h,
                        'TOTAL_COST': k * h,
                    })
            df_p = pd.DataFrame(p_rows)
            if not df_p.empty:
                df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'], errors='coerce')
            res['pemakaian'] = df_p
            debug_log.append(f"✅ Gabungan: {len(df_p)} baris")
    except Exception as e:
        debug_log.append(f"❌ Gabungan GAGAL: {str(e)[:100]}")

    res['debug_log'] = debug_log
    return res

# ==================== HOME ====================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    data = load_all()
    df = data.get('stock', pd.DataFrame())
    if df.empty:
        st.warning("Data belum tersedia.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("PLTD", df['PLTD'].nunique())
    c2.metric("Total Stok", f"{df['Qty'].sum():,.0f}")
    c3.metric("Prev / Corr", f"{(df['Jenis'] == 'Preventive').sum()} / {(df['Jenis'] == 'Corrective').sum()}")
    coords = {
        'PEMARON': (-8.16, 114.68), 'MANGOLI': (-1.88, 125.37), 'TAYAN': (-0.03, 110.10),
        'TIMIKA': (-4.56, 136.89), 'BOBONG': (-1.95, 124.39), 'MERAWANG': (-1.95, 105.96),
        'AIR ANYIR': (-1.94, 106.11), 'PADANG MANGGAR': (-2.14, 106.14), 'KRUENG RAYA': (5.60, 95.53),
        'LUENG BATA': (5.55, 95.33), 'ULEE KARENG': (5.55, 95.33), 'WAENA': (-2.61, 140.56),
        'SAMBELIA': (-8.40, 116.67), 'TIMIKA 2': (-4.56, 136.89), 'WAMENA': (-4.09, 138.94)
    }
    loc = df[['PLTD']].drop_duplicates()
    loc['lat'] = loc['PLTD'].map(lambda x: coords.get(x, (None, None))[0])
    loc['lon'] = loc['PLTD'].map(lambda x: coords.get(x, (None, None))[1])
    st.map(loc.dropna(subset=['lat']), latitude='lat', longitude='lon', zoom=4, height=350)

# ==================== PAGE STOCK ====================
# ==================== HELPER: HITUNG SISA BULAN ====================
def hitung_sisa_bulan(df_stock, m1):
    """
    Menghitung Sisa Bulan dengan logika:
    1. Merge stok dengan M1 via Primary Code (prioritas)
    2. Fallback merge via Kode Material untuk yang tidak match
    3. Sisa Bulan = round(Qty / Keb_Aktual, 1)
    """
    if df_stock.empty or m1 is None:
        return pd.DataFrame()
    
    # Siapkan M1 - ambil kolom yang diperlukan
    # Pastikan kolom 'primary_code' ada, kalau tidak buat dari kode_material
    if 'primary_code' not in m1.columns:
        m1['primary_code'] = m1['kode_material'].apply(get_primary_code)
    
    m1_use = m1[['pltd', 'kode_material', 'primary_code', 'keb_aktual']].copy()
    m1_use.columns = ['PLTD_M1', 'Kode_M1', 'Primary_Code_M1', 'Keb_Aktual']
    
    # Clean M1
    m1_use['PLTD_M1'] = m1_use['PLTD_M1'].astype(str).str.strip().str.upper()
    m1_use['Primary_Code_M1'] = m1_use['Primary_Code_M1'].astype(str).str.strip().str.upper()
    m1_use['Kode_M1'] = m1_use['Kode_M1'].astype(str).str.strip().str.upper()
    m1_use['Keb_Aktual'] = pd.to_numeric(m1_use['Keb_Aktual'], errors='coerce').fillna(0)
    
    # HAPUS baris yang tidak valid
    m1_use = m1_use[m1_use['PLTD_M1'] != '']
    m1_use = m1_use[m1_use['Primary_Code_M1'] != '']
    
    # AMBIL MAX Keb_Aktual per PLTD + Primary Code (karena mungkin ada duplikat)
    m1_use = m1_use.groupby(['PLTD_M1', 'Primary_Code_M1'], as_index=False).agg({
        'Keb_Aktual': 'max',
        'Kode_M1': 'first'  # simpan salah satu kode
    })
    
    # Siapkan stock
    stok = df_stock.copy()
    stok['PLTD'] = stok['PLTD'].astype(str).str.strip().str.upper()
    stok['Primary Code'] = stok['Primary Code'].astype(str).str.strip().str.upper()
    stok['Kode Material'] = stok['Kode Material'].astype(str).str.strip().str.upper()
    stok = stok.reset_index(drop=True)
    
    # Merge step 1: via Primary Code
    merged = stok.merge(
        m1_use,
        left_on=['PLTD', 'Primary Code'],
        right_on=['PLTD_M1', 'Primary_Code_M1'],
        how='left'
    )
    
    # Merge step 2: untuk yang masih NaN, coba via Kode Material
    mask_null = merged['Keb_Aktual'].isna() | (merged['Keb_Aktual'] == 0)
    
    if mask_null.any():
        # Siapkan M1 untuk fallback via Kode Material
        m1_kode = m1[['pltd', 'kode_material', 'keb_aktual']].copy()
        m1_kode.columns = ['PLTD_M1', 'Kode_M1', 'Keb_Aktual_kode']
        m1_kode['PLTD_M1'] = m1_kode['PLTD_M1'].astype(str).str.strip().str.upper()
        m1_kode['Kode_M1'] = m1_kode['Kode_M1'].astype(str).str.strip().str.upper()
        m1_kode['Keb_Aktual_kode'] = pd.to_numeric(m1_kode['Keb_Aktual_kode'], errors='coerce').fillna(0)
        m1_kode = m1_kode.groupby(['PLTD_M1', 'Kode_M1'], as_index=False)['Keb_Aktual_kode'].max()
        
        # Ambil baris yang null saja
        null_rows = merged[mask_null].copy()
        # Buang kolom M1 dari merge pertama
        null_cols_to_drop = ['PLTD_M1', 'Primary_Code_M1', 'Kode_M1', 'Keb_Aktual']
        null_rows = null_rows.drop(columns=[c for c in null_cols_to_drop if c in null_rows.columns])
        
        # Merge ulang via Kode Material
        null_fixed = null_rows.merge(
            m1_kode,
            left_on=['PLTD', 'Kode Material'],
            right_on=['PLTD_M1', 'Kode_M1'],
            how='left'
        )
        
        # Update nilai di merged untuk baris yang null
        null_indices = merged.index[mask_null]
        for i, idx in enumerate(null_indices):
            if i < len(null_fixed):
                new_val = null_fixed.iloc[i]['Keb_Aktual_kode']
                if pd.notna(new_val) and new_val > 0:
                    merged.loc[idx, 'Keb_Aktual'] = new_val
    
    # Bersihkan
    merged['Keb_Aktual'] = pd.to_numeric(merged['Keb_Aktual'], errors='coerce').fillna(0)
    
    # Buang kolom M1
    merged = merged.drop(columns=['PLTD_M1', 'Primary_Code_M1', 'Kode_M1'], errors='ignore')
    
    # HITUNG Sisa Bulan = round(Qty / Keb_Aktual, 1) — sesuai rumus manual
    merged['Sisa_Bulan'] = np.where(
        merged['Keb_Aktual'] > 0,
        round(merged['Qty'] / merged['Keb_Aktual'], 1),
        0.0
    )
    
    return merged

# ==================== PAGE STOCK ====================
def page_stock():
    st.title("📦 Stok Material PLTD")
    data = load_all()
    df = data['stock'].copy()
    debug_log = data.get('debug_log', [])
    
    if df.empty:
        st.warning("Data belum tersedia.")
        return
    
    cik = data['cik']
    if not cik.empty:
        df = df.merge(cik, on=['Kode Material', 'Nama Material', 'Primary Code'], how='left')
        df['WH Cikande'] = df['WH Cikande'].fillna(0)
    else:
        df['WH Cikande'] = 0.0

    # ---- DEBUG PANEL ----
    with st.sidebar:
        with st.expander("🔧 DEBUG INFO", expanded=False):
            st.markdown("### Log Load Data")
            for log in debug_log:
                if '❌' in log:
                    st.error(log)
                elif '⚠️' in log:
                    st.warning(log)
                else:
                    st.text(log)
            
            st.markdown("---")
            st.markdown("### PLTD di Stock vs M1")
            m1 = data['m1']
            if m1 is not None and 'pltd' in m1.columns:
                pltd_stok = set(df['PLTD'].unique())
                pltd_m1 = set(m1['pltd'].unique())
                st.write(f"**Di Stock:** {sorted(pltd_stok)}")
                st.write(f"**Di M1:** {sorted(pltd_m1)}")
                missing_stok = pltd_m1 - pltd_stok
                missing_m1 = pltd_stok - pltd_m1
                if missing_stok:
                    st.warning(f"⚠️ Di M1 tapi TIDAK di stock: {sorted(missing_stok)}")
                if missing_m1:
                    st.info(f"ℹ️ Di stock tapi TIDAK di M1: {sorted(missing_m1)}")
            
            st.markdown("---")
            st.markdown("### Sample Stok per PLTD")
            for pltd in sorted(df['PLTD'].unique()):
                count = len(df[df['PLTD'] == pltd])
                qty_sum = df[df['PLTD'] == pltd]['Qty'].sum()
                st.text(f"{pltd}: {count} baris, Qty={qty_sum:,.0f}")
    
    st.sidebar.header("Filter Stok")
    sel_pltd = st.sidebar.multiselect("PLTD", sorted(df['PLTD'].unique()), default=[])
    sel_jenis = st.sidebar.multiselect("Jenis Material", ['Preventive', 'Corrective'], default=[])
    sel_nama = st.sidebar.multiselect("Nama Material", sorted(df['Nama Material'].unique()), default=[])
    sel_kode = st.sidebar.multiselect("Kode Material", sorted(df['Kode Material'].unique()), default=[])
    highlight_only = st.sidebar.checkbox("🔴 Highlight hanya yang kritis (≤1.5 bulan)", value=False)

    f = df.copy()
    if sel_pltd:
        f = f[f['PLTD'].isin(sel_pltd)]
    if sel_jenis:
        f = f[f['Jenis'].isin(sel_jenis)]
    if sel_nama:
        f = f[f['Nama Material'].isin(sel_nama)]
    if sel_kode:
        f = f[f['Kode Material'].isin(sel_kode)]

    prev = f[f['Jenis'] == 'Preventive'].copy()
    corr = f[f['Jenis'] == 'Corrective'].copy()
    m1 = data['m1']

    st.subheader("🔵 Material Preventive")
    if not prev.empty:
        p = prev.pivot_table(index=['Kode Material', 'Nama Material'], columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
        p = p.round(0).astype(int)
        cik_p = prev.groupby(['Kode Material', 'Nama Material'])['WH Cikande'].max().round(0).astype(int)
        p = p.join(cik_p)
        p['Total'] = p.drop(columns='WH Cikande').sum(axis=1)
        p = p.reset_index()
        pltd_cols = [c for c in p.columns if c not in ('Kode Material', 'Nama Material', 'WH Cikande', 'Total')]
        p = p[['Kode Material', 'Nama Material'] + pltd_cols + ['WH Cikande', 'Total']]
        cfg = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Preventive.")

    st.subheader("⏳ Sisa Stok Preventive dalam Bulan")
    if not prev.empty and m1 is not None:
        sisa_df = hitung_sisa_bulan(prev, m1)
        
        if not sisa_df.empty:
            sp = sisa_df.pivot_table(
                index=['Kode Material', 'Nama Material'],
                columns='PLTD',
                values='Sisa_Bulan',
                aggfunc='first',
                fill_value=0.0
            )
            sp = sp.reset_index()
            pltd_cols_s = [c for c in sp.columns if c not in ('Kode Material', 'Nama Material')]
            sp = sp[['Kode Material', 'Nama Material'] + pltd_cols_s]
            
            if highlight_only:
                mask = (sp[pltd_cols_s] > 0) & (sp[pltd_cols_s] <= 1.5)
                sp = sp[mask.any(axis=1)]
            
            cfg_s = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
            for col in pltd_cols_s:
                cfg_s[col] = st.column_config.NumberColumn(format="%.1f")
            
            def hl(val):
                if isinstance(val, (int, float)) and val <= 1.5:
                    return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                return ''
            
            st.dataframe(sp.style.map(hl, subset=pltd_cols_s), column_config=cfg_s, use_container_width=True, hide_index=True)
            
            # Debug: tampilkan sample perhitungan
            with st.expander("🔍 Debug: Sample Perhitungan Sisa Bulan"):
                sample = sisa_df[['PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Keb_Aktual', 'Sisa_Bulan']].head(30)
                st.dataframe(sample, use_container_width=True, hide_index=True)
        else:
            st.info("Data Sisa Bulan tidak tersedia.")
    else:
        st.info("Data tidak lengkap untuk menghitung Sisa Bulan.")

    st.subheader("🟠 Material Corrective")
    if not corr.empty:
        p = corr.pivot_table(index=['Kode Material', 'Nama Material'], columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
        p = p.round(0).astype(int)
        cik_c = corr.groupby(['Kode Material', 'Nama Material'])['WH Cikande'].max().round(0).astype(int)
        p = p.join(cik_c)
        p['Total'] = p.drop(columns='WH Cikande').sum(axis=1)
        p = p.reset_index()
        pltd_cols = [c for c in p.columns if c not in ('Kode Material', 'Nama Material', 'WH Cikande', 'Total')]
        p = p[['Kode Material', 'Nama Material'] + pltd_cols + ['WH Cikande', 'Total']]
        cfg = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Corrective.")

# ==================== PAGE ANALISIS ====================
def page_analisis():
    st.title("📊 Analisis Pemakaian Material")
    data = load_all()
    df_pakai = data.get('pemakaian', pd.DataFrame()).copy()
    if df_pakai.empty:
        st.warning("Data pemakaian belum tersedia.")
        return

    nama_map = {
        'water coollant reco-cool - drum': 'WATER COOLLANT RECO-COOL',
        'filter udara af872': 'FILTER UDARA AF872',
        'air filter element af872': 'FILTER UDARA AF872',
        'element racor 2020pm parker': 'ELEMENT RACOR 2020PM',
        'oil filter lf777 fleet gruad': 'OIL FILTER LF777',
        'coolant filter wf2076 fleetguard': 'COOLANT FILTER WF2076',
        'oil shell rimula r3mv 15w-40 (drum @ 209 ltr)': 'OIL SHELL RIMULA R3MV',
        'oli rimula r4 x 15w-40 (ibc @ 1000 liter)': 'OLI RIMULA R4 (IBC)',
        'filter separator fs 1006 fleetguard': 'FILTER SEPARATOR FS1006',
        'oil filter lf3325 fleetguard': 'OIL FILTER LF3325',
    }
    df_pakai['Nama Material'] = df_pakai['Nama Material'].str.strip().str.lower()
    df_pakai['Nama Material'] = df_pakai['Nama Material'].apply(lambda x: nama_map.get(x, x.upper()))
    for col in ['Masuk', 'Keluar', 'Stok', 'TOTAL_COST']:
        if col in df_pakai.columns:
            df_pakai[col] = pd.to_numeric(df_pakai[col], errors='coerce').fillna(0)
    if 'Tanggal' in df_pakai.columns:
        df_pakai['Tanggal'] = pd.to_datetime(df_pakai['Tanggal'], errors='coerce')
        df_pakai['Tahun'] = df_pakai['Tanggal'].dt.year.astype('Int64').astype(str).replace('<NA>', '')
        bulan_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
                     7: 'Jul', 8: 'Ags', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'}
        df_pakai['Periode'] = df_pakai['Tanggal'].dt.month.map(bulan_map).fillna('')
        df_pakai['BulanStr'] = df_pakai['Tanggal'].dt.strftime('%Y-%m').replace('NaT', '')

    st.sidebar.header("Filter Analisis")
    nama_opts = sorted(df_pakai['Nama Material'].unique().astype(str))
    sel_nama = st.sidebar.multiselect("Nama Material", nama_opts, default=[])
    gudang_opts = sorted(df_pakai['Gudang'].unique().astype(str)) if 'Gudang' in df_pakai.columns else []
    sel_gudang = st.sidebar.multiselect("Gudang", gudang_opts, default=[])
    if 'Tahun' in df_pakai.columns:
        tahun_opts = sorted([str(t) for t in df_pakai['Tahun'].unique() if pd.notna(t) and str(t) not in ['', '<NA>', 'None', 'nan']])
    else:
        tahun_opts = []
    sel_tahun = st.sidebar.multiselect("Tahun", tahun_opts, default=[])
    periode_opts = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']
    sel_periode = st.sidebar.multiselect("Bulan", periode_opts, default=[])

    f = df_pakai.copy()
    if sel_nama:
        f = f[f['Nama Material'].astype(str).isin(sel_nama)]
    if sel_gudang:
        f = f[f['Gudang'].astype(str).isin(sel_gudang)]
    if sel_tahun:
        f = f[f['Tahun'].astype(str).isin(sel_tahun)]
    if sel_periode:
        f = f[f['Periode'].astype(str).isin(sel_periode)]

    pivot_cost = f.pivot_table(index='Nama Material', values=['Keluar', 'TOTAL_COST'], aggfunc={'Keluar': 'sum', 'TOTAL_COST': 'sum'})
    pivot_cost = pivot_cost[pivot_cost['TOTAL_COST'] > 0]
    grand_total_cost = pivot_cost['TOTAL_COST'].sum()

    st.subheader("📈 Ringkasan Pemakaian")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Transaksi", len(f))
    k2.metric("Total Keluar", f"{pivot_cost['Keluar'].sum():,.0f}")
    k3.metric("Material Unik", len(pivot_cost))
    k4.metric("💰 Grand Total Cost", f"Rp {grand_total_cost:,.0f}")
    st.markdown("---")

    st.subheader("📈 Tren Pemakaian Material")
    trend = f[f['BulanStr'] != ''].groupby('BulanStr').agg(Masuk=('Masuk', 'sum'), Keluar=('Keluar', 'sum')).reset_index().sort_values('BulanStr')
    if not trend.empty:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=trend['BulanStr'], y=trend['Masuk'], mode='lines+markers+text', name='Inbound',
                                  line=dict(color='#4B8BBE', width=2), marker=dict(size=8),
                                  text=trend['Masuk'].apply(lambda x: f'{x:,.0f}'), textposition='top center'))
        fig1.add_trace(go.Scatter(x=trend['BulanStr'], y=trend['Keluar'], mode='lines+markers+text', name='Outbound',
                                  line=dict(color='#E67E22', width=2), marker=dict(size=8),
                                  text=trend['Keluar'].apply(lambda x: f'{x:,.0f}'), textposition='top center'))
        fig1.update_layout(height=400, xaxis_title='Periode', yaxis_title='Quantity',
                          legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5), xaxis=dict(tickangle=-45))
        st.plotly_chart(fig1, use_container_width=True)
    st.markdown("---")

    st.subheader("💰 TOP 10 Cost Material")
    top_cost = pivot_cost.nlargest(10, 'TOTAL_COST').sort_values('TOTAL_COST', ascending=True)
    if not top_cost.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(y=top_cost.index, x=top_cost['TOTAL_COST'], orientation='h', marker=dict(color='#27AE60'),
                              text=top_cost['TOTAL_COST'].apply(lambda x: f'Rp {x:,.0f}'), textposition='outside'))
        fig2.update_layout(height=400, margin=dict(l=250, r=100, t=30, b=20))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("---")

    st.subheader("📥📤 TOP 10 Material: Inbound vs Outbound")
    top_10 = f.groupby('Nama Material').agg(Masuk=('Masuk', 'sum'), Keluar=('Keluar', 'sum')).sum(axis=1).nlargest(10).index.tolist()
    agg = f[f['Nama Material'].isin(top_10)].groupby('Nama Material').agg(Masuk=('Masuk', 'sum'), Keluar=('Keluar', 'sum')).reset_index().sort_values('Masuk', ascending=True)
    if not agg.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(y=agg['Nama Material'], x=agg['Masuk'], name='Inbound', orientation='h', marker=dict(color='#4B8BBE'),
                              text=agg['Masuk'].apply(lambda x: f'{x:,.0f}'), textposition='outside'))
        fig3.add_trace(go.Bar(y=agg['Nama Material'], x=agg['Keluar'], name='Outbound', orientation='h', marker=dict(color='#E67E22'),
                              text=agg['Keluar'].apply(lambda x: f'{x:,.0f}'), textposition='outside'))
        fig3.update_layout(barmode='group', height=400, margin=dict(l=200, r=80, t=30, b=60),
                          legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5))
        st.plotly_chart(fig3, use_container_width=True)
    st.markdown("---")

    st.subheader("📋 Detail Pemakaian Material")
    cols = ['Tanggal', 'Nama Material', 'Masuk', 'Keluar', 'Stok', 'Gudang', 'Keterangan', 'Transaksi', 'JobType', 'TOTAL_COST']
    cols = [c for c in cols if c in f.columns]
    if 'Tanggal' in f.columns:
        f = f.sort_values('Tanggal', ascending=False)
    st.dataframe(f[cols], use_container_width=True, hide_index=True, height=400)

# ==================== PAGE PROPOSE ====================
def page_propose():
    st.title("📦 Propose Order Material")
    st.markdown("*Analisis stok vs kebutuhan untuk perencanaan pengadaan*")

    data = load_all()
    df_stock = data.get('stock', pd.DataFrame()).copy()
    m1 = data.get('m1')

    if df_stock.empty or m1 is None:
        st.warning("Data stok atau Master Data 1 tidak tersedia.")
        return

    # GUNAKAN FUNGSI hitung_sisa_bulan YANG SAMA
    sisa_df = hitung_sisa_bulan(df_stock[df_stock['Jenis'] == 'Preventive'], m1)

    if sisa_df.empty:
        st.warning("Data Sisa Bulan tidak tersedia.")
        return

    # Dapatkan Keb_PM dari M1
    m1_pm = m1[['primary_code', 'keb_pm']].copy()
    m1_pm.columns = ['Primary Code', 'Keb_PM']
    m1_pm['Primary Code'] = m1_pm['Primary Code'].astype(str).str.strip().str.upper()
    m1_pm['Keb_PM'] = pd.to_numeric(m1_pm['Keb_PM'], errors='coerce').fillna(0)
    m1_pm = m1_pm.drop_duplicates(subset=['Primary Code'], keep='first')

    # Merge Keb_PM ke sisa_df
    sisa_df['Primary Code'] = sisa_df['Primary Code'].astype(str).str.strip().str.upper()
    sisa_df = sisa_df.merge(m1_pm, on='Primary Code', how='left')
    sisa_df['Keb_PM'] = pd.to_numeric(sisa_df['Keb_PM'], errors='coerce').fillna(sisa_df['Keb_Aktual'])

    # Tambahkan PLTD dari M1 yang tidak ada di stok
    pltd_stok = set(sisa_df['PLTD'].unique())
    pltd_m1 = set(m1['pltd'].dropna().str.strip().str.upper().unique())
    pltd_missing = pltd_m1 - pltd_stok

    if pltd_missing:
        m1_missing = m1[m1['pltd'].str.strip().str.upper().isin(pltd_missing)].copy()
        m1_missing['PLTD'] = m1_missing['pltd'].str.strip().str.upper()
        m1_missing['Primary Code'] = m1_missing['primary_code'].astype(str).str.strip().str.upper()
        
        missing_rows = []
        for _, row in m1_missing.iterrows():
            missing_rows.append({
                'PLTD': row['PLTD'],
                'Kode Material': row.get('kode_material', row.get('Primary Code', '')),
                'Nama Material': PREVENTIVE_MAP.get(row.get('Primary Code', '').upper(), 'Unknown'),
                'Primary Code': row.get('Primary Code', ''),
                'Qty': 0,
                'Jenis': 'Preventive',
                'Keb_Aktual': pd.to_numeric(row.get('keb_aktual', 0), errors='coerce') or 0,
                'Keb_PM': pd.to_numeric(row.get('keb_pm', 0), errors='coerce') or 0,
                'Sisa_Bulan': 0.0,
            })
        
        if missing_rows:
            missing_df = pd.DataFrame(missing_rows)
            sisa_df = pd.concat([sisa_df, missing_df], ignore_index=True)

    # Fill NA
    for col in ['Qty', 'Keb_PM', 'Keb_Aktual']:
        if col in sisa_df.columns:
            sisa_df[col] = pd.to_numeric(sisa_df[col], errors='coerce').fillna(0)

    st.sidebar.header("🎯 Filter Propose")
    pltd_opts = sorted(sisa_df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("📍 PLTD", pltd_opts, default=[])
    jumlah_bulan = st.sidebar.slider("📅 Jumlah Bulan Order", min_value=1, max_value=12, value=3, step=1)
    status_opts = ['🔴 Urgent', '🟠 Warning', '🟡 Perlu Order', '🟢 Aman']
    sel_status = st.sidebar.multiselect("📊 Status", status_opts, default=[])

    prev = sisa_df.copy()
    if sel_pltd:
        prev = prev[prev['PLTD'].isin(sel_pltd)]

    prev['Keb_N_Bulan'] = prev['Keb_Aktual'] * jumlah_bulan
    prev['Propose_N_Bulan'] = np.ceil(np.maximum(0, prev['Keb_N_Bulan'] - prev['Qty']))

    def get_status(row):
        if row['Keb_Aktual'] <= 0:
            return '⚪ No Data'
        if row['Qty'] >= row['Keb_N_Bulan']:
            return '🟢 Aman'
        elif row['Sisa_Bulan'] < 1:
            return '🔴 Urgent'
        elif row['Sisa_Bulan'] < 2:
            return '🟠 Warning'
        else:
            return '🟡 Perlu Order'

    prev['Status'] = prev.apply(get_status, axis=1)
    prev = prev[prev['Keb_Aktual'] > 0]
    if sel_status:
        prev = prev[prev['Status'].isin(sel_status)]

    # 1. Sisa Stok
    st.subheader("⏳ Sisa Stok Preventive dalam Bulan")
    sp = prev.pivot_table(index=['Kode Material', 'Nama Material'], columns='PLTD', values='Sisa_Bulan', aggfunc='first', fill_value=0.0)
    sp = sp.reset_index()
    pltd_cols_s = [c for c in sp.columns if c not in ('Kode Material', 'Nama Material')]
    sp = sp[['Kode Material', 'Nama Material'] + pltd_cols_s]
    cfg_s = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
    for col in pltd_cols_s:
        cfg_s[col] = st.column_config.NumberColumn(format="%.1f")

    def hl(val):
        if isinstance(val, (int, float)) and val <= 1.5:
            return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
        return ''

    st.dataframe(sp.style.map(hl, subset=pltd_cols_s), column_config=cfg_s, use_container_width=True, hide_index=True)
    st.markdown("---")

    # 2. Kebutuhan PM
    st.subheader("📋 Kebutuhan Per Bulan Sesuai PM")
    pm_pivot = prev.pivot_table(index=['Kode Material', 'Nama Material'], columns='PLTD', values='Keb_PM', aggfunc='first', fill_value=0)
    pm_pivot = pm_pivot.round(0).astype(int).reset_index()
    pm_pivot = pm_pivot[['Kode Material', 'Nama Material'] + pltd_cols_s]
    cfg_pm = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
    st.dataframe(pm_pivot, column_config=cfg_pm, use_container_width=True, hide_index=True)
    st.markdown("---")

    # 3. Kebutuhan CF Aktual
    st.subheader("📋 Kebutuhan Per Bulan Sesuai CF Aktual")
    cf_pivot = prev.pivot_table(index=['Kode Material', 'Nama Material'], columns='PLTD', values='Keb_Aktual', aggfunc='first', fill_value=0)
    cf_pivot = cf_pivot.round(0).astype(int).reset_index()
    cf_pivot = cf_pivot[['Kode Material', 'Nama Material'] + pltd_cols_s]
    cfg_cf = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
    st.dataframe(cf_pivot, column_config=cfg_cf, use_container_width=True, hide_index=True)
    st.markdown("---")

    # 4. Detail Propose
    st.subheader(f"📋 Detail Propose Order per Material ({jumlah_bulan} Bulan)")
    prev_display = prev.rename(columns={'Keb_N_Bulan': f'Keb_{jumlah_bulan}_Bulan', 'Propose_N_Bulan': f'Propose_{jumlah_bulan}_Bulan'})
    cols_show = ['PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Keb_Aktual', 'Sisa_Bulan', f'Keb_{jumlah_bulan}_Bulan', f'Propose_{jumlah_bulan}_Bulan', 'Status']
    cols_show = [c for c in cols_show if c in prev_display.columns]
    status_order = {'🔴 Urgent': 0, '🟠 Warning': 1, '🟡 Perlu Order': 2, '🟢 Aman': 3}
    prev_display['Status_Sort'] = prev_display['Status'].map(status_order)
    prev_display = prev_display.sort_values(['Status_Sort', 'PLTD'])
    st.dataframe(prev_display[cols_show], use_container_width=True, hide_index=True, height=400)
    st.markdown("---")

    # 5. Rekomendasi
    st.subheader("📝 Rekomendasi Order")
    urgent_df = prev[prev['Status'] == '🔴 Urgent']
    warning_df = prev[prev['Status'] == '🟠 Warning']
    if not urgent_df.empty:
        total_urgent = urgent_df['Propose_N_Bulan'].sum()
        st.error(f"🔴 **URGENT:** {len(urgent_df)} material perlu segera order! Total: **{total_urgent:,.0f} unit**")
        rek = urgent_df[['PLTD', 'Nama Material', 'Qty', 'Keb_Aktual', 'Propose_N_Bulan']].copy()
        rek.columns = ['PLTD', 'Material', 'Stok', 'Keb/Bulan', f'Usulan Order ({jumlah_bulan} bln)']
        st.dataframe(rek, use_container_width=True, hide_index=True)
    if not warning_df.empty:
        total_warning = warning_df['Propose_N_Bulan'].sum()
        st.warning(f"🟠 **WARNING:** {len(warning_df)} material perlu order. Total: **{total_warning:,.0f} unit**")
        rek = warning_df[['PLTD', 'Nama Material', 'Qty', 'Keb_Aktual', 'Propose_N_Bulan']].copy()
        rek.columns = ['PLTD', 'Material', 'Stok', 'Keb/Bulan', f'Usulan Order ({jumlah_bulan} bln)']
        st.dataframe(rek, use_container_width=True, hide_index=True)
    total_all = urgent_df['Propose_N_Bulan'].sum() + warning_df['Propose_N_Bulan'].sum()
    st.info(f"📦 **Total usulan order (urgent + warning): {total_all:,.0f} unit**")

# ==================== PAGE TRANSAKSI ====================
def page_transaksi():
    st.title("📊 Transaksi Project")
    st.info("Segera hadir.")

# ==================== NAVIGASI ====================
home_pg = st.Page(home, title="Beranda", icon="🏠", default=True)
stock_pg = st.Page(page_stock, title="Stok PLTD", icon="📦")
anal_pg = st.Page(page_analisis, title="Analisis Stok", icon="📊")
propose_pg = st.Page(page_propose, title="Propose Order", icon="📦")
trans_pg = st.Page(page_transaksi, title="Transaksi Project", icon="🚚")

pg = st.navigation([home_pg, stock_pg, anal_pg, propose_pg, trans_pg])
pg.run()
