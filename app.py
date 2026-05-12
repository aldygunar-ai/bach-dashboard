import streamlit as st
import sys
sys.path.append('.')

# Import langsung dari app.py
from app import load_all

st.set_page_config(page_title="Debug Load All Padang")
st.title("🔍 Cek df_stock untuk PADANG MANGGAR dari load_all()")

data = load_all()
df = data['stock']

st.write(f"**Total baris di df_stock: {len(df)}**")
st.write(f"**PLTD unik: {sorted(df['PLTD'].unique())}**")

padang = df[df['PLTD'] == 'PADANG MANGGAR']
st.write(f"**Baris PADANG MANGGAR: {len(padang)}**")

if not padang.empty:
    st.dataframe(padang[['PLTD', 'Kode Material', 'Nama Material', 'Qty', 'Primary Code', 'Jenis']])
    
    prev_padang = padang[padang['Jenis'] == 'Preventive']
    st.write(f"**Preventive: {len(prev_padang)}**")
    if not prev_padang.empty:
        st.dataframe(prev_padang[['Kode Material', 'Nama Material', 'Qty', 'Primary Code']])
else:
    st.error("❌ PADANG MANGGAR TIDAK ADA di df_stock!")
