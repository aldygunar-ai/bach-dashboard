import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import gspread
from gspread_dataframe import get_as_dataframe
import requests
import io

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
DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"

PREVENTIVE_CODES = {
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076', '3629140',
    'AF872', 'AF25278', 'AHO1135', '5413003', '3015257', '5412990',
    '5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108',
    'RIMULA R4 X 15W-40'
}

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
    """Kolom: B=nama, D=kode, I=qty"""
    client = get_gspread_client()
    rows = []
    for pltd, sid in PLTD_SHEETS.items():
        try:
            sh = client.open_by_key(sid)
            data = sh.sheet1.get_all_values()
            if len(data) < 2: continue
            for r in data[1:]:
                if len(r) < 9: continue
                nama = r[1].strip()
                kode = r[3].strip()
                qty = float(r[8].replace(',', '')) if r[8].strip() else 0.0
                if kode or nama:
                    rows.append((pltd, kode, nama, qty))
        except: pass
    df = pd.DataFrame(rows, columns=['PLTD','Kode Material','Nama Material','Qty'])
    if not df.empty:
        df['Jenis'] = df['Kode Material'].apply(lambda x: 'Preventive' if x in PREVENTIVE_CODES else 'Corrective')
    return df

@st.cache_data(ttl=600)
def load_master_data():
    client = get_gspread_client()
    sh = client.open_by_key(MASTER_PLTD_ID)
    # Master 1
    try:
        df1 = get_as_dataframe(sh.worksheet('Master data 1'), evaluate_formulas=True)
        df1.columns = df1.columns.str.strip()
        rename1 = {'Nama Material':'nama_material','Kode Material':'kode_material',
                   'Nama PLTD':'pltd','Jenis Service':'jenis_service',
                   'Harga D365':'harga','Kebutuhan Perbulan Sesuai CF PM':'keb_pm',
                   'Kebutuhan Perbulan Sesuai Aktual FC':'keb_aktual'}
        df1.rename(columns={k:v for k,v in rename1.items() if k in df1.columns}, inplace=True)
    except: df1 = None
    # Master 2
    try:
        df2 = get_as_dataframe(sh.worksheet('Master data 2'), evaluate_formulas=True)
        df2.columns = df2.columns.str.strip()
        rename2 = {'Nama PLTD':'pltd','Durasi Kirim Darat+Laut (Hari)':'durasi_kirim'}
        df2.rename(columns={k:v for k,v in rename2.items() if k in df2.columns}, inplace=True)
        if 'durasi_kirim' in df2.columns:
            df2['durasi_kirim'] = pd.to_numeric(df2['durasi_kirim'], errors='coerce').fillna(14)
    except: df2 = None
    return df1, df2

@st.cache_data(ttl=600)
def load_delivery():
    try:
        resp = requests.get(DELIVERY_URL, headers={'User-Agent':'Mozilla/5.0'}, timeout=20)
        return pd.read_excel(io.BytesIO(resp.content))
    except: return pd.DataFrame()

# ======================== APLIKASI ========================
def home():
    st.title("⚡ Dashboard Stok & Logistik PLTD")
    df = load_stock_all()
    if df.empty: st.warning("Data belum tersedia."); return
    c1,c2,c3 = st.columns(3)
    c1.metric("PLTD", df['PLTD'].nunique())
    c2.metric("Total Stok", f"{df['Qty'].sum():,.0f}")
    c3.metric("Kritis", "Lihat Analisis")
    st.markdown("---")
    st.info("Gunakan sidebar untuk navigasi.")
    pltd_coords = {
        'Pemaron':(-8.16,114.68),'Mangoli':(-1.88,125.37),'Tayan':(-0.03,110.10),
        'Timika':(-4.56,136.89),'Bobong':(-1.95,124.39),'Merawang':(-1.95,105.96),
        'Air Anyir':(-1.94,106.11),'Padang Manggar':(-2.14,106.14),'Krueng Raya':(5.60,95.53),
        'Lueng Bata':(5.55,95.33),'Ulee Kareng':(5.55,95.33),'Waena':(-2.61,140.56),
        'Sambelia':(-8.40,116.67),'Timika 2':(-4.56,136.89),'Wamena':(-4.09,138.94)
    }
    loc = df[['PLTD']].drop_duplicates()
    loc['lat'] = loc['PLTD'].map(lambda x: pltd_coords.get(x,(None,None))[0])
    loc['lon'] = loc['PLTD'].map(lambda x: pltd_coords.get(x,(None,None))[1])
    st.map(loc.dropna(subset=['lat']), latitude='lat', longitude='lon', zoom=4, height=350)

