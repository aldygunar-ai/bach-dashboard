import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound, APIError
import traceback
import json

# ======================== PAGE CONFIG ========================
st.set_page_config(
    page_title="Dashboard PLTD Bach (DEBUG)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CSS (sederhana) ========================
st.markdown("""
<style>
    .main { background-color: #F5F7FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    [data-testid="stSidebarNav"] span { color: #FFFFFF !important; font-weight: 600 !important; }
    [data-testid="stSidebarNav"] a { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ======================== DATA SOURCES ========================
PLTD_SHEETS = {
    'Pemaron':        '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli':        '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan':          '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika':         '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    # tambahkan sisanya jika perlu, untuk debug kita pakai beberapa saja
}
MASTER_SHEET_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'

# ======================== FUNGSI DIAGNOSTIK ========================
def debug_credentials():
    """Mengembalikan string informasi tentang kredensial."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
    except Exception as e:
        return f"❌ Secrets 'gcp_service_account' tidak ditemukan. Error: {e}"

    # Sembunyikan data sensitif
    safe = {}
    for k, v in creds.items():
        if 'private_key' in k:
            safe[k] = v[:30] + '...' if v else '(kosong)'
        else:
            safe[k] = v
    info = "**Isi Secrets (parsial):**\n```\n" + json.dumps(safe, indent=2) + "\n```\n"

    # Cek format private_key
    pk = creds.get('private_key', '')
    if not pk:
        info += "❌ private_key kosong.\n"
    else:
        # Ganti \n untuk pengecekan
        pk_check = pk.replace('\\n', '\n')
        if '-----BEGIN PRIVATE KEY-----' not in pk_check:
            info += "❌ private_key tidak memiliki header BEGIN PRIVATE KEY.\n"
        elif '-----END PRIVATE KEY-----' not in pk_check:
            info += "❌ private_key tidak memiliki footer END PRIVATE KEY.\n"
        else:
            # Hitung jumlah baris di dalamnya
            lines = [l for l in pk_check.split('\n') if l.strip() and '-----' not in l]
            info += f"✅ private_key memiliki header/footer. Jumlah baris data: {len(lines)} (seharusnya 27-28 untuk RSA 2048).\n"
    return info

def test_sheets_connection():
    """Coba koneksi ke satu spreadsheet untuk menguji hak akses."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
        # Bersihkan private key seperti biasa
        pk = creds.get('private_key', '')
        if pk:
            pk = pk.replace('\\n', '\n')
            creds['private_key'] = pk
        client = gspread.service_account_from_dict(creds)
        # Coba buka spreadsheet PLTD pertama
        sheet_id = list(PLTD_SHEETS.values())[0]
        sh = client.open_by_key(sheet_id)
        ws = sh.sheet1
        title = ws.title
        return f"✅ Berhasil membuka spreadsheet `{sh.title}` (sheet `{title}`). Service account memiliki akses."
    except APIError as e:
        tb = traceback.format_exc()
        return f"❌ APIError: {str(e)[:300]}\n\nTraceback:\n```\n{tb[-500:]}\n```"
    except SpreadsheetNotFound:
        return "❌ Spreadsheet tidak ditemukan. Apakah Service Account sudah diundang ke spreadsheet sebagai editor?"
    except Exception as e:
        tb = traceback.format_exc()
        return f"❌ Gagal dengan error: {str(e)[:300]}\n\nTraceback:\n```\n{tb[-500:]}\n```"

# ======================== HALAMAN DEBUG ========================
st.title("⚡ Diagnostik Koneksi Google Sheets")

st.markdown("### 1. Informasi Kredensial")
st.markdown(debug_credentials())

st.markdown("### 2. Uji Koneksi ke Spreadsheet")
if st.button("🔍 Tes Koneksi Sekarang", use_container_width=True):
    with st.spinner("Menghubungi Google Sheets..."):
        hasil = test_sheets_connection()
        st.markdown(hasil)

st.markdown("---")
st.info("""
**Cara membaca hasil:**
- Jika berhasil, aplikasi siap digunakan. Klik tombol di bawah untuk melanjutkan ke dashboard.
- Jika gagal dengan `APIError`, cek apakah `private_key` di Secrets sudah benar (masih ada `\n` literal atau tidak).
- Jika gagal dengan `SpreadsheetNotFound`, buka Google Sheet lalu bagikan ke `client_email` yang tercantum di atas (sebagai Editor).
""")

if st.button("🚀 Lanjut ke Dashboard (jika sudah OK)"):
    st.switch_page("pages/home")
