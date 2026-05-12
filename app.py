import streamlit as st
import requests
import io
import pandas as pd

st.set_page_config(page_title="Debug DAS")
st.title("🔍 Debug SharePoint DAS")

URL_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

headers = {'User-Agent': 'Mozilla/5.0'}

try:
    resp = requests.get(URL_DAS, headers=headers, timeout=30)
    st.write(f"**Status Code:** {resp.status_code}")
    st.write(f"**Content-Type:** {resp.headers.get('Content-Type', 'N/A')}")
    st.write(f"**Content Length:** {len(resp.content)} bytes")
    
    if resp.status_code == 200:
        # Coba berbagai format
        errors = {}
        
        # 1. Excel default
        try:
            df = pd.read_excel(io.BytesIO(resp.content))
            st.success(f"✅ Excel default: {len(df)} baris")
            st.dataframe(df.head(3))
        except Exception as e:
            errors['excel'] = str(e)[:100]
        
        # 2. Excel openpyxl
        if 'excel' in errors:
            try:
                df = pd.read_excel(io.BytesIO(resp.content), engine='openpyxl')
                st.success(f"✅ Excel openpyxl: {len(df)} baris")
                st.dataframe(df.head(3))
            except Exception as e:
                errors['openpyxl'] = str(e)[:100]
        
        # 3. CSV
        if 'openpyxl' in errors:
            try:
                df = pd.read_csv(io.BytesIO(resp.content))
                st.success(f"✅ CSV: {len(df)} baris")
                st.dataframe(df.head(3))
            except Exception as e:
                errors['csv'] = str(e)[:100]
        
        if not errors:
            st.success("Semua OK")
        else:
            st.error(f"Errors: {errors}")
            st.write("**Preview:**")
            st.code(resp.content[:200])
    else:
        st.error(f"HTTP {resp.status_code}")
        
except Exception as e:
    st.error(f"Error: {e}")
    
