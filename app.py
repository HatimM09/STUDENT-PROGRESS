import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Sanah Rabea Portal", layout="wide")

# --- 2. THEME & CUSTOM CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://www.elearningquran.com/imgs/MAZLogo.png") no-repeat center;
        background-size: 500px;
        background-color: #fdfdfd;
        background-attachment: fixed;
    }}
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 20px;
        padding: 50px;
        margin-top: 50px;
        border: 2px solid #1e3a8a;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }}
    h1 {{ color: #1e3a8a !important; text-align: center; font-size: 55px; font-weight: bold; }}
    h3 {{ color: #1e3a8a !important; }}
    .stButton>button {{
        background-color: #1e3a8a;
        color: #FFD700; /* Gold */
        border-radius: 10px;
        font-weight: bold;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_sheet():
    try:
        # Loading the JSON string from secrets
        creds_info = json.loads(st.secrets["GOOGLE_JSON"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

sheet = get_sheet()

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_data = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

st.markdown("<h1>Sanah Rabea</h1>", unsafe_allow_html=True)

# --- 5. LOGIN INTERFACE (CENTERED) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h3 style='text-align:center;'>User Login</h3>", unsafe_allow_html=True)
        login_role = st.selectbox("Select Access Level", ["Student", "Teacher", "Admin"])
        
        if login_role == "Student":
            id_code = st.text_input("Student Code")
            if st.button("Access Report"):
                df = pd.DataFrame(sheet.get_all_records())
                user = df[df['CODE'].astype(str) == id_code]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.role = "Student"
                    st.session_state.user_data = user.iloc[0]
                    # Log Login Time (Column 7)
                    row_idx = user.index[0] + 2
                    sheet.update_cell(row_idx, 7, datetime.now().strftime("%d/%m/%Y %H:%M"))
                    st.rerun()
                else: st.error("Code not found.")

        elif login_role == "Teacher":
            pwd = st.text_input("Teacher Password", type="password")
            if st.button("Teacher Login"):
                if pwd == st.secrets["TEACHER_PASSWORD"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "Teacher"
                    st.rerun()
                else: st.error("Incorrect Password")

        elif login_role == "Admin":
            pwd = st.text_input("Admin Password", type="password")
            if st.button("Admin Login"):
                if pwd == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.rerun()
                else: st.error("Incorrect Password")

# --- 6. DASHBOARDS ---
else:
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{st.session_state.role}**")
    if st.sidebar.button("Logout"): logout()

    # --- STUDENT DASHBOARD ---
    if st.session_state.role == "Student":
        u = st.session_state.user_data
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            # Use placeholder if PHOTO_URL is empty
            img_url = u['PHOTO_URL'] if u['PHOTO_URL'] else "https://www.w3schools.com/howto/img_avatar.png"
            st.image(img_url, width=200)
        with col_txt:
            st.title(f"Welcome, {u['NAME']}")
            st.write(f"**Juz Level:** {u['JUZ']}")
            
            # Progress Bar Comparison
            curr = int(u['CURRENT_MARKS'])
            prev = int(u['PREVIOUS_MARKS'])
            st.subheader(f"Ikhtebaar Score: {curr}%")
            st.progress(curr / 100)
            
            delta = curr - prev
            color = "green" if delta >= 0 else "red"
            st.markdown(f"Trend: <span style='color:{color}; font-weight:bold;'>{'+' if delta >=0 else ''}{delta}%</span> since previous exam.", unsafe_allow_html=True)

    # --- TEACHER DASHBOARD ---
    elif st.session_state.role == "Teacher":
        st.subheader("Student Progress Management")
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df[['CODE', 'NAME', 'JUZ', 'CURRENT_MARKS']])
        
        with st.expander("Update Student Marks/Juz"):
            target = st.selectbox("Select Student", df['CODE'].tolist())
            njuz = st.number_input("Update Juz", 1, 30)
            nmarks = st.number_input("Update Marks", 0, 100)
            if st.button("Save to Database"):
                row = df.index[df['CODE'] == target].tolist()[0] + 2
                # Push Current to Previous automatically
                old_val = df.loc[df['CODE'] == target, 'CURRENT_MARKS'].values[0]
                sheet.update_cell(row, 4, old_val) 
                sheet.update_cell(row, 3, njuz)
                sheet.update_cell(row, 5, nmarks)
                st.success("Successfully updated!")
                st.rerun()

    # --- ADMIN DASHBOARD ---
    elif st.session_state.role == "Admin":
        st.subheader("Admin Sole Power Dashboard")
        df = pd.DataFrame(sheet.get_all_records())
        
        tab1, tab2 = st.tabs(["User Activity (Login Logs)", "Master Database"])
        with tab1:
            st.write("### Login Status Tracker")
            st.table(df[['NAME', 'CODE', 'LAST_LOGIN']])
        with tab2:
            st.write("### Full Records (Read/Edit Only)")
            st.dataframe(df)
