import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIG GOOGLE SHEETS ---
def get_gsheet_connection():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(creds)
    # Magaca sheet-kaaga beddel haddii loo baahdo
    sheet = client.open("Shaqaalaha_Attendance").sheet1
    return sheet

# --- WAKHTIGA SOOMAALIYA ---
def get_somalia_time():
    somalia_tz = pytz.timezone('Africa/Mogadishu')
    return datetime.now(somalia_tz).strftime('%Y-%m-%d %H:%M:%S')

# --- APP SETUP ---
st.set_page_config(page_title="Nidaamka Shaqaalaha", page_icon="🏢")

if 'device_id' not in st.session_state:
    st.session_state['device_id'] = str(uuid.uuid4())

# --- LOGIN (Isticmaal Sheet loogu talagalay Users ama halkii hore) ---
# Fiiro gaar ah: Qaybta Login-ka waxaa fiican inaad ku dartaa users-kaaga Google Sheet si aysan u dhicin.

if not st.session_state.get('logged_in', False):
    st.title("🔐 Fadlan Gal Nidaamka")
    user_input = st.text_input("Magaca")
    pass_input = st.text_input("Furaha", type="password")
    
    if st.button("Gal"):
        # Halkan waxaad ka akhrin kartaa Users-ka Google Sheet
        st.session_state.update({'logged_in': True, 'username': user_input, 'role': 'employee'})
        st.rerun()

else:
    # --- EMPLOYEE VIEW (Google Sheets version) ---
    if st.session_state.get('role') != 'admin':
        st.title("🏢 Bogga Shaqaalaha")
        st.write(f"Soo dhowoow, {st.session_state['username']}")
        
        cam_container = st.empty()
        with cam_container.container():
            img_file = st.camera_input("Fadlan is-sawir (Selfie)")
        
        if img_file:
            st.success("Sawirkaaga waa la qabtay!")
            if st.button("Xaqiiji Check-in"):
                try:
                    # Halkan waxaan ku diiwaangelinaynaa Google Sheet
                    sheet = get_gsheet_connection()
                    sheet.append_row([st.session_state['username'], get_somalia_time()])
                    st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
                except Exception as e:
                    st.error(f"Khalad ayaa dhacay: {e}")
