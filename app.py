import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import pytz

# --- DATABASE ---
def get_db_connection():
    return sqlite3.connect('shirkada.db', check_same_thread=False)

def get_somalia_time():
    somalia_tz = pytz.timezone('Africa/Mogadishu')
    return datetime.now(somalia_tz).strftime('%Y-%m-%d %H:%M:%S')

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
            # Hubi role-ka (Admin vs Employee)
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
    # --- LOGOUT ---
    if st.sidebar.button("Ka Bax"):
        st.session_state.clear()
        st.rerun()

    # --- ADMIN VIEW ---
    if st.session_state.get('role') == 'admin':
        st.title("📊 Dashboard-ka Maamulka")
        conn = get_db_connection()
        
        tab1, tab2 = st.tabs(["Diiwaanka Shaqada", "Maamulka Shaqaalaha"])
        
        with tab1:
            st.subheader("📋 Diiwaanka")
            try:
                attendance_data = pd.read_sql_query("SELECT * FROM attendance ORDER BY check_in_time DESC", conn)
                st.dataframe(attendance_data, use_container_width=True)
                csv = attendance_data.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, "attendance.csv", "text/csv")
            except:
                st.warning("Xog ma jirto.")

        with tab2:
            st.subheader("🔄 Reset Qalabka Shaqaalaha")
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
