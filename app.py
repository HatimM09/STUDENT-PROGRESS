import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ... (rest of your page setup and CSS here) ...

def get_sheet_connection():
    try:
        # Load the entire JSON from one secret
        creds_json = json.loads(st.secrets["GOOGLE_JSON"])
        
        # Scope for Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Authorize
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        
        return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1
    except Exception as e:
        st.error(f"Critical Connection Error: {e}")
        st.stop()

# Initialize the app
sheet = get_sheet_connection()
st.success("Connected to Sanah Rabea Database!")
