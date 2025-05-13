# init_db.py

import sqlite3

conn = sqlite3.connect("sessions.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    start_time REAL,
    end_time REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    study_minutes INTEGER,
    break_minutes INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS study_goals (
    user_id INTEGER PRIMARY KEY,
    weekly_goal REAL,
    weekly_start INTEGER
                           
  )
'''
)

conn.commit()
conn.close()
print("Database initialized.")
