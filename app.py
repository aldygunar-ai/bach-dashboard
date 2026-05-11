import streamlit as st
import gspread
import re

st.set_page_config(page_title="Debug Padang Final")
st.title("🔍 Debug Row Output Padang Manggar")

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
    'AHO1135': 'Air Filter Element (Aksa)',
    '5413003': 'V-BELT Fan Radiator', '3015257': 'V-BELT (Aksa)',
    '5412990': 'V-BELT Alternator', '5PK889': 'V-BELT Alternator',
    '23PK2032': 'V-BELT Fan Radiator', 'RIMULA R4 X 15W-40': 'Oli Shell',
    'WCL': 'Coolant',
}

def extract_kode(nama):
    """Extract kode dari nama material"""
    nama_upper = nama.upper()
    
    if 'OIL FILTER' in nama_upper and 'BY PASS' not in nama_upper and 'LF777' not in nama_upper:
        return 'LF3325'
    if 'OIL FILTER BY PASS' in nama_upper or 'LF777' in nama_upper:
        return 'LF777'
    if 'WATER SEPARATOR' in nama_upper or '2020PM' in nama_upper or 'RACOR' in nama_upper:
        return '2020PM V30-C'
    if 'FUEL FILTER' in nama_upper or 'FS1006' in nama_upper or 'ELEMENT FUEL FILTER' in nama_upper:
        return 'FS1006'
    if 'WATER FILTER' in nama_upper or 'WF2076' in nama_upper:
        return 'WF2076'
    if 'GASKET' in nama_upper or '3629140' in nama_upper:
        return '3629140'
    if 'AIR FILTER' in nama_upper and 'AF872' in nama_upper:
        return 'AF872'
    if 'AIR FILTER' in nama_upper and 'AF25278' in nama_upper:
        return 'AF25278'
    if 'AIR FILTER' in nama_upper and 'AHO1135' in nama_upper:
        return 'AHO1135'
    if 'AIR FILTER' in nama_upper and 'ELEMENT' in nama_upper:
        return 'AF872'
    if 'V-BELT FAN' in nama_upper or 'V BELT FAN' in nama_upper:
        return '5413003'
    if 'V-BELT (AKSA)' in nama_upper or 'V BELT AKSA' in nama_upper or '3015257' in nama_upper:
        return '3015257'
    if 'V-BELT ALTERNATOR' in nama_upper or 'V BELT ALTERNATOR' in nama_upper or '5412990' in nama_upper:
        return '5412990'
    if 'OLI SHELL' in nama_upper or 'RIMULA' in nama_upper:
        return 'RIMULA R4 X 15W-40'
    if 'COOLANT' in nama_upper or 'COLLANT' in nama_upper or 'WCL' in nama_upper:
        return 'WCL'
    
    return nama

def get_primary_code(kode):
    k = str(kode).strip().upper()
    parts = re.split(r'\s*/\s*', k)
    return parts[0].strip() if parts else k

def is_prev(kode):
    k = str(kode).strip().upper()
    for part in re.split(r'\s*/\s*', k):
        if part.strip() in PREVENTIVE_MAP:
            return True
    return k in PREVENTIVE_MAP

def norm(kode, nama):
    k = str(kode).strip().upper()
    nama_lower = str(nama).strip().lower()
    
    for pk, pn in PREVENTIVE_MAP.items():
        if k == pk.upper():
            if pk.upper() == 'RIMULA R4 X 15W-40':
                if 'ibc' in nama_lower:
                    return 'Oli Shell (IBC)'
                elif 'drum' in nama_lower:
                    return 'Oli Shell (Drum)'
            return pn
    
    if 'oil filter' in nama_lower and 'by pass' not in nama_lower:
        return 'Oil Filter'
    if 'oil filter by pass' in nama_lower:
        return 'Oil Filter By pass'
    if 'air filter' in nama_lower and 'element' in nama_lower:
        return 'Air Filter Element'
    if 'water separator' in nama_lower or 'racor' in nama_lower:
        return 'Element Water Separator'
    if 'fuel filter' in nama_lower:
        return 'Fuel Filter'
    if 'water filter' in nama_lower:
        return 'Water Filter'
    if 'gasket' in nama_lower:
        return 'Cylinder head cover gasket'
    if 'coolant' in nama_lower or 'collant' in nama_lower:
        return 'Coolant'
    if 'oli shell' in nama_lower or 'rimula' in nama_lower:
        if 'ibc' in nama_lower:
            return 'Oli Shell (IBC)'
        return 'Oli Shell'
    
    return nama

cl = get_client()
sid = '1IH0prF5h5rOtV2TbRbRI4wuj5PbafbLbAesUIfrYihM'

try:
    sh = cl.open_by_key(sid)
    data = sh.sheet1.get_all_values()
    
    i_nama = 3
    i_qty = 10
    
    rows = []
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
        
        kode = extract_kode(nama)
        nama_normal = norm(kode, nama)
        jenis = 'Preventive' if is_prev(kode) else 'Corrective'
        primary = get_primary_code(kode)
        
        rows.append({
            'PLTD': 'PADANG MANGGAR',
            'Kode Material': kode,
            'Nama Material': nama_normal,
            'Qty': qty,
            'Primary Code': primary,
            'Jenis': jenis,
        })
    
    st.write(f"**Total rows: {len(rows)}**")
    
    prev_rows = [r for r in rows if r['Jenis'] == 'Preventive']
    st.write(f"**Preventive rows: {len(prev_rows)}**")
    
    st.write("**Semua Preventive:**")
    for r in prev_rows:
        st.write(f"- `{r['Kode Material']}` | {r['Nama Material']} | Qty={r['Qty']} | Primary={r['Primary Code']}")
    
    st.write("---")
    st.write("**Setelah groupby (seperti di load_all):**")
    grouped = {}
    for r in prev_rows:
        key = (r['Kode Material'], r['Nama Material'], r['Primary Code'])
        if key not in grouped:
            grouped[key] = 0
        grouped[key] += r['Qty']
    
    for (kode, nama, pc), qty in sorted(grouped.items()):
        st.write(f"- `{kode}` | {nama} | Primary={pc} | Qty={qty}")
    
    if len(prev_rows) == 0:
        st.error("TIDAK ADA PREVENTIVE ROWS! Ini masalahnya.")
        st.write("**Semua rows (termasuk Corrective):**")
        for r in rows:
            st.write(f"- `{r['Kode Material']}` | {r['Nama Material']} | Qty={r['Qty']} | Jenis={r['Jenis']}")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
