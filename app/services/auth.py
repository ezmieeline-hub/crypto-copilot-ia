import hashlib
import secrets
from app.services.database import connect

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def register_user(name: str, email: str, password: str):
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?) RETURNING id",
            (name.strip(), email.strip().lower(), hash_password(password)),
        )
        new_id = cursor.fetchone()["id"]
        db.commit()
        return new_id

def login_user(email: str, password: str):
    with connect() as db:
        user = db.execute(
            "SELECT id,name,email FROM users WHERE email=? AND password=?",
            (email.strip().lower(), hash_password(password)),
        ).fetchone()
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions(token,user_id) VALUES(?,?)", (token, user["id"]))
        db.commit()
        return token, dict(user)

def get_user(token: str | None):
    if not token:
        return None
    with connect() as db:
        row = db.execute(
            '''SELECT users.id,users.name,users.email
               FROM sessions JOIN users ON users.id=sessions.user_id
               WHERE sessions.token=?''',
            (token,),
        ).fetchone()
        return dict(row) if row else None
