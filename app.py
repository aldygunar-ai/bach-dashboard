import streamlit as st
import gspread

st.set_page_config(page_title="Debug Sheet")
st.title("🔍 Debug Isi Spreadsheet PLTD")

@st.cache_resource
def get_client():
    c = dict(st.secrets["gcp_service_account"])
    if c.get('private_key'):
        c['private_key'] = c['private_key'].replace('\\n', '\n')
    return gspread.service_account_from_dict(c)

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
        st.write(f"Total baris: {len(data)}")
        
        if len(data) >= 2:
            # Tampilkan header
            st.write("**Header (baris 1):**")
            st.write(data[0])
            
            # Tampilkan 5 baris pertama
            st.write("**5 Baris pertama data:**")
            for i, row in enumerate(data[1:6]):
                st.write(f"Baris {i+2}: kolom C='{row[2] if len(row)>2 else ''}', kolom D='{row[3] if len(row)>3 else ''}', kolom I='{row[8] if len(row)>8 else ''}'")
            
            # Hitung berapa yang akan valid menurut fungsi is_valid
            valid = 0
            invalid_nama_kosong = 0
            invalid_nama_angka = 0
            invalid_kolom_pendek = 0
            
            for r in data[1:]:
                if len(r) < 9:
                    invalid_kolom_pendek += 1
                    continue
                nama = r[2].strip() if len(r) > 2 else ''
                kode = r[3].strip() if len(r) > 3 else ''
                
                if not nama:
                    invalid_nama_kosong += 1
                elif nama.replace('.','').replace(',','').isdigit():
                    invalid_nama_angka += 1
                else:
                    valid += 1
            
            st.write(f"✅ Valid: {valid}")
            st.write(f"❌ Nama kosong: {invalid_nama_kosong}")
            st.write(f"❌ Nama angka: {invalid_nama_angka}")
            st.write(f"❌ Kolom < 9: {invalid_kolom_pendek}")
            
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
