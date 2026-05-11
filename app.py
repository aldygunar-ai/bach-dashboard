import streamlit as st
import gspread
import re

st.set_page_config(page_title="Debug Merge Padang")
st.title("🔍 Debug Merge PADANG MANGGAR dengan M1")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

cl = get_client()

# Load M1
MASTER_PLTD_ID = '1FsaZyKs3DgJlyZkx5qqpBotNK8Z6C8GOrNeJv3I8AJA'
sh = cl.open_by_key(MASTER_PLTD_ID)

for ws in sh.worksheets():
    t = ws.title.strip().lower()
    if ('master' in t or 'mater' in t) and '1' in t:
        from gspread_dataframe import get_as_dataframe
        d = get_as_dataframe(ws, evaluate_formulas=True)
        d.columns = [str(c).strip() for c in d.columns]
        
        # Rename seperti di load_all
        d = d.rename(columns={d.columns[9]: 'pltd', d.columns[2]: 'kode_material', d.columns[10]: 'keb_pm', d.columns[11]: 'keb_aktual'})
        d['pltd'] = d['pltd'].astype(str).str.strip().str.upper()
        d['kode_material'] = d['kode_material'].astype(str).str.strip().str.upper()
        
        # Cari PADANG MANGGAR
        padang = d[d['pltd'] == 'PADANG MANGGAR']
        st.write(f"**PADANG MANGGAR di M1: {len(padang)} baris**")
        if not padang.empty:
            st.dataframe(padang[['pltd', 'kode_material', 'keb_pm', 'keb_aktual']])
        
        # Cek primary_code
        def get_primary_code(kode):
            k = str(kode).strip().upper()
            parts = re.split(r'\s*/\s*', k)
            return parts[0].strip() if parts else k
        
        d['primary_code'] = d['kode_material'].apply(get_primary_code)
        d['primary_code'] = d['primary_code'].str.strip().str.upper()
        
        st.write("---")
        st.write("**Primary codes untuk PADANG MANGGAR:**")
        padang_pc = d[d['pltd'] == 'PADANG MANGGAR'][['pltd', 'kode_material', 'primary_code', 'keb_aktual']]
        st.dataframe(padang_pc)
        
        # Simulasikan merge dengan data Padang Manggar dari debug sebelumnya
        st.write("---")
        st.write("**Simulasi merge dengan stok Padang Manggar:**")
        
        stok_padang = [
            ('2020PM V30-C', 0.0),
            ('3629140', 70.0),
            ('5412990', 0.0),
            ('AF872', 40.0),
            ('FS1006', 29.0),
            ('LF3325', 0.0),
            ('RIMULA R4 X 15W-40', 4.559),
            ('WCL', 1.551),
            ('WF2076', 0.0),
        ]
        
        for kode, qty in stok_padang:
            pc = get_primary_code(kode)
            m1_match = d[(d['pltd'] == 'PADANG MANGGAR') & (d['primary_code'] == pc)]
            if not m1_match.empty:
                keb = m1_match['keb_aktual'].values[0]
                sisa = round(qty / keb, 1) if keb > 0 else 0
                st.write(f"✅ `{kode}` (PC=`{pc}`) | Qty={qty} | Keb={keb} | Sisa={sisa}")
            else:
                st.write(f"❌ `{kode}` (PC=`{pc}`) | TIDAK MATCH di M1!")
