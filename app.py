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
    '5412990': 'V-BELT Alternator',
    'RIMULA R4 X 15W-40': 'Oli Shell', 'WCL': 'Coolant',
}

KNOWN_CODES = list(PREVENTIVE_MAP.keys())

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
    
    # Filter hanya Preventive
    prev_rows = [r for r in rows if r['Jenis'] == 'Preventive']
    st.write(f"**Preventive rows: {len(prev_rows)}**")
    
    st.write("**Semua Preventive:**")
    for r in prev_rows:
        st.write(f"- `{r['Kode Material']}` | {r['Nama Material']} | Qty={r['Qty']} | Jenis={r['Jenis']}")
    
    # Group by
    st.write("---")
    st.write("**Setelah groupby:**")
    grouped = {}
    for r in prev_rows:
        key = (r['Kode Material'], r['Nama Material'], r['Primary Code'])
        if key not in grouped:
            grouped[key] = 0
        grouped[key] += r['Qty']
    
    for (kode, nama, pc), qty in sorted(grouped.items()):
        st.write(f"- `{kode}` | {nama} | Qty={qty}")

except Exception as e:
    st.error(f"Error: {e}")
