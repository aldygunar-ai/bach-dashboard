import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import plotly.express as px
import plotly.graph_objects as go
import gspread
from gspread_dataframe import get_as_dataframe
from gspread.exceptions import WorksheetNotFound
import re
import base64
import logging

# ======================== PAGE CONFIG ========================
st.set_page_config(
    page_title="Dashboard PLTD Bach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CSS ========================
st.markdown("""
<style>
    .main { background-color: #F5F7FA; }
    [data-testid="stSidebar"] { background-color: #0A2540 !important; }
    .sidebar-title {
        color: #FFFFFF; font-size: 20px; font-weight: 700; text-align: center;
        margin-bottom: 20px; padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    [data-testid="stSidebar"] label p { color: #CCCCCC !important; font-weight: 500 !important; }
    [data-testid="stSidebarNav"] span { color: #FFFFFF !important; font-weight: 600 !important; }
    [data-testid="stSidebarNav"] a { color: #FFFFFF !important; }
    [data-testid="stSidebar"] button svg, button[kind="headerNoSpacing"] svg { fill: #FFFFFF !important; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #0A2540; }
    .stPlotlyChart { background-color: #FFFFFF; border-radius: 10px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    [data-testid="stDataFrame"] { background-color: #FFFFFF; border-radius: 10px; padding: 8px; }
    .stButton>button { background-color: #1F4E79; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #2A6DA1; color: white; }
</style>
""", unsafe_allow_html=True)

# ======================== DATA SOURCES ========================
PLTD_SHEETS = {
    'Pemaron':        '1HN-X9OhLTGo5Ieu2uzBa6VHh0UlFdGTiw56yOIX5VgI',
    'Mangoli':        '1agNRbhpUJRqsA91eDlDq49BKpbW5x3v-2DiAGlbdq9s',
    'Tayan':          '1_FUPGfUWbKFSfYJj4c6rlZDSYDXdL2LOCGG3g6w9vBo',
    'Timika':         '1SyaYeykle3Fg0FTQzXPzLhkoN60PC9GzygZkrnDY-04',
    'Bobong':         '1OGeGlQqwO2a4tbL_rS0x5b4guTIiIzVNXySUsbK4GMM',
    'Merawang':       '1WrNipP179XrvKjNIGjeNSnCz94_6IJQBf4pM-vO5OO8',
    'Air Anyir':      '10dCcXN574G_xGxsnaq7UmExsA7asbz_HTJPMo6oWN2o',
    'Padang Manggar': '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Krueng Raya':    '1u8nurDgXSRLCFB0p9YFv3x7i_8FDU0FZmsQK_yw4W4s',
    'Lueng Bata':     '1syFmB3cwN0FfYRBmjgYTshlFiZAXdvVDdcdZ-Xr_p6g',
    'Ulee Kareng':    '1BlhNGU1L6QJq3W2Qi7Vmp3aOdYNalACKJUwUUecDeoU',
    'Waena':          '10NKbFUi0SVh1784OQnSU0ULhWzL6_AK7XLY-8EgKbG8',
    'Sambelia':       '1-8uGvDwZnciEgAXBbogkYWdHQcEClcwuln-hbaR0UAc',
    'Timika 2':       '17FR17wxkeVgd0_GElV59ugetL8nutqiYwQRyY6FqIVE',
    'Wamena':         '14ieCIQwEXf4hZ-RsOeLIMyKi5qEJLtQBwTz35b9JXxs',
}
MASTER_SHEET_ID = '1aZZnnBjSybgzEgUECdLSCaPJ_rMKNHJmfGEwetOARbs'
SHAREPOINT_DELIVERY_URL = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQDpLV2xOcHmS51kfDxWqHQAAUHHovDCqOPtICGu3HUp6nc?download=1"
SHAREPOINT_PROJECT_OPS = SHAREPOINT_DELIVERY_URL
SHAREPOINT_PROJECT_DAS = "https://bachmulti-my.sharepoint.com/:x:/g/personal/prabawa_bachgroup_co_id/IQBxJHUjgIjQTooUQPRp14iZAUy5KIiRVxLFRW-z8X17lDY?download=1"

PREVENTIVE_CODES = {
    'LF3325', 'LF777', '2020PM V30-C', 'FS1006', 'WF2076', '3629140',
    'AF872', 'AF25278', 'AHO1135', '5413003', '3015257', '5412990',
    '5PK889', '21-3107', '25471145', '23PK2032', '21-3110', '25477108',
    'RIMULA R4 X 15W-40'
}

PLTD_COORDS = {
    'Pemaron': (-8.1647, 114.6824), 'Mangoli': (-1.8821, 125.3732),
    'Tayan': (-0.0324, 110.1022), 'Timika': (-4.5564, 136.8883),
    'Bobong': (-1.946, 124.388), 'Merawang': (-1.9508, 105.9643),
    'Air Anyir': (-1.9377, 106.1064), 'Padang Manggar': (-2.1429, 106.1419),
    'Krueng Raya': (5.6023, 95.5336), 'Lueng Bata': (5.5484, 95.3342),
    'Ulee Kareng': (5.5475, 95.3322), 'Waena': (-2.6062, 140.5637),
    'Sambelia': (-8.3973, 116.6729), 'Timika 2': (-4.5564, 136.8883),
    'Wamena': (-4.0922, 138.9447)
}

DURASI_KIRIM = {
    'Pemaron': 7, 'Mangoli': 14, 'Tayan': 10, 'Timika': 14,
    'Bobong': 14, 'Merawang': 5, 'Air Anyir': 5, 'Padang Manggar': 5,
    'Krueng Raya': 7, 'Lueng Bata': 7, 'Ulee Kareng': 7, 'Waena': 14,
    'Sambelia': 7, 'Timika 2': 14, 'Wamena': 21
}

PM_INTERVAL = {
    'LF3325': 400, 'LF777': 500, '2020PM V30-C': 400, 'FS1006': 500,
    'WF2076': 500, '3629140': 400, 'AF872': 400, 'AF25278': 400,
    'AHO1135': 500, '5413003': 500, '3015257': 500, '5412990': 500,
    '5PK889': 500, '21-3107': 500, '25471145': 500, '23PK2032': 500,
    '21-3110': 500, '25477108': 500, 'RIMULA R4 X 15W-40': 750
}
DEFAULT_PM_INTERVAL = 500

# ======================== CREDENTIAL FIXER ========================
def safe_credentials():
    """
    Membersihkan private_key dari Secrets agar valid PEM.
    Langkah:
    1. Ganti literal \n menjadi newline.
    2. Hapus semua karakter yang bukan bagian dari base64 atau newline.
    3. Pastikan header/footer PEM ada dan benar.
    """
    creds = dict(st.secrets["gcp_service_account"])
    pk = creds.get('private_key', '')
    if not pk:
        st.error("private_key tidak ditemukan di Secrets.")
        return creds

    # Step 1: Ubah literal \n menjadi newline sebenarnya
    # Terkadang TOML menyimpan \n sebagai dua karakter: backslash + n.
    # Kita ganti dua karakter "\" "n" menjadi satu newline.
    pk = pk.replace('\\n', '\n')

    # Step 2: Bersihkan karakter non-base64/newline
    # Biarkan hanya karakter A-Za-z0-9+/= dan newline
    allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n-')
    cleaned = ''.join(c if c in allowed_chars else '' for c in pk)

    # Step 3: Tambahkan header dan footer yang presisi
    header = '-----BEGIN PRIVATE KEY-----'
    footer = '-----END PRIVATE KEY-----'
    # Hapus header/footer yang mungkin sudah ada
    cleaned = cleaned.replace(header, '').replace(footer, '')
    # Hilangkan spasi/baris kosong
    cleaned = '\n'.join([line for line in cleaned.split('\n') if line.strip() != ''])

    # Gabungkan dengan header/footer, masing-masing di baris sendiri
    pk = header + '\n' + cleaned + '\n' + footer + '\n'
    # Pastikan tidak ada baris header/footer ganda
    pk = pk.replace(header + '\n' + header, header)
    pk = pk.replace(footer + '\n' + footer, footer)

    # Debug: Tampilkan 5 baris pertama (bisa dihapus nanti)
    logging.debug("Cleaned private key:\n" + "\n".join(pk.split('\n')[:5]))

    creds['private_key'] = pk
    return creds

@st.cache_resource
def get_gspread_client():
    """Buat client gspread dengan penanganan error."""
    try:
        credentials = safe_credentials()
        # Coba validasi langsung
        client = gspread.service_account_from_dict(credentials)
        # Test koneksi ringan (buka spreadsheet dummy, opsional)
        # client.open_by_key('any_valid_sheet_id')  # bisa diaktifkan untuk test
        return client
    except Exception as e:
        err_str = str(e)
        # Tampilkan pesan bantuan yang jelas
        st.error(f"""
        **Gagal autentikasi ke Google Sheets.**
        Error: `{err_str[:200]}...`

        Kemungkinan:
        - **Service Account belum diberi akses ke spreadsheet.**  
        - **Format private_key di Secrets bermasalah.**  

        **Cara memperbaiki:**
        1. Buka [Google Cloud Credentials](https://console.cloud.google.com/apis/credentials) dan pastikan service account `{st.secrets.get('gcp_service_account', {}).get('client_email', '?')}` ada.
        2. Download file JSON baru (jangan edit isinya).
        3. Di Streamlit Cloud > Manage App > Secrets, **hapus semua** lalu tempel file JSON persis seperti ini (jangan ada spasi ekstra):
        ```toml
        [gcp_service_account]
        type = "service_account"
        project_id = "my-project-bach-494704"
        private_key_id = "..."
        private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvA...\n-----END PRIVATE KEY-----\n"
        client_email = "..."
        ... (salin semua field)
