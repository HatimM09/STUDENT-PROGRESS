import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Sanah Rabea", page_icon="🌙", layout="wide")

# --- CUSTOM THEME & BACKGROUND ---
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("https://www.elearningquran.com/imgs/MAZLogo.png");
    background-size: 400px;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-color: #f0f4f8; /* Light Blue/White Theme */
}}
.stApp {{
    background: rgba(255, 255, 255, 0.85); /* White overlay for readability */
}}
h1, h2, h3 {{
    color: #1e3a8a !important; /* Blue Header */
}}
.stButton>button {{
    background-color: #1e3a8a;
    color: gold;
    border-radius: 20px;
    width: 100%;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def get_gsheet():
    creds_dict = {{
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
    }}
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1

sheet = get_gsheet()

# --- STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_data = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>Sanah Rabea</h1>", unsafe_allow_html=True)

# --- LOGIN INTERFACE (CENTERED) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.subheader("Login Portal")
        role_choice = st.radio("I am a:", ["Student", "Teacher", "Admin"])
        
        if role_choice == "Student":
            id_input = st.text_input("Student Code")
            if st.button("Enter"):
                df = pd.DataFrame(sheet.get_all_records())
                user = df[df['CODE'].astype(str) == id_input]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.role = "Student"
                    st.session_state.user_data = user.iloc[0]
                    # Log login time
                    row_idx = df.index[df['CODE'].astype(str) == id_input].tolist()[0] + 2
                    sheet.update_cell(row_idx, 7, str(datetime.now().strftime("%Y-%m-%d %H:%M")))
                    st.rerun()
                else:
                    st.error("Code not found")

        elif role_choice == "Teacher":
            pwd = st.text_input("Teacher Password", type="password")
            if st.button("Login"):
                if pwd == st.secrets["TEACHER_PASSWORD"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "Teacher"
                    st.rerun()
                else: st.error("Wrong Password")

        elif role_choice == "Admin":
            pwd = st.text_input("Admin Password", type="password")
            if st.button("Login"):
                if pwd == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.rerun()
                else: st.error("Wrong Password")

# --- APP CONTENT ---
else:
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.write(f"Logged in as: {st.session_state.role}")

    # --- STUDENT VIEW ---
    if st.session_state.role == "Student":
        data = st.session_state.user_data
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(data['PHOTO_URL'] if data['PHOTO_URL'] else "https://via.placeholder.com/150", width=150)
            st.title(data['NAME'])
        
        with col2:
            st.metric("Current Juz", data['JUZ'])
            # Progress Bar Marks Comparison
            prev = int(data['PREVIOUS_MARKS'])
            curr = int(data['CURRENT_MARKS'])
            st.write(f"Ikhtebaar Score: {curr}%")
            st.progress(curr / 100)
            diff = curr - prev
            st.write(f"Change from previous: {'+' if diff >=0 else ''}{diff}%")

    # --- TEACHER VIEW ---
    elif st.session_state.role == "Teacher":
        st.subheader("Manage Progress")
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df[['CODE', 'NAME', 'JUZ', 'CURRENT_MARKS']])
        
        with st.expander("Update Student"):
            target_id = st.selectbox("Select Student", df['CODE'].tolist())
            new_juz = st.number_input("Update Juz", 1, 30)
            new_marks = st.number_input("Update Marks (%)", 0, 100)
            if st.button("Save Changes"):
                row_idx = df.index[df['CODE'] == target_id].tolist()[0] + 2
                sheet.update_cell(row_idx, 3, new_juz)
                sheet.update_cell(row_idx, 5, new_marks)
                st.success("Updated!")
                time.sleep(1)
                st.rerun()

    # --- ADMIN VIEW ---
    elif st.session_state.role == "Admin":
        st.subheader("Admin Control Center")
        df = pd.DataFrame(sheet.get_all_records())
        
        tab1, tab2 = st.tabs(["User Logs", "Full Database"])
        with tab1:
            st.write("Last Active Login times for Students:")
            st.table(df[['NAME', 'LAST_LOGIN']])
        with tab2:
            st.dataframe(df)

# Updated for the literal multiline secret
"private_key": st.secrets["G_PRIVATE_KEY"],
