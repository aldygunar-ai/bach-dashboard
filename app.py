import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PLTD Bach Dashboard", page_icon="⚡", layout="wide")

# ==================== CUSTOM CSS - CORPORATE BLUE PREMIUM ====================
st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .header {
        background: linear-gradient(135deg, #0A2540 0%, #1E40AF 100%);
        padding: 2.8rem 0;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(10, 37, 64, 0.25);
    }
    h1 { font-size: 2.8rem !important; font-weight: 800; margin: 0; }
    h2 { color: #0A2540; font-weight: 700; }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
    }
    .stMetricValue { font-size: 2.1rem !important; font-weight: 700; color: #1E40AF; }
    
    [data-testid="stSidebar"] {
        background-color: #0A2540;
    }
    [data-testid="stSidebar"] * { color: #E0F2FE !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== HEADER ======================
st.markdown("""
<div class="header">
    <h1>⚡ Dashboard PLTD Bach</h1>
    <p style="font-size:1.25rem; margin-top:12px; opacity:0.95;">
        Monitoring Stok • Logistik • Preventive Maintenance
    </p>
</div>
""", unsafe_allow_html=True)

# ====================== LOAD DATA ======================
data = load_all()          # ← fungsi kamu tetap
df = data.get('stock', pd.DataFrame())

# ====================== METRICS ======================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total PLTD", df['PLTD'].nunique() if not df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total Stok", f"{int(df['Qty'].sum()):,}" if not df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Preventive", (df['Jenis']=='Preventive').sum() if not df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Corrective", (df['Jenis']=='Corrective').sum() if not df.empty else 0)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ====================== MAIN CONTENT ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Beranda", 
    "📦 Stok Material", 
    "📊 Analisis Pemakaian", 
    "📋 Propose Order", 
    "🚚 Transaksi Project"
])

with tab1:
    st.subheader("📍 Lokasi PLTD")
    # masukkan kode map kamu di sini

with tab2:
    st.subheader("📦 Stok Material")
    # masukkan kode page_stock kamu di sini (tab Preventive, Corrective, Sisa Bulan)

with tab3:
    st.subheader("📊 Analisis Pemakaian Material")
    # masukkan kode page_analisis kamu

with tab4:
    st.subheader("📋 Propose Order Material")
    # masukkan kode page_propose kamu

with tab5:
    st.subheader("🚚 Transaksi Project")
    # masukkan kode page_transaksi kamu
