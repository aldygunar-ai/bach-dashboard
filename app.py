import streamlit as st
import gspread

st.set_page_config(page_title="Debug Gabungan")
st.title("🔍 Debug Sheet Gabungan")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

cl = get_client()
MASTER_GABUNGAN_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'

try:
    sh = cl.open_by_key(MASTER_GABUNGAN_ID)
    st.write(f"**Worksheets:** {[ws.title for ws in sh.worksheets()]}")
    
    # Coba semua sheet
    for ws in sh.worksheets():
        data = ws.get_all_values()
        st.write(f"**Sheet '{ws.title}':** {len(data)} baris")
        if len(data) >= 2:
            st.write(f"  Header: {data[0][:5]}...")
            st.write(f"  Baris 2: {data[1][:5]}...")
            st.write(f"  Baris 3: {data[2][:5]}..." if len(data) > 2 else "")
        st.write("---")
except Exception as e:
    st.error(f"Error: {e}")
