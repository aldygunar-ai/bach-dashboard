import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

## Konfigurasi Utama
st.set_page_config(page_title="Dashboard Project Bach", layout="wide", page_icon="📊")

## Database Link PLTD
## Menggunakan ID dari link yang Anda berikan
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
    "Ulee Kareng": "1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU",
    "Waena": "", # Link Menyusul
    "Sambelia": "", # Link Menyusul
    "Timika 2": "", # Link Menyusul
    "Wamena": "" # Link Menyusul
}

ID_GABUNGAN_D365 = "1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs"

## Fungsi Helper
def get_csv_url(sheet_id, sheet_name=None):
    if not sheet_id:
        return None
    if sheet_name:
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=600)
def load_data(url):
    if url:
        try:
            return pd.read_csv(url)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

## Sidebar Navigasi
st.sidebar.title("Dashboard Project Bach")
page = st.sidebar.radio("Navigasi Halaman", ["Page 1: Menu", "Page 2: Stock Aktual", "Page 3: Analisa & Propose", "Page 4: Pemakaian"])

## Global Filter - Dibuat Bersih (Kosong di Awal)
st.sidebar.markdown("---")
st.sidebar.subheader("Global Filter")
f_pltd = st.sidebar.multiselect("Pilih Nama PLTD", options=list(PLTD_IDS.keys()), default=[])
f_kode = st.sidebar.text_input("Cari Kode Material")
f_nama = st.sidebar.text_input("Cari Nama Material")
f_jenis = st.sidebar.selectbox("Jenis Material", ["Semua", "Preventive", "Corrective"])

## Logic Page 1: Menu Utama
if page == "Page 1: Menu":
    st.title("Logistics Command Center")
    st.markdown("### Selamat Datang di Dashboard Project Bach")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("#### Cek Stock Material PLTD")
        st.write("Pantau ketersediaan stok aktual di setiap site.")
    with col2:
        st.info("#### Cek Pemakaian Material PLTD")
        st.write("Analisa riwayat pemakaian dan biaya material.")
    
    st.markdown("---")
    st.subheader("Fitur Download Report")
    st.write("Gunakan tombol download pada setiap halaman untuk menarik data ke Excel/CSV.")

## Logic Page 2: Stock Aktual
elif page == "Page 2: Stock Aktual":
    st.title("📦 Stock Material PLTD Aktual")
    
    if not f_pltd:
        st.warning("⚠️ Silakan pilih minimal satu PLTD pada filter sidebar untuk menampilkan data.")
    else:
        # Load Data PLTD Terpilih
        target_id = PLTD_IDS.get(f_pltd[0])
        df_stok = load_data(get_csv_url(target_id))
        
        # Metrik Ringkasan (Simulasi dari data gudang & transit)
        m1, m2, m3 = st.columns(3)
        m1.metric("Proses Kirim (In-Transit)", "Aktif")
        m2.metric("Proses Import / Pembelian", "On Progress")
        m3.metric("Stok Gudang Cikande", "Tersedia")

        if not df_stok.empty:
            st.subheader(f"Data Stok: {f_pltd[0]}")
            st.dataframe(df_stok, use_container_width=True)
            
            csv = df_stok.to_csv(index=False).encode('utf-8')
            st.download_button("Download Report Stock", data=csv, file_name=f"Stock_{f_pltd[0]}.csv", mime='text/csv')
        else:
            st.error("Data tidak ditemukan atau ID Spreadsheet salah.")

## Logic Page 3: Analisa & Propose
elif page == "Page 3: Analisa & Propose":
    st.title("📈 Analisa & Propose Pengiriman")
    
    if not f_pltd:
        st.warning("⚠️ Pilih PLTD di sidebar untuk memulai analisa.")
    else:
        # Load Data Harga D365 & Data Stok
        url_harga = get_csv_url(ID_GABUNGAN_D365, "DARI+TARIKAN")
        df_harga = load_data(url_harga)
        
        target_id = PLTD_IDS.get(f_pltd[0])
        df_stok = load_data(get_csv_url(target_id))
        
        if not df_stok.empty and not df_harga.empty:
            # Integrasi Harga (Merge berdasarkan Kode Material)
            df_merged = pd.merge(df_stok, df_harga, on='Kode Material', how='left')
            
            # Lead Time Alert Logic
            st.subheader("Lead Time Alert")
            if 'Stock_Bulan' in df_merged.columns:
                critical = df_merged[df_merged['Stock_Bulan'] < 1.5]
                if not critical.empty:
                    st.error(f"Terdapat {len(critical)} material dengan status Critical Reorder!")
                    st.dataframe(critical)
            
            st.subheader("Propose Pembelian & Pengiriman")
            st.dataframe(df_merged, use_container_width=True)
        else:
            st.info("Memuat data analisa dan harga D365...")

## Logic Page 4: Pemakaian
elif page == "Page 4: Pemakaian":
    st.title("📊 Analisa Pemakaian Material")
    
    url_gabungan = get_csv_url(ID_GABUNGAN_D365, "Gabungan")
    df_gabungan = load_data(url_gabungan)
    
    if not df_gabungan.empty:
        # Logic Need Consume
        if 'No_Transaksi' in df_gabungan.columns:
            df_gabungan['Status_Consume'] = df_gabungan['No_Transaksi'].apply(
                lambda x: "Need Consume" if pd.isna(x) or x == "" else "Consumed"
            )
        
        # Visualisasi
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top 10 Material Terbanyak")
            if 'Nama Material' in df_gabungan.columns:
                fig = px.bar(df_gabungan.head(10), x='Nama Material', y=df_gabungan.columns[1])
                st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("Status Konsumsi")
            fig_pie = px.pie(df_gabungan, names='Status_Consume', hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.subheader("Dashboard Project Bach - Lokasi Site")
        if 'lat' in df_gabungan.columns and 'lon' in df_gabungan.columns:
            st.map(df_gabungan[['lat', 'lon']])
        
        st.dataframe(df_gabungan, use_container_width=True)
    else:
        st.warning("Data gabungan pemakaian belum tersedia.")
