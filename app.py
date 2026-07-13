import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage

# --- DATABASE (Scalability: Indexed columns) ---
def get_db_connection():
    conn = sqlite3.connect('shirkada.db', check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS attendance (username TEXT, check_in_time TEXT)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON attendance(username)") # Scalability
    return conn

def send_email_notification(username, time):
    # Automation: Email dirid
    msg = EmailMessage()
    msg.set_content(f"Shaqaale {username} wuxuu Check-in sameeyay wakhtiga: {time}")
    msg['Subject'] = 'Check-in Notification'
    msg['From'] = 'shirkada@email.com'
    msg['To'] = 'admin@shirkada.com'
    # Fiiro gaar ah: Waxaad u baahan tahay SMTP settings halkan
    # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: ...

# --- SECURITY (Advanced Wall Recognition) ---
def is_valid_wall(img_file):
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    user_img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(user_img, cv2.COLOR_BGR2GRAY)
    # Canny Edge Detection si loo xaqiijiyo "Texture-ka" gidaarka
    edges = cv2.Canny(gray, 100, 200)
    # Haddii muuqaalku aad u mashquul badan yahay, waa meel kale
    return np.mean(edges) < 50 

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
            st.rerun()
        else:
            st.error("Magaca ama furaha ayaa qaldan!")
        conn.close()

else:
    if st.sidebar.button("Ka Bax"):
        st.session_state.clear()
        st.rerun()

    # --- ADMIN VIEW ---
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        attendance_data = pd.read_sql_query("SELECT * FROM attendance ORDER BY check_in_time DESC", conn)
        st.dataframe(attendance_data, use_container_width=True)
        conn.close()

    # --- EMPLOYEE VIEW ---
    else:
        st.title("🏢 Bogga Shaqaalaha")
        img_file = st.camera_input("Fadlan is-sawir (Selfie)")
        
        if img_file:
            if st.button("Xaqiiji Check-in"):
                # Security: Hubinta gidaarka oo la adkeeyay
                if is_valid_wall(img_file):
                    time_now = datetime.now(pytz.timezone('Africa/Mogadishu')).strftime('%Y-%m-%d %H:%M:%S')
                    conn = get_db_connection()
                    conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", 
                                 (st.session_state['username'], time_now))
                    conn.commit()
                    conn.close()
                    # Automation: Dirista ogaysiinta
                    send_email_notification(st.session_state['username'], time_now)
                    st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
                else:
                    st.error("❌ Khalad! Uma muuqato inaad hor taagan tahay Gidaarkii saxda ah.")
