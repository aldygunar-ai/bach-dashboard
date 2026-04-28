import streamlit as st
import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
import traceback
import json

st.set_page_config(page_title="Debug Google Sheets", layout="wide")
st.title("🔍 Debug Koneksi Google Sheets")

st.markdown("### 1. Cek Kredensial")
try:
    creds = dict(st.secrets["gcp_service_account"])
    st.success("✅ Secrets `gcp_service_account` ditemukan.")
    # Tampilkan info aman
    safe_creds = {k: (v[:40]+'...' if 'private_key' in k else v) for k, v in creds.items()}
    st.json(safe_creds)
except Exception as e:
    st.error(f"❌ Secrets tidak ditemukan: {e}")
    st.stop()

# Perbaiki private key
pk = creds.get('private_key', '')
if pk:
    pk = pk.replace('\\n', '\n')
    creds['private_key'] = pk
    st.success("✅ private_key berhasil diformat.")
else:
    st.error("❌ private_key kosong.")
    st.stop()

st.markdown("### 2. Uji Koneksi ke Spreadsheet")
sheet_id = st.text_input("Masukkan ID spreadsheet (dari URL) yang sudah dibagikan ke service account")

if st.button("Tes Buka Spreadsheet") and sheet_id:
    try:
        client = gspread.service_account_from_dict(creds)
        sh = client.open_by_key(sheet_id.strip())
        st.success(f"✅ Berhasil membuka spreadsheet: `{sh.title}`")
        # Tampilkan sheet yang tersedia
        worksheets = sh.worksheets()
        st.write("Sheet yang tersedia:")
        for ws in worksheets:
            st.write(f"- {ws.title}")
        # Coba baca data dari sheet pertama
        ws = sh.sheet1
        data = ws.get_all_values()
        st.write(f"Baris data di sheet pertama: {len(data)}")
        if data:
            st.dataframe(data[:5])  # tampilkan 5 baris pertama
    except APIError as e:
        st.error(f"❌ APIError: {e}")
    except SpreadsheetNotFound:
        st.error("❌ Spreadsheet tidak ditemukan. Periksa ID.")
    except Exception as e:
        st.error(f"❌ Error: {e}\n\n```{traceback.format_exc()}```")
