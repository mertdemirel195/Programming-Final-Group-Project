"""SQLite helpers for Streamlit auth."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import bcrypt

DB_PATH = Path(__file__).parent / "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    conn.close()


def create_user(email: str, password: str) -> bool:
    conn = get_connection()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        with conn:
            conn.execute("INSERT INTO users(email, password) VALUES (?, ?)", (email.lower(), hashed))
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def authenticate(email: str, password: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT password FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if not row:
            return False
        return bcrypt.checkpw(password.encode(), row["password"])
    finally:
        conn.close()


def get_user(email: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email.lower(),)).fetchone()
        return row
    finally:
        conn.close()
