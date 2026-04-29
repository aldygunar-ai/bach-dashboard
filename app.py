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
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

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
MASTER_GABUNGAN_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'

PREVENTIVE_MAP = {
    'LF3325': 'Oil Filter', 'LF777': 'Oil Filter By pass',
    '2020PM V30-C': 'Element Water Separator', 'FS1006': 'Fuel Filter',
    'WF2076': 'Water Filter', '3629140': 'Cylinder head cover gasket',
    'AF872': 'Air Filter Element', 'AF25278': 'Air Filter Element',
    'AHO1135': 'Air Filter Element (Aksa)', '5413003': 'V-BELT Fan Radiator',
    '3015257': 'V-BELT (Aksa)', '5412990': 'V-BELT Alternator',
    'RIMULA R4 X 15W-40': 'Oli Shell', 'WCL': 'Coolant',
}

NORMALIZE_NAME = {
    'AF25278': 'Air Filter Element', 'AF872': 'Air Filter Element',
    'RIMULA R4 X 15W-40': 'Oli Shell', 'WCL': 'Coolant',
    'ACC-Y': 'ACCU 12V N150 YUASA',
}

def norm(kode, nama):
    k = str(kode).strip().upper()
    if k in NORMALIZE_NAME: return NORMALIZE_NAME[k]
    for pk, pn in PREVENTIVE_MAP.items():
        if k == pk.upper(): return pn
    return nama

def is_prev(kode):
    k = str(kode).strip().upper()
    for pk in PREVENTIVE_MAP:
        if k == pk.upper(): return True
        for p in re.split(r'\s*/\s*', k):
            if p == pk.upper(): return True
    return False

def is_valid(kode, nama):
    if not nama or not nama.strip(): return False
    if re.match(r'^\d+(\.\d+)?$', nama.strip()): return False
    return True

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'): c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

