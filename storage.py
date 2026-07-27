import sqlite3, json
from pathlib import Path
from datetime import datetime,timezone
DB=Path("data/copilot.db"); DB.parent.mkdir(exist_ok=True)
def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY,created_at TEXT,symbol TEXT,interval TEXT,side TEXT,entry REAL,stop REAL,tp1 REAL,tp2 REAL,tp3 REAL,status TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY,created_at TEXT,symbol TEXT,interval TEXT,score INTEGER,side TEXT,fingerprint TEXT UNIQUE)")
def add_trade(d):
    with sqlite3.connect(DB) as c: c.execute("INSERT INTO trades(created_at,symbol,interval,side,entry,stop,tp1,tp2,tp3,status) VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),d["symbol"],d["interval"],d["side"],d["entry"],d["stop"],d["tp1"],d["tp2"],d["tp3"],"ouvert"))
def rows(q):
    with sqlite3.connect(DB) as c: c.row_factory=sqlite3.Row; return [dict(x) for x in c.execute(q)]
def add_alert(s,i,r,fp):
    try:
        with sqlite3.connect(DB) as c: c.execute("INSERT INTO alerts(created_at,symbol,interval,score,side,fingerprint) VALUES(?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),s,i,r["score"],r["side"],fp)); return True
    except sqlite3.IntegrityError: return False
