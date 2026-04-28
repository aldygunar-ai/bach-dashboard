import streamlit as st
import pandas as pd
from utils import load_project_data

st.set_page_config(page_title="Transaksi Project", layout="wide")

df_raw = load_project_data()

# Reset logic dari kode asli
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
    m1.metric("Total Order", f"{len(df_f)}")
    m2.metric("Total Qty", f"{int(df_f['QTY'].sum()):,}")
    m3.metric("Total Biaya", f"Rp {df_f['TOTAL COST'].sum():,.0f}")
    m4.metric("Site Aktif", df_f['WH TUJUAN'].nunique())

    st.markdown("---")
    st.subheader("📈 Tren Permintaan Harian")
    trend_data = df_f.groupby('Tgl_Str').size().reset_index(name='Requests')
    fig_tr = px.line(trend_data, x='Tgl_Str', y='Requests', markers=True, text='Requests')
    st.plotly_chart(fig_tr, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏢 Top Site Request (QTY)")
        top_site = df_f.groupby('WH TUJUAN')['QTY'].sum().nlargest(8)
        st.bar_chart(top_site)
    with c2:
        st.subheader("🔝 Top Requested Items")
        top_item = df_f.groupby('ITEM NAME')['QTY'].sum().nlargest(8)
        st.bar_chart(top_item)

    st.markdown("---")
    st.subheader("⚠️ Highlight Outstanding")
    df_out = df_f[~df_f['STATUS'].isin(['DELIVERED', 'CANCEL'])]
    st.dataframe(df_out[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'STATUS']],
                 use_container_width=True, hide_index=True)

    st.subheader("📋 Detail Movement Record")
    st.dataframe(df_f[['TANGGAL', 'PROJECT', 'WH TUJUAN', 'ITEM NAME', 'QTY', 'TOTAL COST', 'STATUS']],
                 use_container_width=True, hide_index=True)