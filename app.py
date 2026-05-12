import streamlit as st
import requests
import io
import pandas as pd

st.set_page_config(page_title="Debug DAS v2")
st.title("🔍 Debug DAS dengan URL Baru")

URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?e=QEqUQc&download=1"

headers = {'User-Agent': 'Mozilla/5.0'}

try:
    resp = requests.get(URL_DAS, headers=headers, timeout=30)
    st.write(f"**Status:** {resp.status_code}")
    st.write(f"**Size:** {len(resp.content)} bytes")
    
    if resp.status_code == 200:
        df = pd.read_excel(io.BytesIO(resp.content))
        st.success(f"✅ {len(df)} baris, {len(df.columns)} kolom")
        st.write("**Kolom:**", list(df.columns))
        st.write("**5 baris pertama:**")
        st.dataframe(df.head())
        
        # Cek kolom PROJECT
        if 'PROJECT' not in df.columns:
            df['PROJECT'] = 'PROJECT DAS'
        st.write(f"**PROJECT unik:** {df['PROJECT'].unique()}")
except Exception as e:
    st.error(f"Error: {e}")