def page_stock():
    st.title("📦 Stok Material PLTD")
    df = load_stock_all()
    if df.empty: st.warning("Data belum tersedia."); return
    
    st.sidebar.header("Filter")
    pltd_opts = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opts, default=pltd_opts)
    sel_jenis = st.sidebar.multiselect("Jenis", ['Preventive','Corrective'], default=['Preventive','Corrective'])
    df_f = df[df['PLTD'].isin(sel_pltd) & df['Jenis'].isin(sel_jenis)]

    # Pivot: baris material, kolom PLTD
    pivot = df_f.pivot_table(index=['Kode Material','Nama Material','Jenis'],
                             columns='PLTD', values='Qty', aggfunc='sum', fill_value=0)
    pivot['Total'] = pivot.sum(axis=1)
    st.subheader("🔹 Tabel Stok (Material vs PLTD)")
    st.dataframe(pivot.reset_index(), use_container_width=True, hide_index=True)

    # Pengiriman
    st.subheader("🚚 Status Pengiriman")
    deliv = load_delivery()
    if not deliv.empty:
        if 'STATUS' in deliv.columns:
            mapping = {'IN TRANSIT':'Proses Kirim','SHIPPED':'Proses Kirim',
                       'PO':'Proses Import/Pembelian','PROCUREMENT':'Proses Import/Pembelian'}
            deliv['Kategori'] = deliv['STATUS'].map(mapping).fillna('Lainnya')
        else:
            deliv['Kategori'] = 'Proses Kirim'
        st.dataframe(deliv, use_container_width=True, hide_index=True)
    else:
        st.info("Data pengiriman belum tersedia.")

def page_analisis():
    st.title("📊 Analisis Kebutuhan & Lead Time")
    df = load_stock_all()
    if df.empty: st.warning("Data stok belum tersedia."); return
    master1, master2 = load_master_data()

    # Gabung dengan master
    if master1 is not None:
        df = df.merge(master1[['pltd','kode_material','jenis_service','harga','keb_pm','keb_aktual']],
                      left_on=['PLTD','Kode Material'], right_on=['pltd','kode_material'], how='left')
        if 'pltd' in df.columns: df.drop(columns=['pltd'], inplace=True)
    else:
        df['harga'] = np.nan; df['keb_pm'] = np.nan; df['keb_aktual'] = np.nan

    if master2 is not None and 'pltd' in master2.columns and 'durasi_kirim' in master2.columns:
        df = df.merge(master2[['pltd','durasi_kirim']], left_on='PLTD', right_on='pltd', how='left')
        if 'pltd' in df.columns: df.drop(columns=['pltd'], inplace=True)
    else:
        df['durasi_kirim'] = 14

    df['keb_efektif'] = df['keb_aktual'].fillna(df['keb_pm']).fillna(0)
    df['keb_harian'] = df['keb_efektif'] / 30.5
    df['sisa_hari'] = np.where(df['keb_harian'] > 0, df['Qty'] / df['keb_harian'], 9999)
    dur = df['durasi_kirim'].fillna(14)
    df['status'] = np.where(df['sisa_hari'] < dur, '🔴 Critical Reorder',
                    np.where(df['sisa_hari'] < 1.5*dur, '🟡 Warning', '🟢 Aman'))
    df['propose'] = np.ceil(np.maximum(0, (df['keb_harian'] * dur) - df['Qty']))

    st.sidebar.header("Filter")
    pltd_opts = sorted(df['PLTD'].unique())
    sel_pltd = st.sidebar.multiselect("PLTD", pltd_opts, default=pltd_opts)
    sel_jenis = st.sidebar.multiselect("Jenis", ['Preventive','Corrective'], default=['Preventive','Corrective'])
    sel_status = st.sidebar.multiselect("Status", ['🔴 Critical Reorder','🟡 Warning','🟢 Aman'],
                                        default=['🔴 Critical Reorder','🟡 Warning','🟢 Aman'])
    df_v = df[df['PLTD'].isin(sel_pltd) & df['Jenis'].isin(sel_jenis) & df['status'].isin(sel_status)]

    cols = ['PLTD','Kode Material','Nama Material','Jenis','Qty','keb_pm','keb_aktual',
            'sisa_hari','durasi_kirim','status','propose']
    if 'harga' in df_v.columns: cols.insert(-1,'harga')
    st.subheader("📋 Tabel Kebutuhan")
    st.dataframe(df_v[cols], use_container_width=True, hide_index=True)

    st.subheader("⏳ Alert Status")
    st.bar_chart(df_v['status'].value_counts())

    pm = df_v[df_v['Jenis']=='Preventive']
    if not pm.empty:
        mat = st.selectbox("Timeline Material PM", pm['Nama Material'].unique())
        row = pm[pm['Nama Material']==mat].iloc[0]
        st.metric("Sisa Hari Stok", f"{row['sisa_hari']:.0f}")
        st.progress(min(row['sisa_hari']/row['durasi_kirim'], 1.0))

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
