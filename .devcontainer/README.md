# Bach Dashboard - Monitoring Stok & Logistik PLTD

## Setup
1. **Clone repository** dan buat virtual environment.
2. Install dependensi: `pip install -r requirements.txt`
3. Buat service account Google Cloud dan aktifkan Google Sheets API.
4. Unduh JSON kredensial dan simpan isinya di Streamlit Secrets:
   ```toml
   # .streamlit/secrets.toml
   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "..."
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "..."
   client_x509_cert_url = "..."