import streamlit as st
import gspread
import re

st.set_page_config(page_title="Debug Padang Final")
st.title("🔍 Debug Row Output Padang Manggar (dengan extract_kode_from_product_id)")

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

KNOWN_CODES = list(PREVENTIVE_MAP.keys()) + ['5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108']

def extract_kode_from_product_id(product_id, nama_material):
    pid = str(product_id).upper().strip()
    nama = str(nama_material).upper().strip()
    gabungan = pid + ' ' + nama

    PID_TO_CODE = {
        'DP.ELE.PAR.001----': '2020PM V30-C',
        'DP.FIL.FLE.001----': 'FS1006',
        'DP.CF.FLE.001----': 'WF2076',
        'DP.OIL.FLE.009----': 'LF777',
    }
    if pid in PID_TO_CODE:
        return PID_TO_CODE[pid]

    SKIP_LIST = [
        'FS.SO.VDO.001----', 'AKSESORIS PART', 'ES.SKU.POL', 'ASSET',
        'VARISTOR----', '10 MICRON', '5 MICRON', 'AMPERE METER',
        'AVR D350', 'BATRAI ACCU', 'CONTROL GOVERNOR', 'COS PHI METER',
        'DINAMO AMPERE', 'ELEMENT FILTER 20', 'ELEMENT FILTER WIREMESH',
        'FILTER SOLAR', 'HZ METER', 'INJECTOR', 'MODUL', 'MPU',
        'MV FUSE LINK', 'PUSH ROD', 'RACOR FILTER', 'RELAY MY2',
        'RELAY MY4', 'SEAL MAIN FILTER', 'SHOCK ABSORBER', 'SOCKET RELAY',
        'SOLENOID', 'STC (FUEL', 'UVR ABB', 'VALVE PUSH ROD',
        'VOLT METER', 'V BELT',
    ]
    for skip in SKIP_LIST:
        if skip in nama:
            return None

    if 'OIL FILTER' in nama and 'BY PASS' not in nama:
        return 'LF3325'
    if 'OIL FILTER BY PASS' in nama:
        return 'LF777'
    if 'WATER SEPARATOR' in nama or 'RACOR 2020PM' in nama:
        return '2020PM V30-C'
    if 'FUEL FILTER' in nama or 'ELEMENT FUEL FILTER' in nama:
        return 'FS1006'
    if 'WATER FILTER' in nama:
        return 'WF2076'
    if 'GASKET' in nama:
        return '3629140'
    if 'AIR FILTER' in nama and 'ELEMENT' in nama:
        return 'AF872'
    if 'AIR FILTER' in nama and 'AHO1135' in nama:
        return 'AHO1135'
    if 'V-BELT FAN' in nama or 'V BELT FAN' in nama:
        return '5413003'
    if 'V-BELT (AKSA)' in nama or 'V BELT AKSA' in nama:
        return '3015257'
    if 'V-BELT ALTERNATOR' in nama or 'V BELT ALTERNATOR' in nama:
        return '5412990'
    if 'OLI SHELL' in nama or 'RIMULA' in nama:
        return 'RIMULA R4 X 15W-40'
    if 'COOLANT' in nama or 'COLLANT' in nama:
        return 'WCL'

    for kode in KNOWN_CODES:
        pattern = r'(?:^|[-/\s])' + re.escape(kode) + r'(?:$|[-/\s])'
        if re.search(pattern, gabungan):
            return kode

    return product_id

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
    if 'oli shell' in nama_lower:
        if 'ibc' in nama_lower:
            return 'Oli Shell (IBC)'
        return 'Oli Shell'
    return nama

cl = get_client()
sid = '1IH0prF5h5rOtV2TbRbRI4wuj5PbafbLbAesUIfrYihM'

try:
    sh = cl.open_by_key(sid)
    data = sh.sheet1.get_all_values()

    header_row = 0
    for i in range(min(3, len(data))):
        row_check = data[i]
        if len(row_check) > 3:
            kolom_c = str(row_check[2]).strip().lower()
            kolom_d = str(row_check[3]).strip().lower()
            if kolom_c == 'no' and 'matrial' in kolom_d:
                header_row = i
                break

    st.write(f"**Header row:** {header_row}")

    i_nama = 3
    i_qty = 10

    rows = []
    skipped = 0
    for r in data[header_row + 1:]:
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

        kode = extract_kode_from_product_id(nama, nama)
        if kode is None:
            skipped += 1
            continue

        nama_normal = norm(kode, nama)
        jenis = 'Preventive' if is_prev(kode) else 'Corrective'
        primary = get_primary_code(kode)

        rows.append((kode, nama_normal, qty, primary, jenis))

    st.write(f"**Total rows: {len(rows)} | Skipped: {skipped}**")

    non_zero = [r for r in rows if r[2] > 0]
    st.write(f"**Rows Qty > 0: {len(non_zero)}**")

    prev_rows = [r for r in rows if r[4] == 'Preventive']
    st.write(f"**Preventive: {len(prev_rows)}**")

    prev_nonzero = [r for r in prev_rows if r[2] > 0]
    st.write(f"**Preventive Qty > 0: {len(prev_nonzero)}**")

    if prev_nonzero:
        st.write("---")
        st.write("### ✅ Preventive non-zero (akan masuk dashboard):")
        for r in prev_nonzero:
            st.write(f"- `{r[0]}` | {r[1]} | Qty={r[2]} | Primary={r[3]}")

        st.write("---")
        st.write("### 📊 Setelah Groupby:")
        grouped = {}
        for r in prev_nonzero:
            key = (r[0], r[1], r[3])
            if key not in grouped:
                grouped[key] = 0
            grouped[key] += r[2]

        for (kode, nama, pc), qty in sorted(grouped.items()):
            st.write(f"- `{kode}` | {nama} | Qty={qty} | Primary={pc}")
    else:
        st.error("❌ TIDAK ADA PREVENTIVE DENGAN QTY > 0!")
        st.write("**Semua rows:**")
        for r in rows:
            st.write(f"- `{r[0]}` | {r[1]} | Qty={r[2]} | Jenis={r[4]}")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
