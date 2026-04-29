import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound, APIError
import requests
import io
import re
import time

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
        if len(data) >= 4:  # header di baris ke-3 (index 2)
            header = [str(c).strip() for c in data[2]]
            # Mapping kolom
            col_map = {}
            for i, h in enumerate(header):
                hl = h.lower()
                if 'tanggal' in hl and 'convert' not in hl: col_map['tanggal'] = i
                elif 'masuk' in hl: col_map['masuk'] = i
                elif 'keluar' in hl: col_map['keluar'] = i
                elif 'stok' in hl: col_map['stok'] = i
                elif 'keterangan' in hl: col_map['keterangan'] = i
                elif 'hour' in hl: col_map['hour_meter'] = i
                elif 'transaksi' in hl: col_map['transaksi'] = i
                elif 'nama material' in hl: col_map['nama_material'] = i
                elif 'jobtype' in hl or 'job type' in hl: col_map['jobtype'] = i
                elif 'gudang' in hl: col_map['gudang'] = i
                elif 'harga' in hl: col_map['harga'] = i
                elif 'total' in hl: col_map['total'] = i
            
            if 'nama_material' in col_map:
                p_rows = []
                for r in data[3:]:
                    if len(r) >= max(col_map.values())+1:
                        nama = r[col_map.get('nama_material', 0)].strip()
                        tgl = r[col_map.get('tanggal', 0)].strip() if 'tanggal' in col_map else ''
                        masuk = r[col_map.get('masuk', 1)].strip() if 'masuk' in col_map else '0'
                        keluar = r[col_map.get('keluar', 2)].strip() if 'keluar' in col_map else '0'
                        stok = r[col_map.get('stok', 3)].strip() if 'stok' in col_map else '0'
                        gudang = r[col_map.get('gudang', 4)].strip() if 'gudang' in col_map else ''
                        keterangan = r[col_map.get('keterangan', 5)].strip() if 'keterangan' in col_map else ''
                        transaksi = r[col_map.get('transaksi', 6)].strip() if 'transaksi' in col_map else ''
                        jobtype = r[col_map.get('jobtype', 7)].strip() if 'jobtype' in col_map else ''
                        harga = r[col_map.get('harga', 8)].strip() if 'harga' in col_map else '0'
                        total = r[col_map.get('total', 9)].strip() if 'total' in col_map else '0'
                        
                        if nama:
                            p_rows.append({
                                'Tanggal': tgl,
                                'Nama Material': nama,
                                'Masuk': float(masuk.replace(',','')) if masuk else 0.0,
                                'Keluar': float(keluar.replace(',','')) if keluar else 0.0,
                                'Stok': float(stok.replace(',','')) if stok else 0.0,
                                'Gudang': gudang,
                                'Keterangan': keterangan,
                                'Transaksi': transaksi,
                                'JobType': jobtype,
                            })
                df_p = pd.DataFrame(p_rows)
                if not df_p.empty:
                    df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'], errors='coerce')
                res['pemakaian'] = df_p
    except: pass

    return res

