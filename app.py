import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Page Config
st.set_page_config(page_title="Al-Kanz Portal", page_icon="🌙", layout="wide")

# Styling
st.markdown("""
    <style>
    .main { background-color: #064e3b; color: #ffffff; }
    .stButton>button { background-color: #f1c40f; color: #064e3b; font-weight: bold; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# GOOGLE SHEETS CONNECTION (gspread method)
# ---------------------------------------------------------
@st.cache_resource
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Load JSON from secrets
    creds_info = json.loads(st.secrets["GSHEETS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

try:
    client = get_gsheet_client()
    # Opens the first sheet of the spreadsheet
    sheet = client.open_by_url(st.secrets["SHEET_URL"]).sheet1
except Exception as e:
    st.error(f"Connection Failed: {e}")
    st.stop()

# ---------------------------------------------------------
# APP LOGIC
# ---------------------------------------------------------
st.title("🌙 Al-Kanz Student Portal")

menu = ["Student Login", "Teacher Dashboard"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Student Login":
    st.header("👤 Student Progress")
    student_id = st.text_input("Enter Student Code")
    
    if student_id:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        student_row = df[df['CODE'].astype(str) == student_id]
        
        if not student_row.empty:
            st.success(f"Welcome, {student_row.iloc[0]['NAME']}!")
            col1, col2 = st.columns(2)
            col1.metric("Current Juz", student_row.iloc[0]['JUZ'])
            col2.metric("Last Updated", student_row.iloc[0]['LAST_DATE'])
        else:
            st.error("Student code not found.")

elif choice == "Teacher Dashboard":
    st.header("👨‍🏫 Teacher Access")
    pwd = st.text_input("Enter Teacher Password", type="password")
    
    if pwd == st.secrets["TEACHER_PASSWORD"]:
        st.info("Access Granted")
        
        # Form to update progress
        with st.form("update_form"):
            s_code = st.text_input("Student Code to Update")
            new_juz = st.number_input("New Juz Count", min_value=1, max_value=30)
            submit = st.form_submit_button("Update Progress")
            
            if submit:
                # Find the row index (gspread is 1-indexed, +1 for header)
                all_data = sheet.get_all_records()
                found = False
                for i, row in enumerate(all_data):
                    if str(row['CODE']) == s_code:
                        # Update JUZ column (Assume it's Column C / Index 3)
                        sheet.update_cell(i + 2, 3, new_juz)
                        st.success("Record updated successfully!")
                        found = True
                        break
                if not found:
                    st.warning("Student code not found in the sheet.")