@st.cache_data(ttl=600)
def load_all():
    cl = get_client()
    res = {'stock':pd.DataFrame(),'m1':None,'m2':None,'cik':pd.DataFrame(),'pemakaian':pd.DataFrame()}

    # STOK PLTD
    rows = []
    for pltd, sid in PLTD_SHEETS.items():
        try:
            sh = cl.open_by_key(sid)
            data = sh.sheet1.get_all_values()
            if len(data)<2: continue
            for r in data[1:]:
                if len(r)<9: continue
                nama = r[2].strip() if len(r)>2 else ''
                kode = r[3].strip() if len(r)>3 else ''
                qty_s = r[8].strip() if len(r)>8 else '0'
                if not is_valid(kode,nama): continue
                qty = float(qty_s.replace(',','')) if qty_s else 0.0
                rows.append((pltd.strip().upper(), kode.upper().strip(), norm(kode,nama).strip(), qty))
        except: pass
    df = pd.DataFrame(rows, columns=['PLTD','Kode Material','Nama Material','Qty'])
    if not df.empty:
        df['Jenis'] = df['Kode Material'].apply(lambda k: 'Preventive' if is_prev(k) else 'Corrective')
        df = df.groupby(['PLTD','Kode Material','Nama Material','Jenis'], as_index=False)['Qty'].sum()
    res['stock'] = df

    # MASTER DATA
    try:
        sh = cl.open_by_key(MASTER_PLTD_ID)
        for ws in sh.worksheets():
            t = ws.title.strip().lower()
            if ('master' in t or 'mater' in t) and '1' in t:
                try:
                    d = get_as_dataframe(ws, evaluate_formulas=True)
                    d.columns = [str(c).strip() for c in d.columns]
                    pltd_col = next((c for c in d.columns if 'pltd' in c.lower()), None)
                    kode_col = next((c for c in d.columns if 'kode' in c.lower()), None)
                    aktual_col = next((c for c in d.columns if 'aktual' in c.lower()), None)
                    if pltd_col: d.rename(columns={pltd_col:'pltd'}, inplace=True)
                    if kode_col: d.rename(columns={kode_col:'kode_material'}, inplace=True)
                    if aktual_col: d.rename(columns={aktual_col:'keb_aktual'}, inplace=True)
                    for col in ['pltd','kode_material']:
                        if col in d.columns: d[col] = d[col].astype(str).str.strip().str.upper()
                    if 'keb_aktual' in d.columns:
                        d['keb_aktual'] = pd.to_numeric(d['keb_aktual'], errors='coerce').fillna(0)
                    res['m1'] = d
                except: pass
            if ('master' in t or 'mater' in t) and '2' in t:
                try:
                    d = get_as_dataframe(ws, evaluate_formulas=True)
                    d.columns = [str(c).strip() for c in d.columns]
                    pltd_col = next((c for c in d.columns if 'pltd' in c.lower()), None)
                    dur_col = next((c for c in d.columns if 'durasi' in c.lower()), None)
                    if pltd_col: d.rename(columns={pltd_col:'pltd'}, inplace=True)
                    if dur_col: d.rename(columns={dur_col:'durasi_kirim'}, inplace=True)
                    if 'pltd' in d.columns: d['pltd'] = d['pltd'].astype(str).str.strip().str.upper()
                    if 'durasi_kirim' in d.columns: d['durasi_kirim'] = pd.to_numeric(d['durasi_kirim'], errors='coerce').fillna(14)
                    else: d['durasi_kirim'] = 14
                    res['m2'] = d
                except: pass
    except: pass

    # CIKANDE
    try:
        sh = cl.open_by_key(MASTER_D365_ID)
        ws = sh.worksheet('Sheet1')
        data = ws.get_all_values()
        hrow = 0
        for i, row in enumerate(data[:5]):
            if 'cikande' in ' '.join([str(c).lower() for c in row]):
                hrow = i; break
        header = [str(c).strip().lower() for c in data[hrow]]
        i_nama = next((i for i,h in enumerate(header) if 'nama' in h or 'material' in h or 'matrial' in h), 0)
        i_kode = next((i for i,h in enumerate(header) if 'kode' in h or 'seri' in h), 1)
        i_qty  = next((i for i,h in enumerate(header) if 'cikande' in h), 2)
        crows = []
        for r in data[hrow+1:]:
            if len(r) <= max(i_nama,i_kode,i_qty): continue
            nama = r[i_nama].strip() if i_nama<len(r) else ''
            kode = r[i_kode].strip() if i_kode<len(r) else ''
            qty_s = r[i_qty].strip() if i_qty<len(r) else '0'
            try: qty = float(qty_s.replace(',','')) if qty_s else 0.0
            except: qty = 0.0
            if nama or kode:
                crows.append({'Kode Material':kode.upper().strip(),'Nama Material':norm(kode,nama).strip(),'WH Cikande':qty})
        dc = pd.DataFrame(crows)
        if not dc.empty: dc = dc.groupby(['Kode Material','Nama Material'], as_index=False)['WH Cikande'].sum()
        res['cik'] = dc
    except: pass

    # PEMAKAIAN (SHEET GABUNGAN)
    try:
        sh = cl.open_by_key(MASTER_GABUNGAN_ID)
        ws = sh.worksheet('Gabungan')
        data = ws.get_all_values()
        if len(data) >= 4:
            p_rows = []
            for r in data[3:]:
                if len(r) < 2: continue
                tanggal = r[0].strip() if len(r) > 0 else ''
                masuk = r[1].strip() if len(r) > 1 else '0'
                keluar = r[2].strip() if len(r) > 2 else '0'
                stok = r[3].strip() if len(r) > 3 else '0'
                keterangan = r[4].strip() if len(r) > 4 else ''
                hour_meter = r[5].strip() if len(r) > 5 else ''
                week = r[6].strip() if len(r) > 6 else ''
                transaksi = r[7].strip() if len(r) > 7 else ''
                nama_material = r[8].strip() if len(r) > 8 else ''
                jobtype = r[9].strip() if len(r) > 9 else ''
                product_id = r[10].strip() if len(r) > 10 else ''
                gudang = r[11].strip() if len(r) > 11 else ''
                convert_tgl = r[12].strip() if len(r) > 12 else ''
                periode = r[13].strip() if len(r) > 13 else ''
                harga = r[14].strip() if len(r) > 14 else '0'
                total = r[15].strip() if len(r) > 15 else '0'
                
                if nama_material:
                    try: m = float(masuk.replace(',','')) if masuk else 0.0
                    except: m = 0.0
                    try: k = float(keluar.replace(',','')) if keluar else 0.0
                    except: k = 0.0
                    try: s = float(stok.replace(',','')) if stok else 0.0
                    except: s = 0.0
                    try: t = float(total.replace(',','')) if total else 0.0
                    except: t = 0.0
                    
                    p_rows.append({
                        'Tanggal': tanggal, 'Nama Material': nama_material,
                        'Masuk': m, 'Keluar': k, 'Stok': s,
                        'Gudang': gudang, 'Keterangan': keterangan,
                        'Transaksi': transaksi, 'JobType': jobtype, 'TOTAL': t,
                    })
            df_p = pd.DataFrame(p_rows)
            if not df_p.empty:
                df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'], errors='coerce')
            res['pemakaian'] = df_p
    except Exception as e:
        st.warning(f"Gagal baca Gabungan: {e}")

    return res

