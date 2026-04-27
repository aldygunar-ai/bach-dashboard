import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import numpy as np

# --- 1. KONFIGURASI HALAMAN & STYLE ---
st.set_page_config(page_title="Dashboard Project Bach", layout="wide")

TEMA_BIRU = "#0E2F56"
TEMA_MUDA = "#4B8BBE"

st.markdown(f"""
    <style>
    .main {{ background-color: #F8F9FA; }}
    [data-testid="stSidebar"] {{ background-color: {TEMA_BIRU} !important; }}
    .sidebar-title {{
        color: white; font-size: 20px; font-weight: 800; text-align: center;
        margin-bottom: 25px; padding: 10px; border-bottom: 1px solid #ffffff33;
    }}
    [data-testid="stSidebar"] label p {{ color: white !important; font-weight: 500 !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px; font-weight: 800; color: {TEMA_BIRU}; }}
    .stPlotlyChart {{ background-color: white; border-radius: 12px; padding: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE LINK ---
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

ID_GABUNGAN_D365 = "1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs"
URL_OPS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

# --- 3. HELPER FUNCTIONS ---
@st.cache_data
def load_transaction_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res_ops = requests.get(URL_OPS, headers=headers, timeout=20)
        df_ops = pd.read_excel(io.BytesIO(res_ops.content))
        df_ops['PROJECT'] = 'PROJECT PLTD'
    except: df_ops = pd.DataFrame()
    try:
        res_das = requests.get(URL_DAS, headers=headers, timeout=20)
        df_das = pd.read_excel(io.BytesIO(res_das.content))
        df_das['PROJECT'] = 'PROJECT DAS'
    except: df_das = pd.DataFrame()
    df = pd.concat([df_ops, df_das], ignore_index=True)
    if not df.empty and 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        df = df.dropna(subset=['TANGGAL'])
        df['Tahun'] = df['TANGGAL'].dt.year.astype(str)
        df['Bulan'] = df['TANGGAL'].dt.strftime('%B')
        df['Tgl_Str'] = df['TANGGAL'].dt.strftime('%Y-%m-%d')
    
    geo_data = {'ACEH': [4.69, 96.74], 'BALI': [-8.34, 115.09], 'BANGKA': [-2.13, 106.11],
                'JAKARTA': [-6.20, 106.84], 'KALBAR': [-0.27, 109.97], 'MALUKU': [-3.23, 130.14],
                'PAPUA': [-4.26, 138.08], 'SUMUT': [2.11, 99.13], 'SULSEL': [-5.14, 119.43]}
    if not df.empty and 'PROVINCE' in df.columns:
        df['lat'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[0])
        df['lon'] = df['PROVINCE'].str.upper().map(lambda x: geo_data.get(x, [0, 0])[1])
    return df

@st.cache_data(ttl=600)
def load_gsheet_data(sheet_id, sheet_name=None):
    if not sheet_id: return pd.DataFrame()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    if sheet_name: url += f"&sheet={sheet_name.replace(' ', '+')}"
    try: return pd.read_csv(url)
    except: return pd.DataFrame()

def find_column(df, keywords):
    """Mencari nama kolom asli berdasarkan list keyword."""
    for col in df.columns:
        if any(key.upper() in col.upper() for key in keywords):
            return col
    return None

# --- 4. SIDEBAR ---
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

with st.sidebar:
    st.markdown('<div class="sidebar-title">PT BACH MULTI GLOBAL</div>', unsafe_allow_html=True)
    page = st.radio("Navigasi", ["Page 1: Menu Utama", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Monitoring Transaksi"])
    
    st.divider()
    c = st.session_state.reset_counter
    if page == "Page 4: Monitoring Transaksi":
        df_raw_transaksi = load_transaction_data()
        sel_proj = st.multiselect("Project", df_raw_transaksi['PROJECT'].unique() if not df_raw_transaksi.empty else [], key=f'p_{c}')
        sel_year = st.multiselect("Tahun", sorted(df_raw_transaksi['Tahun'].unique(), reverse=True) if not df_raw_transaksi.empty else [], key=f'y_{c}')
        sel_stat = st.multiselect("Status", sorted(df_raw_transaksi['STATUS'].unique()) if not df_raw_transaksi.empty else [], key=f's_{c}')
    else:
        sel_pltd = st.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()), key=f'pltd_{c}')

    st.button("🔄 Clear All Filters", on_click=lambda: st.session_state.update({"reset_counter": st.session_state.reset_counter + 1}), use_container_width=True)

# --- PAGE 2: STOCK AKTUAL (FIXED READ & COMPARISON) ---
if page == "Page 2: Stock Aktual":
    st.title("📦 Perbandingan Stock Aktual Antar Site")
    if not sel_pltd:
        st.info("👋 Pilih beberapa PLTD di sidebar untuk membandingkan stok.")
    else:
        all_data = []
        for site in sel_pltd:
            df = load_gsheet_data(PLTD_IDS.get(site))
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                # Cari kolom kunci
                c_kode = find_column(df, ['KODE', 'PART NUMBER'])
                c_nama = find_column(df, ['NAMA', 'DESCRIPTION'])
                c_qty = find_column(df, ['SISA', 'AKTUAL', 'STOCK', 'QTY'])
                
                # Filter hanya kolom yang ada
                cols = [c for c in [c_kode, c_nama, c_qty] if c]
                temp_df = df[cols].copy()
                temp_df['LOKASI'] = site
                # Rename untuk standarisasi tabel perbandingan
                temp_df = temp_df.rename(columns={c_kode: 'Kode', c_nama: 'Nama Material', c_qty: 'Stock Aktual'})
                all_data.append(temp_df)
        
        if all_data:
            df_compare = pd.concat(all_data, ignore_index=True)
            
            # Tampilan Ringkasan Tabel (Mudah Dibaca)
            st.subheader("📋 Ringkasan Per Lokasi")
            for site in sel_pltd:
                site_data = df_compare[df_compare['LOKASI'] == site].drop(columns=['LOKASI'])
                with st.expander(f"📍 {site.upper()} (Total: {len(site_data)} Item)", expanded=True):
                    st.dataframe(site_data, use_container_width=True, hide_index=True)
            
            # Tabel Perbandingan Side-by-Side (Pivot)
            st.subheader("⚖️ Perbandingan Side-by-Side")
            pivot_df = df_compare.pivot_table(index=['Kode', 'Nama Material'], columns='LOKASI', values='Stock Aktual', aggfunc='sum').reset_index()
            st.dataframe(pivot_df, use_container_width=True)
        else: st.error("Data tidak ditemukan.")

# --- PAGE 3: ANALISA (AUTO-CHECK IMPROVED) ---
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose")
    if not sel_pltd:
        st.info("👋 Pilih PLTD di sidebar.")
    else:
        site = sel_pltd[0]
        df_stok = load_gsheet_data(PLTD_IDS.get(site))
        df_harga = load_gsheet_data(ID_GABUNGAN_D365, "DARI TARIKAN")
        
        if not df_stok.empty and not df_harga.empty:
            c_left = find_column(df_stok, ['KODE', 'PART NUMBER'])
            c_right = find_column(df_harga, ['KODE', 'PART NUMBER'])
            
            if c_left and c_right:
                df_merged = pd.merge(df_stok, df_harga, left_on=c_left, right_on=c_right, how='left')
                st.success(f"✅ Sinkronisasi Berhasil Menggunakan Kolom: '{c_left}'")
                st.dataframe(df_merged, use_container_width=True)
            else:
                st.error("❌ Kolom Kode Material tidak ditemukan. Harap pastikan kolom di spreadsheet mengandung kata 'KODE'.")
        else: st.warning("Data belum siap.")

# --- PAGE 4: MONITORING TRANSAKSI (DEGRADASI WARNA & RAPI) ---
elif page == "Page 4: Monitoring Transaksi":
    df_raw = load_transaction_data()
    st.title("📊 Monitoring Transaksi")
    
    if not (sel_proj or sel_year or sel_stat):
        st.info("👋 Pilih filter untuk menampilkan dashboard.")
        st.stop()

    df_f = df_raw.copy()
    if sel_proj: df_f = df_f[df_f['PROJECT'].isin(sel_proj)]
    if sel_year: df_f = df_f[df_f['Tahun'].isin(sel_year)]
    if sel_stat: df_f = df_f[df_f['STATUS'].isin(sel_stat)]

    # KPI
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Order", len(df_f))
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    st.markdown("---")
    
    # 1. Grafik Tren (Degradasi di Line & Area)
    st.subheader("📈 Tren Permintaan Harian")
    trend = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    fig_tr = px.area(trend, x='Tgl_Str', y='Requests', text='Requests', color_discrete_sequence=[TEMA_BIRU])
    fig_tr.update_traces(mode="markers+lines+text", textposition="top center")
    st.plotly_chart(fig_tr, use_container_width=True)

    # 2. Top Site & Material (Warna Degradasi / Continuous Scale)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏢 Top Site Request (QTY)")
        top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().sort_values(ascending=True).reset_index()
        # Menggunakan color_continuous_scale untuk degradasi warna
        fig_site = px.bar(top_site, y='WH TUJUAN', x='QTY', orientation='h', text_auto='.2s', 
                          color='QTY', color_continuous_scale='Blues')
        fig_site.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_site, use_container_width=True)

    with c2:
        st.subheader("🔝 Top Requested Material")
        top_mat = df_f.groupby('ITEM NAME')['QTY'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_mat = px.bar(top_mat, y='ITEM NAME', x='QTY', orientation='h', text_auto='.2s',
                         color='QTY', color_continuous_scale='GnBu')
        fig_mat.update_layout(showlegend=False, coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_mat, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS', 'TOTAL COST']], use_container_width=True, hide_index=True)
    st.map(df_f[df_f['lat'] != 0][['lat', 'lon']], zoom=3)

# --- PAGE 1: MENU UTAMA ---
elif page == "Page 1: Menu Utama":
    st.title("🚛 Dashboard Logistics Bach")
    st.markdown("### Navigasi Dashboard")
    st.info("Pilih menu di sidebar untuk melihat data stok aktual atau transaksi.")