# ======================== HOME ========================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    data = load_all()
    df = data['stock']
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

    # ==== 1. TABEL PREVENTIVE (QTY) ====
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
        cfg = {'Kode Material':st.column_config.TextColumn(pinned=True),
               'Nama Material':st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Preventive.")

    # ==== 2. SISA BULAN PREVENTIVE ====
    st.subheader("⏳ Sisa Stok Preventive dalam Bulan")

    if not prev.empty and m1 is not None and 'pltd' in m1.columns and 'kode_material' in m1.columns and 'keb_aktual' in m1.columns:
        p1 = m1[['pltd','kode_material','keb_aktual']].copy()
        p1['pltd'] = p1['pltd'].str.strip().str.upper()
        p1['kode_material'] = p1['kode_material'].str.strip().str.upper()
        
        sisa = prev.merge(p1, left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        sisa.drop(columns=['pltd','kode_material'], inplace=True, errors='ignore')

        sisa['Sisa Bulan'] = np.where(
            sisa['keb_aktual'].notna() & (sisa['keb_aktual'] > 0),
            np.floor(sisa['Qty'] / sisa['keb_aktual'] * 10) / 10,
            0.0
        )

        sp = sisa.pivot_table(
            index=['Kode Material','Nama Material'], 
            columns='PLTD', 
            values='Sisa Bulan', 
            aggfunc='first', 
            fill_value=0.0
        )
        sp = sp.reset_index()
        pltd_cols_s = [c for c in sp.columns if c not in ('Kode Material','Nama Material')]
        sp = sp[['Kode Material','Nama Material'] + pltd_cols_s]

        if highlight_only:
            mask = (sp[pltd_cols_s] > 0) & (sp[pltd_cols_s] <= 1.5)
            sp = sp[mask.any(axis=1)]

        cfg_s = {
            'Kode Material': st.column_config.TextColumn(pinned=True),
            'Nama Material': st.column_config.TextColumn(pinned=True),
        }
        for col in pltd_cols_s:
            cfg_s[col] = st.column_config.NumberColumn(format="%.1f")
        
        def highlight_low(val):
            if isinstance(val, (int, float)) and val > 0 and val <= 1.5:
                return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
            return ''
        
        styled_sp = sp.style.map(highlight_low, subset=pltd_cols_s)
        st.dataframe(styled_sp, column_config=cfg_s, use_container_width=True, hide_index=True)
        
    else:
        st.info("Data Sisa Bulan tidak tersedia (periksa sheet Master data 1).")

    # ==== 3. CORRECTIVE ====
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
        cfg = {'Kode Material':st.column_config.TextColumn(pinned=True),
               'Nama Material':st.column_config.TextColumn(pinned=True)}
        st.dataframe(p, column_config=cfg, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data Corrective.")

# ======================== ANALISIS ========================
def page_analisis():
    st.title("📊 Analisis Pemakaian Material")
    
    data = load_all()
    df_stock = data['stock'].copy()
    df_pakai = data.get('pemakaian', pd.DataFrame()).copy()
    m1 = data.get('m1')
    m2 = data.get('m2')
    
    if df_pakai.empty:
        st.warning("Data pemakaian (sheet Gabungan) belum tersedia atau belum bisa dibaca.")
        return
    
    # ==== DETEKSI KODE MATERIAL ====
    if not df_stock.empty:
        name_to_code = df_stock[['Nama Material', 'Kode Material']].drop_duplicates()
        name_to_code = name_to_code.groupby('Nama Material')['Kode Material'].apply(lambda x: ', '.join(sorted(set(x)))).reset_index()
        code_map = dict(zip(name_to_code['Nama Material'], name_to_code['Kode Material']))
    else:
        code_map = {}
    
    if 'Nama Material' in df_pakai.columns:
        df_pakai['Kode Material'] = df_pakai['Nama Material'].map(code_map).fillna('')
        df_pakai['Jenis'] = df_pakai['Kode Material'].apply(lambda k: 'Preventive' if is_prev(k) else ('Corrective' if k else 'Unknown'))
    
    # ==== KONVERSI TANGGAL ====
    if 'Tanggal' in df_pakai.columns:
        df_pakai['Tanggal'] = pd.to_datetime(df_pakai['Tanggal'], errors='coerce')
        df_pakai = df_pakai.dropna(subset=['Tanggal'])
        df_pakai['Tahun'] = df_pakai['Tanggal'].dt.year.astype(int).astype(str)
        bulan_map = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                     7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}
        df_pakai['Periode'] = df_pakai['Tanggal'].dt.month.map(bulan_map)
    
    # ==== KONVERSI NUMERIK ====
    for col in ['Masuk', 'Keluar', 'Stok']:
        if col in df_pakai.columns:
            df_pakai[col] = pd.to_numeric(df_pakai[col], errors='coerce').fillna(0)
    
    # Kolom TOTAL (kolom P) untuk cost
    if 'TOTAL' in df_pakai.columns:
        df_pakai['TOTAL'] = pd.to_numeric(df_pakai['TOTAL'], errors='coerce').fillna(0)
    
    # ==== SIDEBAR FILTER (KOSONG) ====
    st.sidebar.header("Filter Analisis")
    
    nama_opts = sorted(df_pakai['Nama Material'].unique().astype(str)) if 'Nama Material' in df_pakai.columns else []
    sel_nama = st.sidebar.multiselect("Nama Material", nama_opts, default=[])
    
    kode_opts = sorted(df_pakai['Kode Material'].unique().astype(str)) if 'Kode Material' in df_pakai.columns else []
    sel_kode = st.sidebar.multiselect("Kode Material", kode_opts, default=[])
    
    gudang_opts = sorted(df_pakai['Gudang'].unique().astype(str)) if 'Gudang' in df_pakai.columns else []
    sel_gudang = st.sidebar.multiselect("Gudang", gudang_opts, default=[])
    
    jobtype_opts = sorted(df_pakai['JobType'].unique().astype(str)) if 'JobType' in df_pakai.columns else []
    sel_jobtype = st.sidebar.multiselect("JobType", jobtype_opts, default=[])
    
    tahun_opts = sorted(df_pakai['Tahun'].astype(str).unique()) if 'Tahun' in df_pakai.columns else []
    sel_tahun = st.sidebar.multiselect("Tahun", tahun_opts, default=[])
    
    periode_opts = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
    sel_periode = st.sidebar.multiselect("Periode (Bulan)", periode_opts, default=[])
    
    jenis_opts = sorted(df_pakai['Jenis'].unique().astype(str)) if 'Jenis' in df_pakai.columns else []
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
    
    # ==== KPI RINGKASAN ====
    st.subheader("📈 Ringkasan Pemakaian")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Transaksi", len(f))
    k2.metric("Total Keluar", f"{f['Keluar'].sum():,.0f}" if 'Keluar' in f.columns else "0")
    k3.metric("Total Masuk", f"{f['Masuk'].sum():,.0f}" if 'Masuk' in f.columns else "0")
    k4.metric("Material Unik", f['Nama Material'].nunique() if 'Nama Material' in f.columns else 0)
    if 'TOTAL' in f.columns:
        total_cost = f['TOTAL'].sum()
        k5.metric("Total Cost", f"Rp {total_cost:,.0f}")
    else:
        k5.metric("Total Cost", "N/A")
    
    st.markdown("---")
    
    # ==== GRAFIK 1: INBOUND VS OUTBOUND ====
    if 'Tanggal' in f.columns and not f['Tanggal'].isna().all() and 'Masuk' in f.columns and 'Keluar' in f.columns:
        f['BulanStr'] = f['Tanggal'].dt.to_period('M').astype(str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Inbound (Masuk) per Bulan")
            inbound = f.groupby('BulanStr')['Masuk'].sum().reset_index()
            if not inbound.empty and inbound['Masuk'].sum() > 0:
                fig_in = px.bar(inbound, x='BulanStr', y='Masuk', color='Masuk', color_continuous_scale='Blues')
                fig_in.update_layout(height=350)
                st.plotly_chart(fig_in, use_container_width=True)
            else:
                st.info("Tidak ada data Masuk.")
        
        with col2:
            st.subheader("📤 Outbound (Keluar) per Bulan")
            outbound = f.groupby('BulanStr')['Keluar'].sum().reset_index()
            if not outbound.empty and outbound['Keluar'].sum() > 0:
                fig_out = px.bar(outbound, x='BulanStr', y='Keluar', color='Keluar', color_continuous_scale='Reds')
                fig_out.update_layout(height=350)
                st.plotly_chart(fig_out, use_container_width=True)
            else:
                st.info("Tidak ada data Keluar.")
    
    st.markdown("---")
    
    # ==== GRAFIK 2: TREN PEMAKAIAN BULANAN ====
    if 'Tanggal' in f.columns and not f['Tanggal'].isna().all() and 'Masuk' in f.columns and 'Keluar' in f.columns:
        st.subheader("📈 Tren Pemakaian Bulanan")
        trend = f.groupby('BulanStr').agg({'Masuk':'sum','Keluar':'sum'}).reset_index()
        if not trend.empty and (trend['Masuk'].sum() > 0 or trend['Keluar'].sum() > 0):
            fig_trend = px.line(trend, x='BulanStr', y=['Masuk','Keluar'], markers=True,
                                color_discrete_map={'Masuk':'#4B8BBE','Keluar':'#E67E22'})
            fig_trend.update_layout(height=400, xaxis_title='Bulan', yaxis_title='Quantity')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data tren tidak cukup.")
    
    st.markdown("---")
    
    # ==== GRAFIK 3: COST MATERIAL ANALYSIS ====
    st.subheader("💰 Cost Material Analysis")
    if 'TOTAL' in f.columns and 'Tanggal' in f.columns and not f['Tanggal'].isna().all():
        f['BulanStr'] = f['Tanggal'].dt.to_period('M').astype(str)
        
        top_cost_mat = f.groupby('Nama Material')['TOTAL'].sum().nlargest(5).index.tolist()
        cost_data = f[f['Nama Material'].isin(top_cost_mat)]
        cost_pivot = cost_data.pivot_table(index='BulanStr', columns='Nama Material', values='TOTAL', aggfunc='sum', fill_value=0)
        
        if not cost_pivot.empty and cost_pivot.sum().sum() > 0:
            fig_cost = px.bar(cost_pivot, x=cost_pivot.index, y=cost_pivot.columns,
                              title='Top 5 Material Cost per Bulan',
                              color_discrete_sequence=px.colors.qualitative.Set2)
            fig_cost.update_layout(height=400, barmode='stack', xaxis_title='Bulan', yaxis_title='Cost (Rp)')
            st.plotly_chart(fig_cost, use_container_width=True)
        else:
            st.info("Data cost tidak cukup.")
    else:
        st.info("Data TOTAL (kolom P) tidak tersedia.")
    
    st.markdown("---")
    
    # ==== GRAFIK 4: STOCK OUT RISK ====
    st.subheader("⚠️ Stock Out Risk & Lead Time")
    if not df_stock.empty and m1 is not None and 'pltd' in m1.columns and 'kode_material' in m1.columns and 'keb_aktual' in m1.columns:
        prev_stock = df_stock[df_stock['Jenis']=='Preventive'].copy()
        prev_stock['PLTD'] = prev_stock['PLTD'].astype(str).str.strip().str.upper()
        prev_stock['Kode Material'] = prev_stock['Kode Material'].astype(str).str.strip().str.upper()
        
        m1_copy = m1[['pltd','kode_material','keb_aktual']].copy()
        m1_copy['pltd'] = m1_copy['pltd'].astype(str).str.strip().str.upper()
        m1_copy['kode_material'] = m1_copy['kode_material'].astype(str).str.strip().str.upper()
        
        risk = prev_stock.merge(m1_copy, left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        risk.drop(columns=['pltd','kode_material'], inplace=True, errors='ignore')
        
        risk['Sisa Hari'] = np.where(
            risk['keb_aktual'].notna() & (risk['keb_aktual'] > 0),
            risk['Qty'] / risk['keb_aktual'] * 30.5,
            np.nan
        )
        
        if m2 is not None and 'pltd' in m2.columns and 'durasi_kirim' in m2.columns:
            m2_copy = m2[['pltd','durasi_kirim']].copy()
            m2_copy['pltd'] = m2_copy['pltd'].astype(str).str.strip().str.upper()
            risk = risk.merge(m2_copy, on='PLTD', how='left')
            risk['durasi_kirim'] = risk['durasi_kirim'].fillna(14)
        else:
            risk['durasi_kirim'] = 14
        
        risk['Status Risiko'] = np.where(
            risk['Sisa Hari'].isna(), 'Unknown',
            np.where(risk['Sisa Hari'] < risk['durasi_kirim'], '🔴 Critical',
                     np.where(risk['Sisa Hari'] < 1.5*risk['durasi_kirim'], '🟡 Warning', '🟢 Aman'))
        )
        
        risk_count = risk['Status Risiko'].value_counts().reset_index()
        risk_count.columns = ['Status','Count']
        fig_risk = px.bar(risk_count, x='Status', y='Count', color='Status',
                          color_discrete_map={'🔴 Critical':'#E74C3C','🟡 Warning':'#F39C12','🟢 Aman':'#27AE60','Unknown':'#95A5A6'})
        fig_risk.update_layout(height=350, xaxis_title='', yaxis_title='Jumlah Material')
        st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.info("Data kebutuhan tidak tersedia.")
    
    st.markdown("---")
    
    # ==== GRAFIK 5: PLAN VS AKTUAL ====
    st.subheader("📊 Plan vs Aktual")
    if not df_stock.empty and m1 is not None and 'pltd' in m1.columns and 'kode_material' in m1.columns:
        pva = df_stock[df_stock['Jenis']=='Preventive'].copy()
        pva['PLTD'] = pva['PLTD'].astype(str).str.strip().str.upper()
        pva['Kode Material'] = pva['Kode Material'].astype(str).str.strip().str.upper()
        
        m1_copy = m1[['pltd','kode_material','keb_pm','keb_aktual']].copy()
        m1_copy['pltd'] = m1_copy['pltd'].astype(str).str.strip().str.upper()
        m1_copy['kode_material'] = m1_copy['kode_material'].astype(str).str.strip().str.upper()
        
        pva = pva.merge(m1_copy, left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        pva.drop(columns=['pltd','kode_material'], inplace=True, errors='ignore')
        
        pva_agg = pva.groupby('Nama Material').agg({'keb_pm':'sum','keb_aktual':'sum','Qty':'sum'}).reset_index()
        pva_agg = pva_agg[pva_agg['keb_pm'] > 0].head(10)
        
        if not pva_agg.empty:
            fig_pva = px.bar(pva_agg, x='Nama Material', y=['keb_pm','keb_aktual'],
                             title='Plan (PM) vs Aktual per Material (Top 10)',
                             barmode='group',
                             color_discrete_map={'keb_pm':'#3498DB','keb_aktual':'#E74C3C'})
            fig_pva.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_pva, use_container_width=True)
        else:
            st.info("Data plan vs aktual tidak cukup.")
    else:
        st.info("Data master tidak tersedia.")
    
    st.markdown("---")
    
    # ==== TABEL DETAIL (PALING BAWAH) ====
    st.subheader("📋 Detail Pemakaian Material")
    cols_show = ['Tanggal','Nama Material','Kode Material','Masuk','Keluar','Stok','Gudang','Keterangan','Transaksi','JobType','Jenis']
    if 'TOTAL' in f.columns:
        cols_show.append('TOTAL')
    
    cols_show = [c for c in cols_show if c in f.columns]
    if 'Tanggal' in f.columns:
        f = f.sort_values('Tanggal', ascending=False)
    st.dataframe(f[cols_show], use_container_width=True, hide_index=True, height=400)

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
