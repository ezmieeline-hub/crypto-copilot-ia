import os

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL", "")


class _ConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, query, params=()):
        query = query.replace("?", "%s")
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        return cur

    def commit(self):
        self._conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn.close()


def connect():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return _ConnWrapper(conn)


def init_db():
    with connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS sessions(
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id)
            )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS analyses(
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS alerts(
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                symbol TEXT NOT NULL,
                target_price REAL NOT NULL,
                direction TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )"""
        )
        db.commit()
