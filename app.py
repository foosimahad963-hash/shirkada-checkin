import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz
import cv2
import numpy as np

# --- DATABASE ---
def get_db_connection():
    return sqlite3.connect('shirkada.db', check_same_thread=False)

def get_somalia_time():
    somalia_tz = pytz.timezone('Africa/Mogadishu')
    return datetime.now(somalia_tz).strftime('%Y-%m-%d %H:%M:%S')

# --- GIDAAR HUBIN (Background Verification) ---
def is_valid_wall(img_file):
    # Sawirka u beddel qaabka OpenCV
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    user_img = cv2.imdecode(file_bytes, 1)
    # Xisaabi celceliska midabka (RGB)
    avg_color = np.average(np.average(user_img, axis=0), axis=0)
    # Gidaarkaaga cad/cawlka waa inuu leeyahay midab ka sarreeya 150 (0-255)
    return avg_color[0] > 150 and avg_color[1] > 150 and avg_color[2] > 150

# --- APP SETUP ---
st.set_page_config(page_title="Nidaamka Shaqaalaha", page_icon="🏢")

if 'device_id' not in st.session_state:
    st.session_state['device_id'] = str(uuid.uuid4())

# --- LOGIN ---
if not st.session_state.get('logged_in', False):
    st.title("🔐 Fadlan Gal Nidaamka")
    user_input = st.text_input("Magaca")
    pass_input = st.text_input("Furaha", type="password")
    
    if st.button("Gal"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user_input, pass_input))
        user = c.fetchone()
        
        if user:
            role = user[3]
            st.session_state.update({'logged_in': True, 'username': user[1], 'role': role})
            if role != 'admin':
                stored_device = user[4]
                if stored_device is None:
                    c.execute("UPDATE users SET device_id=? WHERE username=?", (st.session_state['device_id'], user_input))
                    conn.commit()
                elif stored_device != st.session_state['device_id']:
                    st.error("⚠️ Moobilkan laguma oggola!")
                    st.stop()
            st.rerun()
        else:
            st.error("Magaca ama furaha ayaa qaldan!")
        conn.close()

else:
    if st.sidebar.button("Ka Bax"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        tab1, tab2 = st.tabs(["Diiwaanka Shaqada", "Maamulka Shaqaalaha"])
        with tab1:
            attendance_data = pd.read_sql_query("SELECT * FROM attendance ORDER BY check_in_time DESC", conn)
            st.dataframe(attendance_data, use_container_width=True)
            csv = attendance_data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "attendance.csv", "text/csv")
        with tab2:
            st.subheader("🔄 Reset Qalabka Shaqaalaha")
            users_list = pd.read_sql_query("SELECT username FROM users WHERE role='employee'", conn)['username'].tolist()
            emp_to_reset = st.selectbox("Dooro shaqaale", users_list)
            if st.button("Reset Device ID"):
                conn.execute("UPDATE users SET device_id=NULL WHERE username=?", (emp_to_reset,))
                conn.commit()
                st.success(f"✅ Qalabkii {emp_to_reset} waa la fasaxay.")
        conn.close()

    else:
        st.title("🏢 Bogga Shaqaalaha")
        st.write(f"Soo dhowoow, {st.session_state['username']}")
        st.info("⚠️ Fadlan is-sawir adigoo hor taagan Gidaarka cad ee shirkadda.")
        
        img_file = st.camera_input("Fadlan is-sawir (Selfie)")
        
        if img_file:
            if st.button("Xaqiiji Check-in"):
                if is_valid_wall(img_file):
                    conn = get_db_connection()
                    conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", 
                                 (st.session_state['username'], get_somalia_time()))
                    conn.commit()
                    conn.close()
                    st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
                else:
                    st.error("❌ Khalad! Uma muuqato inaad hor taagan tahay Gidaarkii shirkadda.")
