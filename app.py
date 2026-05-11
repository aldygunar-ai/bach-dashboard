import streamlit as st
import gspread

st.set_page_config(page_title="Debug Padang Manggar v3")
st.title("🔍 Material dari Format Padang Manggar")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

KNOWN_CODES = [
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076',
    '3629140', 'AF872', 'AF25278', 'AHO1135',
    '5413003', '3015257', '5412990', '5PK889', '21-3107', '25471145',
    '23PK2032', '21-3110', '25477108', 'RIMULA R4 X 15W-40', 'WCL'
]

PREVENTIVE_MAP = {
    'LF3325': 'Oil Filter', 'LF777': 'Oil Filter By pass',
    '2020PM V30-C': 'Element Water Separator', 'FS1006': 'Fuel Filter',
    'WF2076': 'Water Filter', '3629140': 'Cylinder head cover gasket',
    'AF872': 'Air Filter Element', 'AF25278': 'Air Filter Element',
    'AHO1135': 'Air Filter Element (Aksa)',
    '5413003': 'V-BELT Fan Radiator', '3015257': 'V-BELT (Aksa)',
    '5412990': 'V-BELT Alternator', '5PK889': 'V-BELT Alternator',
    '23PK2032': 'V-BELT Fan Radiator', 'RIMULA R4 X 15W-40': 'Oli Shell',
    'WCL': 'Coolant',
}

cl = get_client()
sid = '1IH0prF5h5rOtV2TbRbRI4wuj5PbafbLbAesUIfrYihM'

try:
    sh = cl.open_by_key(sid)
    data = sh.sheet1.get_all_values()
    st.write(f"**Total baris:** {len(data)}")
    
    i_nama = 3
    i_qty = 10
    
    material_stok = {}
    for r in data[2:]:
        if len(r) <= max(i_nama, i_qty):
            continue
        nama = r[i_nama].strip() if i_nama < len(r) else ''
        qty_s = r[i_qty].strip() if i_qty < len(r) else '0'
        if not nama:
            continue
        try:
            qty = float(qty_s.replace(',', '')) if qty_s else 0.0
        except:
            qty = 0.0
        
        key = nama.strip().lower()
        if key not in material_stok:
            material_stok[key] = qty
    
    st.write(f"**Material unik:** {len(material_stok)}")
    st.write("---")
    
    matched = 0
    unmatched = 0
    
    for nama, qty in sorted(material_stok.items()):
        nama_upper = nama.upper()
        
        # Coba cari kode
        found_kode = None
        found_nama = None
        
        # Cek direct match di PREVENTIVE_MAP values
        for kode, preventive_nama in PREVENTIVE_MAP.items():
            if preventive_nama.upper() in nama_upper or nama_upper in preventive_nama.upper():
                found_kode = kode
                found_nama = preventive_nama
                break
        
        # Cek kata kunci
        if not found_kode:
            if 'OIL FILTER' in nama_upper and 'BY PASS' not in nama_upper:
                found_kode = 'LF3325'
                found_nama = 'Oil Filter'
            elif 'OIL FILTER BY PASS' in nama_upper or 'LF777' in nama_upper:
                found_kode = 'LF777'
                found_nama = 'Oil Filter By pass'
            elif 'WATER SEPARATOR' in nama_upper or '2020PM' in nama_upper:
                found_kode = '2020PM V30-C'
                found_nama = 'Element Water Separator'
            elif 'FUEL FILTER' in nama_upper or 'FS1006' in nama_upper:
                found_kode = 'FS1006'
                found_nama = 'Fuel Filter'
            elif 'WATER FILTER' in nama_upper or 'WF2076' in nama_upper:
                found_kode = 'WF2076'
                found_nama = 'Water Filter'
            elif 'GASKET' in nama_upper or '3629140' in nama_upper:
                found_kode = '3629140'
                found_nama = 'Cylinder head cover gasket'
            elif 'AIR FILTER' in nama_upper and 'AF872' in nama_upper:
                found_kode = 'AF872'
                found_nama = 'Air Filter Element'
            elif 'AIR FILTER' in nama_upper and 'AF25278' in nama_upper:
                found_kode = 'AF25278'
                found_nama = 'Air Filter Element'
            elif 'AHO1135' in nama_upper:
                found_kode = 'AHO1135'
                found_nama = 'Air Filter Element (Aksa)'
            elif 'V-BELT FAN' in nama_upper or '5413003' in nama_upper:
                found_kode = '5413003'
                found_nama = 'V-BELT Fan Radiator'
            elif 'V-BELT (AKSA)' in nama_upper or '3015257' in nama_upper:
                found_kode = '3015257'
                found_nama = 'V-BELT (Aksa)'
            elif 'V-BELT ALTERNATOR' in nama_upper or '5412990' in nama_upper:
                found_kode = '5412990'
                found_nama = 'V-BELT Alternator'
            elif 'OLI SHELL' in nama_upper or 'RIMULA' in nama_upper:
                found_kode = 'RIMULA R4 X 15W-40'
                found_nama = 'Oli Shell'
            elif 'COOLANT' in nama_upper or 'COLLANT' in nama_upper or 'WCL' in nama_upper:
                found_kode = 'WCL'
                found_nama = 'Coolant'
        
        if found_kode:
            matched += 1
            st.markdown(f"✅ `{nama}` → **{found_kode}** ({found_nama}) | Qty={qty}")
        else:
            unmatched += 1
            st.markdown(f"❌ `{nama}` | Qty={qty}")
    
    st.write("---")
    st.metric("Match", matched)
    st.metric("Unmatch", unmatched)
    
except Exception as e:
    st.error(f"Error: {e}")
