import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz
import cv2
import numpy as np
import requests

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect('shirkada.db', check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS attendance (username TEXT, check_in_time TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, device_id TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS user_profiles (username TEXT PRIMARY KEY, ref_image BLOB)")
    return conn

# --- SECURITY: Face Comparison ---
def compare_faces(img_file, username):
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    new_img = cv2.imdecode(file_bytes, 1)
    new_gray = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT ref_image FROM user_profiles WHERE username=?", (username,))
    data = c.fetchone()
    conn.close()
    if not data: return False
    
    stored_img = cv2.imdecode(np.frombuffer(data[0], np.uint8), 1)
    stored_gray = cv2.resize(cv2.cvtColor(stored_img, cv2.COLOR_BGR2GRAY), (new_gray.shape[1], new_gray.shape[0]))
    return np.mean(cv2.absdiff(new_gray, stored_gray)) < 50

# --- AUTOMATION: WhatsApp ---
def send_whatsapp_notification(username, time):
    instance_id = "instance184936"
    token = "spk55ant79w0xv3x"
    api_url = f"https://api.ultramsg.com/{instance_id}/messages/chat" 
    try: requests.post(api_url, data={"token": token, "to": "+252637281967", "body": f"⚠️ Shaqaale {username} wuxuu Check-in sameeyay: {time}"})
    except: pass

# --- APP SETUP ---
st.set_page_config(page_title="Nidaamka Shaqaalaha", page_icon="🏢")
if 'device_id' not in st.session_state: st.session_state['device_id'] = str(uuid.uuid4())

# --- LOGIN & AUTHENTICATION ---
if not st.session_state.get('logged_in', False):
    st.title("🔐 Fadlan Gal Nidaamka")
    u_name = st.text_input("Magaca")
    p_word = st.text_input("Furaha", type="password")
    if st.button("Gal"):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u_name, p_word)).fetchone()
        if user:
            # user: (username, password, role, device_id)
            st.session_state.update({'logged_in': True, 'username': user[0], 'role': user[2]})
            
            # Xayiraadda Shaqaalaha oo kaliya
            if user[2] != 'admin':
                stored_dev = user[3]
                if stored_dev is None:
                    conn.execute("UPDATE users SET device_id=? WHERE username=?", (st.session_state['device_id'], user[0]))
                    conn.commit()
                elif stored_dev != st.session_state['device_id']:
                    st.error("⚠️ Moobilkan laguma oggola!")
                    st.stop()
            st.rerun()
        else: st.error("Magac ama fure khaldan.")
        conn.close()

# --- MAIN APP ---
else:
    if st.sidebar.button("Ka Bax"): st.session_state.clear(); st.rerun()
    
    # ADMIN DASHBOARD
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        df['check_in_time'] = pd.to_datetime(df['check_in_time'])
        
        t1, t2, t3, t4 = st.tabs(["Diiwaanka", "Diiwaangeli", "Garaafyo", "Maamulka Qalabka"])
        with t1: st.dataframe(df)
        with t2:
            u_name = st.text_input("Magaca shaqaalaha")
            ref_img = st.camera_input("Sawirka Asalka")
            if ref_img and st.button("Kaydso"):
                conn.execute("INSERT OR REPLACE INTO user_profiles (username, ref_image) VALUES (?, ?)", (u_name, ref_img.getvalue()))
                conn.commit()
                st.success("✅ Sawirkii waa la kaydiyay.")
        with t3:
            df['hour'] = df['check_in_time'].dt.hour
            st.bar_chart(df.groupby('hour').size())
        with t4:
            emp = st.selectbox("Dooro shaqaale", pd.read_sql_query("SELECT username FROM users WHERE role='employee'", conn)['username'])
            if st.button("Reset Device ID"):
                conn.execute("UPDATE users SET device_id=NULL WHERE username=?", (emp,))
                conn.commit()
                st.success(f"✅ Qalabkii {emp} waa la fasaxay.")
        conn.close()

    # EMPLOYEE VIEW
    else:
        st.title("🏢 Bogga Shaqaalaha")
        img = st.camera_input("Fadlan is-sawir")
        if img and st.button("Xaqiiji"):
            if compare_faces(img, st.session_state['username']):
                t_now = datetime.now(pytz.timezone('Africa/Mogadishu')).strftime('%Y-%m-%d %H:%M:%S')
                conn = get_db_connection()
                conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", (st.session_state['username'], t_now))
                conn.commit()
                conn.close()
                send_whatsapp_notification(st.session_state['username'], t_now)
                st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
            else: st.error("❌ Khalad! Sawirku ma saxna.")
