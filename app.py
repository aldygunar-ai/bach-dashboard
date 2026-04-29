import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound, APIError
import requests
import io
import re
import time

# ======================== PAGE CONFIG ========================
st.set_page_config(page_title="Dashboard PLTD Bach", page_icon="⚡", layout="wide")

# ======================== STYLING ========================
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] label p { color: #FFFFFF !important; font-weight: 500 !important; }
    [data-testid="stSidebarNav"] span { color: #FFFFFF !important; }
    [data-testid="stSidebarNav"] a { color: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0A2540; }
    .stPlotlyChart { background: white; border-radius: 10px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    [data-testid="stDataFrame"] { background: white; border-radius: 10px; padding: 8px; }
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
MASTER_D365_ID = '1C7r0AUC3taKIMR1CVmIle5gm333F4r2VPo7lWeqeH8A'
DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"

# ======================== PREVENTIVE EXACT ========================
PREVENTIVE_MAP = {
    ('Oil Filter', 'LF3325'),
    ('Oil Filter By pass', 'LF777'),
    ('Element Water Separator', '2020PM V30-C'),
    ('Fuel Filter', 'FS1006'),
    ('Water Filter', 'WF2076'),
    ('Cylinder head cover gasket', '3629140'),
    ('Air Filter Element', 'AF872'),
    ('Air Filter Element', 'AF25278'),
    ('Air Filter Element (Free)', 'AF25278'),
    ('Air Filter Element (Aksa)', 'AHO1135'),
    ('V-BELT Fan Radiator', '5413003'),
    ('V-BELT (Aksa)', '3015257'),
    ('V-BELT Alternator', '5412990'),
    ('V-BELT Alternator', '5PK889 / 21-3107 / 25471145'),
    ('V-BELT Fan Radiator', '23PK2032 / 21-3110 / 25477108'),
    ('Oli Shell (Drum)', 'Rimula R4 X 15W-40'),
    ('Oli Shell (IBC)', 'Rimula R4 X 15W-40'),
}

def is_preventive_exact(nama, kode):
    """Exact match nama+kode, atau partial match kode setelah split '/'."""
    kode_norm = str(kode).strip().lower() if kode else ''
    nama_norm = str(nama).strip().lower() if nama else ''

    # Cek pasangan (nama, kode)
    for pn, pk in PREVENTIVE_MAP:
        pn_n = pn.strip().lower()
        pk_n = pk.strip().lower()
        if nama_norm == pn_n or kode_norm == pk_n:
            return True

    # Split kode multi-varian
    for part in re.split(r'\s*/\s*', kode_norm):
        part = part.strip()
        for _, pk in PREVENTIVE_MAP:
            if part == pk.strip().lower():
                return True

    # Jika kode mengandung salah satu kode preventive
    for _, pk in PREVENTIVE_MAP:
        pk_n = pk.strip().lower()
        if len(pk_n) >= 3 and pk_n in kode_norm:
            return True

    # Jika nama persis
    for pn, _ in PREVENTIVE_MAP:
        if nama_norm == pn.strip().lower():
            return True

    return False

def is_valid_material(kode, nama):
    if not nama or not nama.strip(): return False
    if re.match(r'^\d+(\.\d+)?$', nama.strip()): return False
    return True

# ======================== GSPREAD ========================
@st.cache_resource
def get_gspread_client():
    creds = dict(st.secrets["gcp_service_account"])
    pk = creds.get('private_key', '')
    if pk:
        creds['private_key'] = pk.replace('\\n', '\n')
    return gspread.service_account_from_dict(creds)

def retry_gspread(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if '429' in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

# ======================== LOAD ALL ========================
@st.cache_data(ttl=1800)
def load_all_data():
    client = get_gspread_client()
    result = {'stock': pd.DataFrame(), 'master1': None, 'master2': None, 'cikande': pd.DataFrame(), 'delivery': pd.DataFrame()}

    # 1. Stok PLTD
    rows = []
    for pltd, sid in PLTD_SHEETS.items():
        try:
            sh = retry_gspread(client.open_by_key, sid)
            data = sh.sheet1.get_all_values()
            if len(data) < 2: continue
            for r in data[1:]:
                if len(r) < 9: continue
                nama = r[2].strip() if len(r) > 2 else ''
                kode = r[3].strip() if len(r) > 3 else ''
                qty_s = r[8].strip() if len(r) > 8 else '0'
                if not is_valid_material(kode, nama): continue
                qty = float(qty_s.replace(',', '')) if qty_s else 0.0
                rows.append((pltd, kode, nama, qty))
        except: pass
    df = pd.DataFrame(rows, columns=['PLTD', 'Kode Material', 'Nama Material', 'Qty'])
    if not df.empty:
        df['Jenis'] = df.apply(lambda r: 'Preventive' if is_preventive_exact(r['Nama Material'], r['Kode Material']) else 'Corrective', axis=1)
        df = df.groupby(['PLTD', 'Kode Material', 'Nama Material', 'Jenis'], as_index=False)['Qty'].sum()
    result['stock'] = df

    # 2. Master Data
    try:
        sh = retry_gspread(client.open_by_key, MASTER_PLTD_ID)
        # Master 1 (strip nama sheet)
        for ws in sh.worksheets():
            if 'master data 1' in ws.title.strip().lower():
                try:
                    df1 = get_as_dataframe(ws, evaluate_formulas=True)
                    df1.columns = [str(c).strip() for c in df1.columns]
                    rename1 = {
                        'Nama Material':'nama_material','Kode Material':'kode_material',
                        'Nama PLTD':'pltd','Harga D365':'harga',
                        'Kebutuhan Perbulan Sesuai CF PM':'keb_pm',
                        'Kebutuhan Perbulan Sesuai Aktual FC':'keb_aktual'
                    }
                    df1.rename(columns={k:v for k,v in rename1.items() if k in df1.columns}, inplace=True)
                    result['master1'] = df1
                except: pass
                break
        # Master 2
        for ws in sh.worksheets():
            if 'master data 2' in ws.title.strip().lower():
                try:
                    df2 = get_as_dataframe(ws, evaluate_formulas=True)
                    df2.columns = [str(c).strip() for c in df2.columns]
                    rename2 = {
                        'Nama PLTD': 'pltd',
                        'Durasi Kirim Darat+Laut (Hari)': 'durasi_kirim'
                    }
                    df2.rename(columns={k:v for k,v in rename2.items() if k in df2.columns}, inplace=True)
                    if 'pltd' not in df2.columns:
                        for c in df2.columns:
                            if 'pltd' in c.lower(): df2.rename(columns={c:'pltd'}, inplace=True); break
                    if 'durasi_kirim' not in df2.columns:
                        for c in df2.columns:
                            if 'durasi' in c.lower() and ('darat' in c.lower() or 'kirim' in c.lower()):
                                df2.rename(columns={c:'durasi_kirim'}, inplace=True)
                                break
                    if 'durasi_kirim' in df2.columns:
                        df2['durasi_kirim'] = pd.to_numeric(df2['durasi_kirim'], errors='coerce').fillna(14)
                    else:
                        df2['durasi_kirim'] = 14
                    result['master2'] = df2
                except: pass
                break
    except Exception as e:
        st.warning(f"Master sheet error: {e}")

    # 3. Cikande
    try:
        sh = retry_gspread(client.open_by_key, MASTER_D365_ID)
        ws = sh.worksheet('Sheet1')
        data = ws.get_all_values()
        # Cari header dengan keyword 'nama', 'matrial', 'cikande'
        header_row = -1
        for i, row in enumerate(data[:5]):
            row_lower = ' '.join([str(c).strip().lower() for c in row])
            if 'nama' in row_lower and ('cikande' in row_lower or 'kode' in row_lower):
                header_row = i
                break
        if header_row < 0: header_row = 0
        header = [str(c).strip().lower() for c in data[header_row]]
        idx_nama = next((i for i, h in enumerate(header) if 'nama' in h or 'material' in h), 0)
        idx_kode = next((i for i, h in enumerate(header) if 'kode' in h or 'seri' in h), 1)
        idx_qty = next((i for i, h in enumerate(header) if 'cikande' in h), 2)
        cik_rows = []
        for r in data[header_row+1:]:
            if len(r) <= max(idx_nama, idx_kode, idx_qty): continue
            nama = r[idx_nama].strip() if idx_nama < len(r) else ''
            kode = r[idx_kode].strip() if idx_kode < len(r) else ''
            qty_s = r[idx_qty].strip() if idx_qty < len(r) else '0'
            try:
                qty = float(qty_s.replace(',', '')) if qty_s else 0.0
            except:
                qty = 0.0
            if nama or kode:
                cik_rows.append({'Kode Material': kode, 'Nama Material': nama, 'Qty Cikande': qty})
        df_cik = pd.DataFrame(cik_rows)
        if not df_cik.empty:
            df_cik = df_cik.groupby(['Kode Material', 'Nama Material'], as_index=False)['Qty Cikande'].sum()
        result['cikande'] = df_cik
    except: pass

    # 4. Delivery
    try:
        resp = requests.get(DELIVERY_URL, headers={'User-Agent':'Mozilla/5.0'}, timeout=20)
        result['delivery'] = pd.read_excel(io.BytesIO(resp.content))
    except: pass

    return result

# ======================== PAGE: HOME ========================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    data = load_all_data()
    df = data['stock']
    if df.empty: st.warning("Data belum tersedia."); return
    c1,c2,c3 = st.columns(3)
    c1.metric("PLTD", df['PLTD'].nunique())
    c2.metric("Total Stok", f"{df['Qty'].sum():,.0f}")
    prev = (df['Jenis']=='Preventive').sum()
    corr = (df['Jenis']=='Corrective').sum()
    c3.metric("Preventive / Corrective", f"{prev} / {corr}")
    pltd_coords = {
        'Pemaron':(-8.16,114.68),'Mangoli':(-1.88,125.37),'Tayan':(-0.03,110.10),
        'Timika':(-4.56,136.89),'Bobong':(-1.95,124.39),'Merawang':(-1.95,105.96),
        'Air Anyir':(-1.94,106.11),'Padang Manggar':(-2.14,106.14),'Krueng Raya':(5.60,95.53),
        'Lueng Bata':(5.55,95.33),'Ulee Kareng':(5.55,95.33),'Waena':(-2.61,140.56),
        'Sambelia':(-8.40,116.67),'Timika 2':(-4.56,136.89),'Wamena':(-4.09,138.94)
    }
    loc = df[['PLTD']].drop_duplicates()
    loc['lat'] = loc['PLTD'].map(lambda x: pltd_coords.get(x, (None,None))[0])
    loc['lon'] = loc['PLTD'].map(lambda x: pltd_coords.get(x, (None,None))[1])
    st.map(loc.dropna(subset=['lat']), latitude='lat', longitude='lon', zoom=4, height=350)

# ======================== PAGE: STOK PLTD ========================
def page_stock():
    st.title("📦 Stok Material PLTD")
    data = load_all_data()
    df = data['stock']
    if df.empty: st.warning("Data belum tersedia."); return

    df_cik = data['cikande']
    if not df_cik.empty:
        df = df.merge(df_cik, on=['Kode Material','Nama Material'], how='left')
        df['Qty Cikande'] = df['Qty Cikande'].fillna(0)
    else:
        df['Qty Cikande'] = 0.0

    st.sidebar.header("Filter Stok")
    pltd_opts = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opts, default=[])
    jenis_opts = ['Preventive','Corrective']
    sel_jenis = st.sidebar.multiselect("Jenis Material", jenis_opts, default=[])
    nama_opts = sorted(df['Nama Material'].unique())
    sel_nama = st.sidebar.multiselect("Nama Material", nama_opts, default=[])
    kode_opts = sorted(df['Kode Material'].unique())
    sel_kode = st.sidebar.multiselect("Kode Material", kode_opts, default=[])

    f = df.copy()
    if sel_pltd: f = f[f['PLTD'].isin(sel_pltd)]
    if sel_jenis: f = f[f['Jenis'].isin(sel_jenis)]
    if sel_nama: f = f[f['Nama Material'].isin(sel_nama)]
    if sel_kode: f = f[f['Kode Material'].isin(sel_kode)]

    prev = f[f['Jenis']=='Preventive']
    corr = f[f['Jenis']=='Corrective']

    def tampil_pivot(data, judul, ikon):
        if data.empty:
            st.info(f"Tidak ada data {judul}.")
            return
        st.subheader(f"{ikon} Material {judul}")
        p = data.pivot_table(index=['Kode Material','Nama Material'], columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
        cik = data.groupby(['Kode Material','Nama Material'])['Qty Cikande'].max()
        p = p.join(cik)
        p['Total'] = p.drop(columns='Qty Cikande').sum(axis=1)
        p = p.reset_index()
        pltd_cols = [c for c in p.columns if c not in ('Kode Material','Nama Material','Qty Cikande','Total')]
        p = p[['Kode Material','Nama Material'] + pltd_cols + ['Qty Cikande','Total']]
        cfg = {'Kode Material': st.column_config.TextColumn(pinned=True),
               'Nama Material': st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)

    tampil_pivot(prev, "Preventive", "🔵")
    tampil_pivot(corr, "Corrective", "🟠")

    # ==================== SISA STOK PREVENTIVE ====================
    st.markdown("---")
    st.subheader("⏳ Sisa Stok Preventive dalam Bulan")
    master1 = data['master1']
    master2 = data['master2']

    if master1 is not None and 'pltd' in master1.columns and 'kode_material' in master1.columns:
        anal = prev.merge(master1[['pltd','kode_material','keb_aktual']],
                          left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        anal.drop(columns=['pltd','kode_material'], inplace=True, errors='ignore')
    else:
        anal = prev.copy()
        anal['keb_aktual'] = np.nan

    if master2 is not None and 'pltd' in master2.columns and 'durasi_kirim' in master2.columns:
        anal = anal.merge(master2[['pltd','durasi_kirim']], on='PLTD', how='left')
    else:
        anal['durasi_kirim'] = 14
    anal['durasi_kirim'] = anal['durasi_kirim'].fillna(14)

    anal['Sisa Bulan'] = np.where(
        anal['keb_aktual'].notna() & (anal['keb_aktual']>0),
        np.round(anal['Qty'] / anal['keb_aktual'], 1), np.nan)
    anal['Status'] = np.where(
        anal['Sisa Bulan'].isna(), '⚪ Data tdk tersedia',
        np.where(anal['Sisa Bulan']*30.5 < anal['durasi_kirim'], '🔴 Critical',
                 np.where(anal['Sisa Bulan']*30.5 < 1.5*anal['durasi_kirim'], '🟡 Warning', '🟢 Aman')))

    cols = ['PLTD','Kode Material','Nama Material','Qty','keb_aktual','Sisa Bulan','durasi_kirim','Status']
    st.dataframe(anal[cols],
                 column_config={'keb_aktual':'Keb. Aktual','Sisa Bulan':st.column_config.NumberColumn(format="%.1f Bulan"),
                                'durasi_kirim':'Durasi Kirim (hari)'},
                 use_container_width=True, hide_index=True)
    st.bar_chart(anal['Status'].value_counts())

def page_analisis(): st.title("📊 Analisis Lanjutan"); st.info("Segera hadir.")
def page_pemakaian(): st.title("🔥 Pemakaian Material"); st.info("Segera hadir.")
def page_transaksi(): st.title("📊 Transaksi Project"); st.info("Segera hadir.")

# ======================== NAVIGASI ========================
home_pg = st.Page(home, title="Beranda", icon="🏠", default=True)
stock_pg = st.Page(page_stock, title="Stok PLTD", icon="📦")
anal_pg = st.Page(page_analisis, title="Analisis Stok", icon="📊")
pakai_pg = st.Page(page_pemakaian, title="Pemakaian", icon="🔥")
trans_pg = st.Page(page_transaksi, title="Transaksi Project", icon="🚚")

pg = st.navigation([home_pg, stock_pg, anal_pg, pakai_pg, trans_pg])
pg.run()
