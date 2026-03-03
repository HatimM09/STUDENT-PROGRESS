import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. THEME & HEADER
st.set_page_config(page_title="Sanah Rabea", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: url("https://www.elearningquran.com/imgs/MAZLogo.png") no-repeat center;
        background-size: 400px;
        background-color: white;
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        border: 3px solid #1e3a8a;
        padding: 30px;
    }
    h1 { color: #1e3a8a; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 2. DATABASE CONNECTION (STRICT VERSION)
def get_sheet():
    try:
        info = {
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
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        # Try to open the sheet
        return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        return None

# Initialize connection
sheet = get_sheet()

# 3. SAFETY CHECK
if sheet is None:
    st.warning("Please check your Google Sheet sharing settings and Secrets.")
    st.stop() # Prevents the AttributeError

# 4. APP LOGIC
st.markdown("<h1>Sanah Rabea</h1>", unsafe_allow_html=True)

if 'login' not in st.session_state:
    st.session_state.login = False
    st.session_state.user_type = None

if not st.session_state.login:
    _, col, _ = st.columns([1,1,1])
    with col:
        role = st.selectbox("Login as", ["Student", "Teacher", "Admin"])
        
        if role == "Student":
            code = st.text_input("Student Code")
            if st.button("Login"):
                data = sheet.get_all_records() # Now safe to call
                df = pd.DataFrame(data)
                user = df[df['CODE'].astype(str) == code]
                if not user.empty:
                    st.session_state.login = True
                    st.session_state.user_type = "student"
                    st.session_state.user_info = user.iloc[0]
                    # Log activity
                    row_idx = user.index[0] + 2
                    sheet.update_cell(row_idx, 7, datetime.now().strftime("%Y-%m-%d %H:%M"))
                    st.rerun()
                else: st.error("Invalid Code")

def get_sheet():
    try:
        # Since we used ''' in secrets, the key is already clean!
        info = {
            "type": st.secrets["G_TYPE"],
            "project_id": st.secrets["G_PROJECT_ID"],
            "private_key_id": st.secrets["G_PRIVATE_KEY_ID"],
            "private_key": st.secrets["G_PRIVATE_KEY"], # No .replace needed here
            "client_email": st.secrets["G_CLIENT_EMAIL"],
            "client_id": st.secrets["G_CLIENT_ID"],
            "auth_uri": st.secrets["G_AUTH_URI"],
            "token_uri": st.secrets["G_TOKEN_URI"],
            "auth_provider_x509_cert_url": st.secrets["G_AUTH_CERT_URL"],
            "client_x509_cert_url": st.secrets["G_CLIENT_CERT_URL"]
        }
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        return None
        # ... (Add Teacher/Admin Login here) ...