# ======================== HOME ========================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    data = load_all()
    df = data.get('stock', pd.DataFrame())
    if df.empty: st.warning("Data belum tersedia."); return
    c1,c2,c3 = st.columns(3)
    c1.metric("PLTD", df['PLTD'].nunique())
    c2.metric("Total Stok", f"{df['Qty'].sum():,.0f}")
    c3.metric("Prev / Corr", f"{(df['Jenis']=='Preventive').sum()} / {(df['Jenis']=='Corrective').sum()}")
    coords = {
        'PEMARON':(-8.16,114.68),'MANGOLI':(-1.88,125.37),'TAYAN':(-0.03,110.10),
        'TIMIKA':(-4.56,136.89),'BOBONG':(-1.95,124.39),'MERAWANG':(-1.95,105.96),
        'AIR ANYIR':(-1.94,106.11),'PADANG MANGGAR':(-2.14,106.14),'KRUENG RAYA':(5.60,95.53),
        'LUENG BATA':(5.55,95.33),'ULEE KARENG':(5.55,95.33),'WAENA':(-2.61,140.56),
        'SAMBELIA':(-8.40,116.67),'TIMIKA 2':(-4.56,136.89),'WAMENA':(-4.09,138.94)
    }
    loc = df[['PLTD']].drop_duplicates()
    loc['lat'] = loc['PLTD'].map(lambda x: coords.get(x,(None,None))[0])
    loc['lon'] = loc['PLTD'].map(lambda x: coords.get(x,(None,None))[1])
    st.map(loc.dropna(subset=['lat']), latitude='lat', longitude='lon', zoom=4, height=350)

