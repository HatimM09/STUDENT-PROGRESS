import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

def get_sheet():
    # Reconstruct the credentials from individual simple secrets
    creds_dict = {
        "type": st.secrets["G_TYPE"],
        "project_id": st.secrets["G_PROJECT_ID"],
        "private_key_id": st.secrets["G_PRIVATE_KEY_ID"],
        "private_key": st.secrets["G_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": st.secrets["G_CLIENT_EMAIL"],
        "client_id": st.secrets["G_CLIENT_ID"],
        "auth_uri": st.secrets["G_AUTH_URI"],
        "token_uri": st.secrets["G_TOKEN_URI"],
        "auth_provider_x509_cert_url": st.secrets["G_AUTH_CERT_URL"],
        "client_x509_cert_url": st.secrets["G_CLIENT_CERT_URL"]
    }
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1

# Run the connection
try:
    sheet = get_sheet()
    st.success("Connected to Google Sheets!")
except Exception as e:
    st.error(f"Failed: {e}")
