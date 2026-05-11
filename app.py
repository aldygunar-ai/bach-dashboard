import streamlit as st
import gspread
import re

st.set_page_config(page_title="Debug Material LOG")
st.title("🔍 Material dari Format LOG")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

PREVENTIVE_MAP = {
    'LF3325': 'Oil Filter', 'LF777': 'Oil Filter By pass',
    '2020PM V30-C': 'Element Water Separator', 'FS1006': 'Fuel Filter',
    'WF2076': 'Water Filter', '3629140': 'Cylinder head cover gasket',
    'AF872': 'Air Filter Element', 'AF25278': 'Air Filter Element',
    'AHO1135': 'Air Filter Element (Aksa)', '5413003': 'V-BELT Fan Radiator',
    '3015257': 'V-BELT (Aksa)', '5412990': 'V-BELT Alternator',
    '5PK889': 'V-BELT Alternator', '23PK2032': 'V-BELT Fan Radiator',
    'RIMULA R4 X 15W-40': 'Oli Shell', 'WCL': 'Coolant',
}

SHEETS = {
    'Merawang': '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir': '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
}

cl = get_client()

for nama, sid in SHEETS.items():
    st.subheader(f"📋 {nama}")
    try:
        sh = cl.open_by_key(sid)
        data = sh.sheet1.get_all_values()
        
        # Kumpulkan material unik dengan stok terakhir
        material_stok = {}
                        for r in data[1:]:
                    if len(r) <= max(i_nama, i_kode, i_qty):
                        continue
                    nama = r[i_nama].strip() if i_nama < len(r) else ''
                    product_id = r[i_kode].strip() if i_kode < len(r) else ''
                    qty_s = r[i_qty].strip() if i_qty < len(r) else ''
                    
                    # Ekstrak kode simpel dari PRODUCT IDENTIFICATION
                    kode = extract_kode_from_product_id(product_id, nama)
            
            if not nama_mat:
                continue
            if '#REF' in qty_s.upper():
                continue
            
            try:
                qty = float(qty_s.replace(',', ''))
            except:
                qty = 0.0
            
            key = nama_mat.strip().lower()
            material_stok[key] = {
                'nama': nama_mat,
                'kode': kode,
                'qty': qty
            }
        
        st.write(f"Total material unik: {len(material_stok)}")
        st.write("**Daftar Material:**")
        
        for key, val in sorted(material_stok.items()):
            kode = val['kode']
            qty = val['qty']
            nama = val['nama']
            
            # Cek apakah kode ada di PREVENTIVE_MAP
            kode_upper = kode.upper().strip()
            is_prev = False
            matched_name = ''
            
            for pk, pn in PREVENTIVE_MAP.items():
                if pk.upper() in kode_upper or kode_upper in pk.upper():
                    is_prev = True
                    matched_name = pn
                    break
            
            st.write(f"- `{kode}` | {nama} | Qty={qty} | Prev={is_prev} | Match={matched_name}")
        
    except Exception as e:
        st.error(f"Error: {e}")
    st.markdown("---")
