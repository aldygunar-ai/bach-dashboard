import streamlit as st
import gspread

st.set_page_config(page_title="Debug Padang Manggar")
st.title("🔍 Debug Spreadsheet Padang Manggar")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

cl = get_client()

# Padang Manggar BARU
sid = '1IH0prF5h5rOtV2TbRbRI4wuj5PbafbLbAesUIfrYihM'

try:
    sh = cl.open_by_key(sid)
    data = sh.sheet1.get_all_values()
    st.write(f"**Total baris:** {len(data)}")
    
    if len(data) >= 2:
        # Header
        st.write("**Header (baris 1):**")
        st.write(data[0])
        st.write(f"Jumlah kolom: {len(data[0])}")
        
        # 5 baris pertama
        st.write("**5 Baris pertama:**")
        for i, row in enumerate(data[1:6]):
            st.write(f"Baris {i+2}: C='{row[2] if len(row)>2 else ''}', D='{row[3] if len(row)>3 else ''}', I='{row[8] if len(row)>8 else ''}', K='{row[10] if len(row)>10 else ''}'")
        
        # Deteksi format
        header = [str(c).strip().lower() for c in data[0]]
        is_log = ('keluar' in ' '.join(header[:5]) and 'masuk' in ' '.join(header[:5]))
        st.write(f"**Format LOG:** {is_log}")
        
        if is_log:
            # Cek material unik
            material_stok = {}
            for r in data[1:]:
                if len(r) <= 10: continue
                nama = r[8].strip() if len(r) > 8 else ''
                product_id = r[10].strip() if len(r) > 10 else ''
                qty_s = r[3].strip() if len(r) > 3 else '0'
                if not nama: continue
                try:
                    qty = float(qty_s.replace(',', ''))
                except:
                    qty = 0.0
                key = nama.strip().lower()
                material_stok[key] = {'nama': nama, 'pid': product_id, 'qty': qty}
            
            st.write(f"**Material unik:** {len(material_stok)}")
            for key, val in sorted(material_stok.items()):
                st.write(f"- `{val['pid']}` | {val['nama']} | Qty={val['qty']}")
        
except Exception as e:
    st.error(f"Error: {e}")
