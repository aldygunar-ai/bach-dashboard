import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe

st.set_page_config(page_title="Debug M1")
st.title("Debug M1 Columns")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

cl = get_client()
sh = cl.open_by_key('1FsaZyKs3DgJlyZkx5qqpBotNK8Z6C8GOrNeJv3I8AJA')

for ws in sh.worksheets():
    t = ws.title.strip().lower()
    if 'master' in t and '1' in t:
        d = get_as_dataframe(ws, evaluate_formulas=True)
        d.columns = [str(c).strip() for c in d.columns]
        
        st.subheader(f"Sheet: {ws.title}")
        st.write(f"Jumlah kolom: {len(d.columns)}")
        st.write("### Nama Kolom:")
        for i, c in enumerate(d.columns):
            st.write(f"Index {i}: `{c}`")
        
        st.write("### 5 Baris Pertama:")
        st.dataframe(d.head())
        
        st.write("### Sample kolom index 9, 10, 11:")
        if len(d.columns) > 11:
            st.write(f"Col 9: {d.iloc[:3, 9].tolist()}")
            st.write(f"Col 10: {d.iloc[:3, 10].tolist()}")
            st.write(f"Col 11: {d.iloc[:3, 11].tolist()}")
