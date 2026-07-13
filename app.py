import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz

# --- DATABASE ---
def get_db_connection():
    return sqlite3.connect('shirkada.db')

# --- WAKHTIGA SOOMAALIYA ---
def get_somalia_time():
    somalia_tz = pytz.timezone('Africa/Mogadishu')
    return datetime.now(somalia_tz).strftime('%Y-%m-%d %H:%M:%S')

# --- APP SETUP ---
st.set_page_config(page_title="Nidaamka Shaqaalaha", page_icon="🏢")

if 'device_id' not in st.session_state:
    st.session_state['device_id'] = str(uuid.uuid4())

# --- LOGIN & DASHBOARD ---
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
            is_admin = (user_input == 'admin')
            if is_admin:
                st.session_state.update({'logged_in': True, 'username': user[1], 'role': user[3]})
                st.rerun()
            else:
                stored_device = user[4] 
                if stored_device is None:
                    c.execute("UPDATE users SET device_id=? WHERE username=?", (st.session_state['device_id'], user_input))
                    conn.commit()
                    stored_device = st.session_state['device_id']
                
                if stored_device == st.session_state['device_id']:
                    st.session_state.update({'logged_in': True, 'username': user[1], 'role': user[3]})
                    st.rerun()
                else:
                    st.error("⚠️ Moobilkan laguma oggola! Fadlan la xiriir Admin.")
        else:
            st.error("Magaca ama furaha ayaa qaldan!")
        conn.close()

else:
    # --- SIDEBAR ---
    if st.sidebar.button("Ka Bax"):
        st.session_state.clear()
        st.rerun()

    # --- ADMIN VIEW ---
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        
        # 1. Furayaasha
        st.subheader("🔑 Xogta Shaqaalaha & Furayaasha")
        if st.checkbox("Muuji Furayaasha Shaqaalaha"):
            all_users = pd.read_sql_query("SELECT username, password FROM users", conn)
            st.table(all_users)
        
        # 2. Reset Device (Qaybtan waa la hagaajiyay si aysan u dhicin)
        st.subheader("🔄 Reset Moobilka Shaqaalaha")
        try:
            users_df = pd.read_sql_query("SELECT username FROM users WHERE role='employee'", conn)
            emp_to_reset = st.selectbox("Dooro shaqaale", users_df['username'])
            if st.button("Reset Device ID"):
                try:
                    conn.execute("UPDATE users SET device_id=NULL WHERE username=?", (emp_to_reset,))
                    conn.commit()
                    st.success(f"✅ Qalabkii {emp_to_reset} waa la reset-gareeyay.")
                except Exception as e:
                    st.warning("⚠️ Cloud-ka ayaa diiday inuu kaydiyo. Fadlan hubi in Database-kaagu yahay mid la qori karo.")
        except Exception as e:
            st.error("Ma jiro shaqaale la heli karo.")
        
        # 3. REPORTS & DOWNLOAD
        st.subheader("📋 Reports & Diiwaanka")
        try:
            attendance_data = pd.read_sql_query("SELECT * FROM attendance", conn)
            st.dataframe(attendance_data, use_container_width=True)
            
            csv = attendance_data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Diiwaanka (CSV)", csv, "attendance_report.csv", "text/csv")
        except:
            st.warning("Diiwaanka weli xog kuma jiro.")
        
        conn.close()

    # --- EMPLOYEE VIEW ---
    else:
        st.title("🏢 Bogga Shaqaalaha")
        st.write(f"Soo dhowoow, {st.session_state['username']}")
        
        img_file = st.camera_input("Fadlan is-sawir (Selfie)")
        
        if img_file:
            st.success("Sawirkaaga waa la qabtay!")
            if st.button("Xaqiiji Check-in"):
                conn = get_db_connection()
                conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", 
                             (st.session_state['username'], get_somalia_time()))
                conn.commit()
                conn.close()
                st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")
