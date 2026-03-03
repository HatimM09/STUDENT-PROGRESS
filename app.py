import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. BRANDING, BACKGROUND & ARABIC FONT ---
st.set_page_config(page_title="Talabat Hifz Progress", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri&display=swap');
    
    /* Background Image with soft overlay */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), 
                    url("https://www.mahadalquran.com/wp-content/uploads/2022/01/slider-bg-1.jpg");
        background-size: cover;
        background-attachment: fixed;
    }

    /* Global Font Styling (Kanz Amiri) */
    html, body, [class*="css"], .stText, .stMarkdown {
        font-family: 'Amiri', serif !important;
    }

    /* Header Colors */
    h1, h2, h3 { color: #1A5276 !important; text-align: center; font-weight: bold; }

    /* Blue Button Styling */
    .stButton>button {
        background-color: #1A5276;
        color: white;
        border-radius: 12px;
        border: none;
        height: 3em;
        font-size: 1.1em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #154360;
        border: 1px solid #D4E6F1;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. LOGIN SIDEBAR ---
st.sidebar.markdown("<h2 style='color: #1A5276; text-align: center;'>🔐 Access Portal</h2>", unsafe_allow_html=True)
role = st.sidebar.selectbox("Choose Your Role", ["Student", "Teacher", "Admin"])

st.markdown("<h1>Talabat Hifz Progress</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5D6D7E;'>Al-Kanz Educational Management System</p>", unsafe_allow_html=True)
st.markdown("---")

# --- 4. APP LOGIC ---

# --- STUDENT ROLE (View Only) ---
if role == "Student":
    st.subheader("🔍 Check My Ikhtebar Result")
    student_code = st.text_input("Enter your Unique Student Code", type="password", placeholder="Ex: AK-101")
    
    if student_code:
        # Pull data from Google Sheets
        df = conn.read(ttl="1m")
        # Security Filter: Student ONLY sees their own code
        my_row = df[df['CODE'].astype(str) == student_code]
        
        if not my_row.empty:
            st.balloons()
            st.success(f"Mabrook! Record Found for: {my_row.iloc[-1]['ARABIC_NAME']}")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.info(f"**English Name:** {my_row.iloc[-1]['NAME']}")
                st.info(f"**Juz Number:** {my_row.iloc[-1]['JUZ']}")
                st.info(f"**Exam Date:** {my_row.iloc[-1]['DATE']}")
            with c2:
                st.image(my_row.iloc[-1]['LINK'], caption="Official Marksheet", use_container_width=True)
        else:
            st.error("Access Denied: Code not found. Please verify with your Teacher.")

# --- TEACHER ROLE (Add & View) ---
elif role == "Teacher":
    # Using Secrets for Security
    t_pass = st.sidebar.text_input("Teacher Password", type="password")
    
    # This checks against the 'Secrets' you will set in the Cloud
    if t_pass == st.secrets.get("TEACHER_PASSWORD", "teacher123"):
        tab1, tab2 = st.tabs(["📝 Add New Report", "📊 View Progress Tracker"])
        
        with tab1:
            with st.form("entry_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    name_en = st.text_input("Student Name (English)")
                    code = st.text_input("Unique Code")
                    date = st.date_input("Exam Date")
                with col_b:
                    name_ar = st.text_input("Student Name (Arabic)")
                    juz = st.number_input("Juz Number", 1, 30)
                    link = st.text_input("Marksheet JPG Link")
                
                if st.form_submit_button("Submit to Database"):
                    if name_en and code and link:
                        new_data = pd.DataFrame([{"NAME": name_en, "ARABIC_NAME": name_ar, "CODE": code, "JUZ": juz, "DATE": str(date), "LINK": link}])
                        # Update Google Sheet
                        existing_df = conn.read(ttl=0)
                        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success("Report successfully added to the portal!")
                    else:
                        st.warning("Please fill in all fields before saving.")
        with tab2:
            st.dataframe(conn.read(ttl="1m"), use_container_width=True)

# --- ADMIN ROLE (Full Authority) ---
elif role == "Admin":
    a_pass = st.sidebar.text_input("Admin Master Key", type="password")
    
    if a_pass == st.secrets.get("ADMIN_PASSWORD", "admin000"):
        st.subheader("👑 Master Database Control")
        st.write("Edit any cell or delete rows below. Changes sync globally.")
        
        # Pull fresh data
        df = conn.read(ttl=0)
        # Data Editor allows Admin to Edit/Delete
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 PERMANENTLY SAVE ALL CHANGES"):
            conn.update(data=edited_df)
            st.success("The Google Sheet has been updated with your changes.")
    else:

        st.warning("Admin authentication required.")

# --- STUDENT ROLE (With Progress Bar) ---
if role == "Student":
    st.markdown("<h3 style='text-align: center; color: #064e3b;'>🔍 Check Your Progress</h3>", unsafe_allow_html=True)
    student_code = st.text_input("12", type="password")
    
    if student_code:
        df = conn.read(ttl="1m")
        my_row = df[df['CODE'].astype(str) == student_code]
        
        if not my_row.empty:
            latest_data = my_row.iloc[-1]
            st.success(f"Ahlan wa Sahlan, {latest_data['ARABIC_NAME']}!")
            
            # --- PROGRESS BAR CALCULATION ---
            current_juz = int(latest_data['JUZ'])
            progress_percent = int((current_juz / 30) * 100)
            
            col_prog, col_stats = st.columns([2, 1])
            with col_prog:
                st.write(f"**Hifz Completion: {progress_percent}%**")
                # Emerald Green progress bar
                st.progress(progress_percent / 100) 
            with col_stats:
                st.metric(label="Current Juz", value=f"{current_juz} / 30")

            st.markdown("---")

            # --- DISPLAY DETAILS ---
            col1, col2 = st.columns([1, 1])
            with col1:
                st.info(f"**Name:** {latest_data['NAME']}")
                st.info(f"**Last Exam Date:** {latest_data['DATE']}")
            with col2:
                if latest_data['LINK']:
                    st.image(latest_data['LINK'], caption="Latest Marksheet", use_container_width=True)
        else:
            st.error("Code not found. Please contact the Admin.")


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Montserrat:wght@300;500&display=swap');
    
    /* 1. Background & Overlay */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), 
                    url("https://www.transparenttextures.com/patterns/arabesque.png"); /* Subtle Islamic Pattern */
        background-color: #f4f7f6;
    }

    /* 2. Top Header Bar */
    .main-header {
        background-color: #064e3b; /* Deep Emerald */
        padding: 20px;
        border-radius: 0px 0px 30px 30px;
        color: #f1c40f; /* Gold Text */
        text-align: center;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }

    /* 3. Typography */
    h1, h2, h3 { 
        font-family: 'Amiri', serif !important; 
        color: #064e3b !important; 
    }
    
    p, span, label { 
        font-family: 'Montserrat', sans-serif !important; 
        color: #2d3436;
    }

    /* 4. Beautiful Cards for Data */
    .stAlert {
        border-left: 5px solid #f1c40f !important;
        background-color: white !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        border-radius: 15px !important;
    }

    /* 5. Gold Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #064e3b 0%, #0a6c54 100%);
        color: white !important;
        border: 2px solid #f1c40f;
        border-radius: 25px;
        padding: 10px 25px;
        transition: 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        border-color: #fff;
    }

    /* 6. Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #064e3b;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
</style>

""", unsafe_allow_html=True)




