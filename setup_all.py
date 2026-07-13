import sqlite3

def setup_all():
    conn = sqlite3.connect('shirkada.db')
    c = conn.cursor()

    # Abuuritaanka Miisaska
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, check_in_time TIMESTAMP, location TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT, timestamp TIMESTAMP)')

    # Gelinta Admin
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    except: pass

    # Gelinta 5-ta shaqaale
    employees = [('Iid', 'pass123', 'employee'), ('Cabdilaahi', 'pass123', 'employee'), 
                 ('Cabdiqani', 'pass123', 'employee'), ('Cali', 'pass123', 'employee'), 
                 ('Cabdiraxmaan', 'pass123', 'employee')]
    
    for emp in employees:
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", emp)
        except: print(f"Shaqaale {emp[0]} horey ayuu u jiray.")

    conn.commit()
    conn.close()
    print("✅ Wax walba waa diyaar! Database-kii iyo shaqaalihiiba waa la sameeyay.")

setup_all()