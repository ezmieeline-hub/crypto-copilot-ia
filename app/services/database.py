import sqlite3
from app.core.config import DB_PATH
def connect():
    c=sqlite3.connect(DB_PATH);c.row_factory=sqlite3.Row;return c
def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,symbol TEXT NOT NULL,signal TEXT NOT NULL,confidence INTEGER NOT NULL,result_json TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,symbol TEXT NOT NULL,target_price REAL NOT NULL,direction TEXT NOT NULL,active INTEGER DEFAULT 1,FOREIGN KEY(user_id) REFERENCES users(id))''')
        db.commit()
