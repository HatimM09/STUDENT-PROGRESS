import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. PAGE SETUP & THEME
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
    .stButton>button { background-color: #1e3a8a; color: gold; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. GOOGLE SHEETS CONNECTION
def get_sheet_connection():
    # Constructing the credentials dictionary
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
    return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1

try:
    sheet = get_sheet_connection()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# 3. APP LOGIC
if 'login_state' not in st.session_state:
    st.session_state.login_state = False
    st.session_state.user_type = None
    st.session_state.user_data = None

st.markdown("<h1>Sanah Rabea</h1>", unsafe_allow_html=True)

if not st.session_state.login_state:
    _, center, _ = st.columns([1, 1, 1])
    with center:
        role = st.selectbox("Role", ["Student", "Teacher", "Admin"])
        if role == "Student":
            code = st.text_input("Student Code")
            if st.button("Login"):
                df = pd.DataFrame(sheet.get_all_records())
                user = df[df['CODE'].astype(str) == code]
                if not user.empty:
                    st.session_state.login_state = True
                    st.session_state.user_type = "student"
                    st.session_state.user_data = user.iloc[0]
                    # Log activity in column 7
                    row = user.index[0] + 2
                    sheet.update_cell(row, 7, datetime.now().strftime("%H:%M %d-%m-%Y"))
                    st.rerun()
        elif role == "Teacher":
            pw = st.text_input("Password", type="password")
            if st.button("Login") and pw == st.secrets["TEACHER_PASSWORD"]:
                st.session_state.login_state = True
                st.session_state.user_type = "teacher"
                st.rerun()
        elif role == "Admin":
            pw = st.text_input("Password", type="password")
            if st.button("Login") and pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.login_state = True
                st.session_state.user_type = "admin"
                st.rerun()
else:
    if st.sidebar.button("Logout"):
        st.session_state.login_state = False
        st.rerun()

    # STUDENT DASHBOARD
    if st.session_state.user_type == "student":
        u = st.session_state.user_data
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(u['PHOTO_URL'] if u['PHOTO_URL'] else "https://via.placeholder.com/150")
            st.subheader(u['NAME'])
        with c2:
            st.metric("Juz Level", u['JUZ'])
            marks = int(u['CURRENT_MARKS'])
            st.write(f"**Ikhtebaar Score:** {marks}%")
            st.progress(marks / 100)
            diff = int(u['CURRENT_MARKS']) - int(u['PREVIOUS_MARKS'])
            st.write(f"Progress vs Last: {'+' if diff >=0 else ''}{diff}%")

    # TEACHER DASHBOARD
    elif st.session_state.user_type == "teacher":
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df[['CODE', 'NAME', 'JUZ', 'CURRENT_MARKS']])
        with st.expander("Edit Student Progress"):
            s_code = st.selectbox("Select Student", df['CODE'].tolist())
            new_juz = st.number_input("Juz", 1, 30)
            new_marks = st.number_input("Marks", 0, 100)
            if st.button("Save"):
                row = df.index[df['CODE'] == s_code].tolist()[0] + 2
                old_m = df.loc[df['CODE'] == s_code, 'CURRENT_MARKS'].values[0]
                sheet.update_cell(row, 4, old_m) # Current to Previous
                sheet.update_cell(row, 3, new_juz)
                sheet.update_cell(row, 5, new_marks)
                st.success("Updated!")

    # ADMIN DASHBOARD
    elif st.session_state.user_type == "admin":
        df = pd.DataFrame(sheet.get_all_records())
        st.write("### Live Activity Logs")
        st.table(df[['NAME', 'LAST_LOGIN']])
        st.write("### Database Management")
        st.dataframe(df)
