import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Konfigurasi Halaman Utama
st.set_page_config(page_title="Dashboard Project Bach", layout="wide", page_icon="📊")

# --- 1. DATABASE LINK (Google Sheets) ---
PLTD_LINKS = {
    "Pemaron": "https://docs.google.com/spreadsheets/d/1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI/gviz/tq?tqx=out:csv",
    "Mangoli": "https://docs.google.com/spreadsheets/d/1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s/gviz/tq?tqx=out:csv",
    "Tayan": "https://docs.google.com/spreadsheets/d/1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo/gviz/tq?tqx=out:csv",
    "Timika": "https://docs.google.com/spreadsheets/d/1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04/gviz/tq?tqx=out:csv",
    "Bobong": "https://docs.google.com/spreadsheets/d/1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM/gviz/tq?tqx=out:csv",
    "Merawang": "https://docs.google.com/spreadsheets/d/1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8/gviz/tq?tqx=out:csv",
    "Air Anyir": "https://docs.google.com/spreadsheets/d/10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o/gviz/tq?tqx=out:csv",
    "Padang Manggar": "https://docs.google.com/spreadsheets/d/1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s/gviz/tq?tqx=out:csv",
    "Krueng Raya": "https://docs.google.com/spreadsheets/d/1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s/gviz/tq?tqx=out:csv",
    "Lueng Bata": "https://docs.google.com/spreadsheets/d/1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g/gviz/tq?tqx=out:csv",
    "Ulee Kareng": "https://docs.google.com/spreadsheets/d/1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU/gviz/tq?tqx=out:csv"
}

LINK_GABUNGAN = "https://docs.google.com/spreadsheets/d/1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs/gviz/tq?tqx=out:csv&sheet=Gabungan"
LINK_D365_HARGA = "https://docs.google.com/spreadsheets/d/1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs/gviz/tq?tqx=out:csv&sheet=DARI+TARIKAN"

@st.cache_data(ttl=600)
def load_data(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# --- 2. SIDEBAR NAVIGASI & FILTER GLOBAL ---
st.sidebar.image("https://via.placeholder.com/150x50?text=BACH+LOGISTICS", use_container_width=True) # Ganti dengan logo Bach
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Stock Aktual", "Analisa & Propose", "Pemakaian"])

# Filter Global
st.sidebar.markdown("---")
st.sidebar.subheader("Global Filter")
selected_pltd = st.sidebar.multiselect("Pilih PLTD", options=list(PLTD_LINKS.keys()), default=["Pemaron"])
material_type = st.sidebar.selectbox("Jenis Material", ["Semua", "Preventive", "Corrective"])

# --- PAGE 1: HOME ---
if page == "Home":
    st.title("🚛 Logistics Command Center")
    st.subheader("Dashboard Project Bach")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### Cek Stock Material\nPantau posisi stok terkini di setiap site PLTD.")
        if st.button("Buka Stock"): page = "Stock Aktual"
    with col2:
        st.info("### Analisa Pemakaian\nLihat histori penggunaan dan sisa durasi stok.")
        if st.button("Buka Pemakaian"): page = "Pemakaian"

# --- PAGE 2: STOCK AKTUAL ---
elif page == "Stock Aktual":
    st.title("📦 Stock Material PLTD Aktual")
    
    # Metrik Ringkasan
    m1, m2, m3 = st.columns(3)
    m1.metric("In-Transit (PR/MR)", "12 Shipments")
    m2.metric("Procurement Process", "8 Items")
    m3.metric("Gudang Cikande", "1.240 Unit")
    
    # Load Data dari salah satu PLTD terpilih
    target_url = PLTD_LINKS.get(selected_pltd[0] if selected_pltd else "Pemaron")
    df_stok = load_data(target_url)
    
    if not df_stok.empty:
        st.dataframe(df_stok, use_container_width=True)
        csv = df_stok.to_csv(index=False).encode('utf-8')
        st.download_button("Download Stock Report", data=csv, file_name="Stock_Report.csv", mime='text/csv')
    else:
        st.warning("Data untuk site ini belum tersedia atau link tidak valid.")

# --- PAGE 3: ANALISA & PROPOSE ---
elif page == "Analisa & Propose":
    st.title("📈 Analisa & Propose Pengiriman")
    
    # Integrasi Harga D365
    df_harga = load_data(LINK_D365_HARGA)
    df_stok = load_data(PLTD_LINKS.get(selected_pltd[0] if selected_pltd else "Pemaron"))
    
    if not df_stok.empty and not df_harga.empty:
        # Gabungkan data stok dengan harga berdasarkan Kode Material
        df_merged = pd.merge(df_stok, df_harga[['Kode Material', 'Harga']], on='Kode Material', how='left')
        
        # Logika Lead Time Alert
        # Misal: Sisa_Bulan < 1.5 bulan (Threshold pengiriman)
        if 'Stock_Bulan' in df_merged.columns:
            st.error("🚨 **Critical Reorder Alert:** Material berikut harus segera dikirim!")
            critical = df_merged[df_merged['Stock_Bulan'] < 1.5]
            st.table(critical[['Kode Material', 'Nama Material', 'Stock_Bulan']])
        
        st.subheader("Kalkulasi Kebutuhan (CF PM vs Aktual)")
        st.dataframe(df_merged)
    else:
        st.info("Memuat data analisa...")

# --- PAGE 4: PEMAKAIAN ---
elif page == "Pemakaian":
    st.title("📊 Analisa Pemakaian Material")
    
    df_gabungan = load_data(LINK_GABUNGAN)
    
    if not df_gabungan.empty:
        # Logika Need Consume (Jika nomor transaksi kosong)
        df_gabungan['Status'] = df_gabungan['No_Transaksi'].apply(lambda x: "Need Consume" if pd.isna(x) or x == "" else "Consumed")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("TOP 10 Material Terbanyak")
            fig = px.bar(df_gabungan.head(10), x='Nama Material', y='Qty', color='Status')
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("Status Konsumsi Material")
            fig_pie = px.pie(df_gabungan, names='Status', hole=0.4, color='Status', 
                             color_discrete_map={"Need Consume": "red", "Consumed": "green"})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.subheader("Peta Sebaran Project Bach")
        # Pastikan ada kolom lat & lon di Google Sheets Gabungan
        if 'lat' in df_gabungan.columns and 'lon' in df_gabungan.columns:
            st.map(df_gabungan[['lat', 'lon']])
            
        st.dataframe(df_gabungan)
    else:
        st.warning("Data pemakaian belum tersedia.")
