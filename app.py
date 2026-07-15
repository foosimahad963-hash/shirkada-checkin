import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz
import cv2
import numpy as np
import requests

# --- DATABASE ---
def get_db_connection():
    conn = sqlite3.connect('shirkada.db', check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS attendance (username TEXT, check_in_time TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, device_id TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS user_profiles (username TEXT PRIMARY KEY, ref_image BLOB)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON attendance(username)") 
    return conn

# --- SECURITY: Image Comparison ---
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
    stored_gray = cv2.cvtColor(stored_img, cv2.COLOR_BGR2GRAY)
    stored_gray = cv2.resize(stored_gray, (new_gray.shape[1], new_gray.shape[0]))
    
    diff = cv2.absdiff(new_gray, stored_gray)
    return np.mean(diff) < 50

# --- AUTOMATION: WhatsApp ---
def send_whatsapp_notification(username, time):
    instance_id = "instance184936"
    token = "spk55ant79w0xv3x"
    api_url = f"https://api.ultramsg.com/{instance_id}/messages/chat" 
    payload = {"token": token, "to": "+252637281967", "body": f"⚠️ Shaqaale {username} wuxuu Check-in sameeyay: {time}"}
    try: requests.post(api_url, data=payload)
    except: pass

# --- APP SETUP ---
st.set_page_config(page_title="Nidaamka Shaqaalaha", page_icon="🏢")
if 'device_id' not in st.session_state: st.session_state['device_id'] = str(uuid.uuid4())

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
            # Saxidda Error-ka (Unpacking error prevention)
            username = user[0]
            role = user[2]
            stored_device = user[3] if len(user) > 3 else None
            
            st.session_state.update({'logged_in': True, 'username': username, 'role': role})
            
            # Xayiraadda qalabka (Shaqaalaha kaliya)
            if role != 'admin':
                if stored_device is None:
                    c.execute("UPDATE users SET device_id=? WHERE username=?", (st.session_state['device_id'], username))
                    conn.commit()
                elif stored_device != st.session_state['device_id']:
                    st.error("⚠️ Moobilkan laguma oggola!")
                    st.stop()
            st.rerun()
        else:
            st.error("Magac ama fure khaldan.")
        conn.close()
else:
    if st.sidebar.button("Ka Bax"): st.session_state.clear(); st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        df['check_in_time'] = pd.to_datetime(df['check_in_time'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Wadarta", len(df))
        col2.metric("Maanta", len(df[df['check_in_time'].dt.date == datetime.now().date()]))
        col3.metric("Shaqaale", df['username'].nunique())
        
        st.divider()
        tab1, tab2, tab3, tab4 = st.tabs(["Diiwaanka", "Diiwaangeli", "Garaafyo", "Maamulka"])
        
        with tab1:
            st.dataframe(df.sort_values(by='check_in_time', ascending=False), use_container_width=True)
        with tab2:
            u_name = st.text_input("Magaca shaqaalaha")
            ref_img = st.camera_input("Sawirka Asalka")
            if ref_img and st.button("Kaydso"):
                conn.execute("INSERT OR REPLACE INTO user_profiles (username, ref_image) VALUES (?, ?)", (u_name, ref_img.getvalue()))
                conn.commit()
                st.success("✅ Sawirkii waa la diiwaangeliyay.")
        with tab3:
            df['hour'] = df['check_in_time'].dt.hour
            chart_data = df.groupby('hour').size().reset_index(name='Tirada')
            st.bar_chart(chart_data.set_index('hour'))
        with tab4:
            users_list = pd.read_sql_query("SELECT username FROM users WHERE role='employee'", conn)['username'].tolist()
            emp_to_reset = st.selectbox("Dooro shaqaale", users_list)
            if st.button("Reset Device ID"):
                conn.execute("UPDATE users SET device_id=NULL WHERE username=?", (emp_to_reset,))
                conn.commit()
                st.success(f"✅ Qalabkii {emp_to_reset} waa la fasaxay.")
        conn.close()

    # --- EMPLOYEE VIEW ---
    else:
        st.title("🏢 Bogga Shaqaalaha")
        img_file = st.camera_input("Fadlan is-sawir si aad u Check-in-gareyso")
        if img_file and st.button("Xaqiiji"):
            if compare_faces(img_file, st.session_state['username']):
                time_now = datetime.now(pytz.timezone('Africa/Mogadishu')).strftime('%Y-%m-%d %H:%M:%S')
                conn = get_db_connection()
                conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", (st.session_state['username'], time_now))
                conn.commit()
                conn.close()
                send_whatsapp_notification(st.session_state['username'], time_now)
                st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
            else:
                st.error("❌ Khalad! Sawirku kama dhigna sawirkaadii diiwaanka.")