# ======================== STOCK ========================
def page_stock():
    st.title("📦 Stok Material PLTD")
    data = load_all()
    df = data['stock'].copy()
    if df.empty: st.warning("Data belum tersedia."); return

    cik = data['cik']
    if not cik.empty:
        df = df.merge(cik, on=['Kode Material','Nama Material'], how='left')
        df['WH Cikande'] = df['WH Cikande'].fillna(0)
    else:
        df['WH Cikande'] = 0.0

    st.sidebar.header("Filter Stok")
    sel_pltd = st.sidebar.multiselect("PLTD", sorted(df['PLTD'].unique()), default=[])
    sel_jenis = st.sidebar.multiselect("Jenis Material", ['Preventive','Corrective'], default=[])
    sel_nama = st.sidebar.multiselect("Nama Material", sorted(df['Nama Material'].unique()), default=[])
    sel_kode = st.sidebar.multiselect("Kode Material", sorted(df['Kode Material'].unique()), default=[])
    highlight_only = st.sidebar.checkbox("🔴 Highlight hanya yang kritis (≤1.5 bulan)", value=False)

    f = df.copy()
    if sel_pltd: f = f[f['PLTD'].isin(sel_pltd)]
    if sel_jenis: f = f[f['Jenis'].isin(sel_jenis)]
    if sel_nama: f = f[f['Nama Material'].isin(sel_nama)]
    if sel_kode: f = f[f['Kode Material'].isin(sel_kode)]

    prev = f[f['Jenis']=='Preventive'].copy()
    corr = f[f['Jenis']=='Corrective'].copy()

    m1 = data['m1']

    st.subheader("🔵 Material Preventive")
    if not prev.empty:
        p = prev.pivot_table(index=['Kode Material','Nama Material'], columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
        p = p.round(0).astype(int)
        cik_p = prev.groupby(['Kode Material','Nama Material'])['WH Cikande'].max().round(0).astype(int)
        p = p.join(cik_p)
        p['Total'] = p.drop(columns='WH Cikande').sum(axis=1)
        p = p.reset_index()
        pltd_cols = [c for c in p.columns if c not in ('Kode Material','Nama Material','WH Cikande','Total')]
        p = p[['Kode Material','Nama Material'] + pltd_cols + ['WH Cikande','Total']]
        cfg = {'Kode Material':st.column_config.TextColumn(pinned=True), 'Nama Material':st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Preventive.")

    st.subheader("⏳ Sisa Stok Preventive dalam Bulan")
    if not prev.empty and m1 is not None and 'pltd' in m1.columns and 'kode_material' in m1.columns and 'keb_aktual' in m1.columns:
        p1 = m1[['pltd','kode_material','keb_aktual']].copy()
        p1['pltd'] = p1['pltd'].str.strip().str.upper()
        p1['kode_material'] = p1['kode_material'].str.strip().str.upper()
        sisa = prev.merge(p1, left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        sisa.drop(columns=['pltd','kode_material'], inplace=True, errors='ignore')
        sisa['Sisa Bulan'] = np.where(sisa['keb_aktual'].notna() & (sisa['keb_aktual']>0), np.floor(sisa['Qty']/sisa['keb_aktual']*10)/10, 0.0)
        sp = sisa.pivot_table(index=['Kode Material','Nama Material'], columns='PLTD', values='Sisa Bulan', aggfunc='first', fill_value=0.0)
        sp = sp.reset_index()
        pltd_cols_s = [c for c in sp.columns if c not in ('Kode Material','Nama Material')]
        sp = sp[['Kode Material','Nama Material'] + pltd_cols_s]
        if highlight_only:
            mask = (sp[pltd_cols_s] > 0) & (sp[pltd_cols_s] <= 1.5)
            sp = sp[mask.any(axis=1)]
        cfg_s = {'Kode Material': st.column_config.TextColumn(pinned=True), 'Nama Material': st.column_config.TextColumn(pinned=True)}
        for col in pltd_cols_s: cfg_s[col] = st.column_config.NumberColumn(format="%.1f")
        def hl(val):
            if isinstance(val, (int,float)) and 0 < val <= 1.5: return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
            return ''
        styled_sp = sp.style.map(hl, subset=pltd_cols_s)
        st.dataframe(styled_sp, column_config=cfg_s, use_container_width=True, hide_index=True)
    else:
        st.info("Data Sisa Bulan tidak tersedia.")

    st.subheader("🟠 Material Corrective")
    if not corr.empty:
        p = corr.pivot_table(index=['Kode Material','Nama Material'], columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
        p = p.round(0).astype(int)
        cik_c = corr.groupby(['Kode Material','Nama Material'])['WH Cikande'].max().round(0).astype(int)
        p = p.join(cik_c)
        p['Total'] = p.drop(columns='WH Cikande').sum(axis=1)
        p = p.reset_index()
        pltd_cols = [c for c in p.columns if c not in ('Kode Material','Nama Material','WH Cikande','Total')]
        p = p[['Kode Material','Nama Material'] + pltd_cols + ['WH Cikande','Total']]
        cfg = {'Kode Material':st.column_config.TextColumn(pinned=True), 'Nama Material':st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Corrective.")

# ======================== ANALISIS ========================
def page_analisis():
    st.title("📊 Analisis Pemakaian Material")
    data = load_all()
    df_pakai = data.get('pemakaian', pd.DataFrame()).copy()
    df_stock = data.get('stock', pd.DataFrame()).copy()
    m1 = data.get('m1')
    m2 = data.get('m2')
    
    if df_pakai.empty:
        st.warning("Data pemakaian (sheet Gabungan) belum tersedia.")
        return

    # ==== KODE & JENIS ====
    if not df_stock.empty:
        name_to_code = df_stock[['Nama Material','Kode Material']].drop_duplicates()
        name_to_code = name_to_code.groupby('Nama Material')['Kode Material'].apply(lambda x: ', '.join(sorted(set(x)))).reset_index()
        code_map = dict(zip(name_to_code['Nama Material'], name_to_code['Kode Material']))
        df_pakai['Kode Material'] = df_pakai['Nama Material'].map(code_map).fillna('')
        df_pakai['Jenis'] = df_pakai['Kode Material'].apply(lambda k: 'Preventive' if is_prev(k) else ('Corrective' if k else 'Unknown'))
    else:
        df_pakai['Kode Material'] = ''
        df_pakai['Jenis'] = 'Unknown'

    # ==== TANGGAL ====
    if 'Tanggal' in df_pakai.columns:
        df_pakai['Tanggal'] = pd.to_datetime(df_pakai['Tanggal'], errors='coerce')
        df_pakai = df_pakai.dropna(subset=['Tanggal'])
        df_pakai['Tahun'] = df_pakai['Tanggal'].dt.year.astype(int).astype(str)
        bulan_map = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                     7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}
        df_pakai['Periode'] = df_pakai['Tanggal'].dt.month.map(bulan_map)
        df_pakai['BulanStr'] = df_pakai['Tanggal'].dt.to_period('M').astype(str)

    # ==== NUMERIK ====
    for col in ['Masuk','Keluar','Stok','TOTAL']:
        if col in df_pakai.columns:
            df_pakai[col] = pd.to_numeric(df_pakai[col], errors='coerce').fillna(0)

    # ==== FILTER SIDEBAR ====
    st.sidebar.header("Filter Analisis")
    
    nama_opts = sorted(df_pakai['Nama Material'].unique().astype(str))
    sel_nama = st.sidebar.multiselect("Nama Material", nama_opts, default=[])
    
    kode_opts = sorted(df_pakai['Kode Material'].unique().astype(str))
    sel_kode = st.sidebar.multiselect("Kode Material", kode_opts, default=[])
    
    gudang_opts = sorted(df_pakai['Gudang'].unique().astype(str)) if 'Gudang' in df_pakai.columns else []
    sel_gudang = st.sidebar.multiselect("Gudang", gudang_opts, default=[])
    
    jobtype_opts = sorted(df_pakai['JobType'].unique().astype(str)) if 'JobType' in df_pakai.columns else []
    sel_jobtype = st.sidebar.multiselect("JobType", jobtype_opts, default=[])
    
    tahun_opts = sorted(df_pakai['Tahun'].astype(str).unique())
    sel_tahun = st.sidebar.multiselect("Tahun", tahun_opts, default=[])
    
    periode_opts = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
    sel_periode = st.sidebar.multiselect("Periode (Bulan)", periode_opts, default=[])
    
    jenis_opts = sorted(df_pakai['Jenis'].unique().astype(str))
    sel_jenis = st.sidebar.multiselect("Jenis Material", jenis_opts, default=[])

    # ==== FILTER DATA ====
    f = df_pakai.copy()
    if sel_nama: f = f[f['Nama Material'].astype(str).isin(sel_nama)]
    if sel_kode: f = f[f['Kode Material'].astype(str).isin(sel_kode)]
    if sel_gudang: f = f[f['Gudang'].astype(str).isin(sel_gudang)]
    if sel_jobtype: f = f[f['JobType'].astype(str).isin(sel_jobtype)]
    if sel_tahun: f = f[f['Tahun'].astype(str).isin(sel_tahun)]
    if sel_periode: f = f[f['Periode'].astype(str).isin(sel_periode)]
    if sel_jenis: f = f[f['Jenis'].astype(str).isin(sel_jenis)]

    # ==== KPI ====
    st.subheader("📈 Ringkasan Pemakaian")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total Transaksi", len(f))
    k2.metric("Total Keluar", f"{f['Keluar'].sum():,.0f}")
    k3.metric("Total Masuk", f"{f['Masuk'].sum():,.0f}")
    if 'TOTAL' in f.columns:
        k4.metric("Total Cost", f"Rp {f['TOTAL'].sum():,.0f}")
    else:
        k4.metric("Total Cost", "N/A")
    
    st.markdown("---")

    # ==== GRAFIK 1: TOP 10 INBOUND & OUTBOUND (GABUNG) ====
    st.subheader("📥📤 TOP 10 Material: Inbound vs Outbound")
    
    # Top 10 berdasarkan total aktivitas (Masuk + Keluar)
    top_10 = f.groupby('Nama Material').agg(Masuk=('Masuk','sum'), Keluar=('Keluar','sum')).sum(axis=1).nlargest(10).index.tolist()
    top_data = f[f['Nama Material'].isin(top_10)]
    agg = top_data.groupby('Nama Material').agg(Masuk=('Masuk','sum'), Keluar=('Keluar','sum')).reset_index()
    agg = agg.sort_values('Masuk', ascending=True)  # biar horizontal bar terurut
    
    if not agg.empty:
        fig_inout = go.Figure()
        fig_inout.add_trace(go.Bar(y=agg['Nama Material'], x=agg['Masuk'], name='Masuk',
                                   orientation='h', marker=dict(color='#4B8BBE'), text=agg['Masuk'].round(0), textposition='outside'))
        fig_inout.add_trace(go.Bar(y=agg['Nama Material'], x=agg['Keluar'], name='Keluar',
                                   orientation='h', marker=dict(color='#E67E22'), text=agg['Keluar'].round(0), textposition='outside'))
        fig_inout.update_layout(barmode='group', height=400, margin=dict(l=200, r=40, t=30, b=80),
                                legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                                xaxis_title='Quantity')
        st.plotly_chart(fig_inout, use_container_width=True)
    else:
        st.info("Data tidak cukup.")
    
    st.markdown("---")

    # ==== GRAFIK 2: TREN BULANAN ====
    st.subheader("📈 Tren Pemakaian Bulanan")
    if 'BulanStr' in f.columns:
        trend = f.groupby('BulanStr').agg(Masuk=('Masuk','sum'), Keluar=('Keluar','sum')).reset_index()
        if not trend.empty and (trend['Masuk'].sum() > 0 or trend['Keluar'].sum() > 0):
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=trend['BulanStr'], y=trend['Masuk'], mode='lines+markers',
                                           name='Masuk', line=dict(color='#4B8BBE', width=2)))
            fig_trend.add_trace(go.Scatter(x=trend['BulanStr'], y=trend['Keluar'], mode='lines+markers',
                                           name='Keluar', line=dict(color='#E67E22', width=2)))
            fig_trend.update_layout(height=400, xaxis_title='Bulan', yaxis_title='Quantity',
                                    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data tren tidak cukup.")
    else:
        st.info("Data tanggal tidak tersedia.")
    
    st.markdown("---")

    # ==== GRAFIK 3: COST TOP 10 ====
    st.subheader("💰 TOP 10 Cost Material")
    if 'TOTAL' in f.columns and f['TOTAL'].sum() > 0:
        top_cost = f.groupby('Nama Material')['TOTAL'].sum().nlargest(10).reset_index()
        top_cost = top_cost.sort_values('TOTAL', ascending=True)
        fig_cost = go.Figure()
        fig_cost.add_trace(go.Bar(y=top_cost['Nama Material'], x=top_cost['TOTAL'], orientation='h',
                                  marker=dict(color='#27AE60'), text=top_cost['TOTAL'].apply(lambda x: f'Rp {x:,.0f}'),
                                  textposition='outside'))
        fig_cost.update_layout(height=380, margin=dict(l=200, r=80, t=30, b=20), xaxis_title='Total Cost')
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.info("Data TOTAL (kolom P) tidak tersedia.")
    
    st.markdown("---")

    # ==== TABEL DETAIL ====
    st.subheader("📋 Detail Pemakaian Material")
    cols = ['Tanggal','Nama Material','Kode Material','Masuk','Keluar','Stok','Gudang','Keterangan','Transaksi','JobType','Jenis']
    if 'TOTAL' in f.columns:
        f = f.rename(columns={'TOTAL': 'Cost Total'})
        cols.append('Cost Total')
    cols = [c for c in cols if c in f.columns]
    if 'Tanggal' in f.columns:
        f = f.sort_values('Tanggal', ascending=False)
    st.dataframe(f[cols], use_container_width=True, hide_index=True, height=400)
    
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
