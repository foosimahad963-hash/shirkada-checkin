import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid

# --- DATABASE ---
def get_db_connection():
    return sqlite3.connect('shirkada.db')

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
            # HUBINTA LOGIC-GA LOGIN-KA
            is_admin = (user_input == 'admin')
            
            if is_admin:
                # Admin: device_id lama hubinayo
                st.session_state.update({'logged_in': True, 'username': user[1], 'role': user[3]})
                st.rerun()
            else:
                # Shaqaale: device_id waa la hubinayaa
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
    # --- DASHBOARD & VIEW ---
    if st.sidebar.button("Ka Bax"):
        st.session_state.clear()
        st.rerun()

    # ADMIN VIEW
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        
        # Qaybta Password-ka ee lagu daray
        st.subheader("🔑 Xogta Shaqaalaha & Furayaasha")
        if st.checkbox("Muuji Furayaasha Shaqaalaha"):
            all_users = pd.read_sql_query("SELECT username, password FROM users", conn)
            st.table(all_users)
        
        st.subheader("🔄 Reset Moobilka Shaqaalaha")
        users_df = pd.read_sql_query("SELECT username FROM users WHERE role='employee'", conn)
        emp_to_reset = st.selectbox("Dooro shaqaale", users_df['username'])
        
        if st.button("Reset Device ID"):
            conn.execute("UPDATE users SET device_id=NULL WHERE username=?", (emp_to_reset,))
            conn.commit()
            st.success(f"✅ Qalabkii {emp_to_reset} waa la reset-gareeyay.")
        
        st.subheader("📋 Liiska Qalabka")
        st.table(pd.read_sql_query("SELECT username, device_id FROM users", conn))
        conn.close()

    # EMPLOYEE VIEW
    else:
        st.title("🏢 Bogga Shaqaalaha")
        img_file = st.camera_input("Fadlan is-sawir (Selfie)")
        if img_file and st.button("Xaqiiji Check-in"):
            conn = get_db_connection()
            conn.execute("INSERT INTO attendance (username, check_in_time) VALUES (?, ?)", 
                         (st.session_state['username'], datetime.now()))
            conn.commit()
            conn.close()
            st.success("✅ Check-in-kaaga waa la diiwaan geliyay!")