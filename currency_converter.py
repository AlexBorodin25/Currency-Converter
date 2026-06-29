import sqlite3
import time

import requests


def connect_db():
    conn = sqlite3.connect('DB_PATH')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS conv_rates (
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL,
        rate REAL NOT NULL,
        saved_at INTEGER NOT NULL,
        PRIMARY KEY (from_currency, to_currency))
    ''')

    conn.commit()
    return conn

def get_conv_rate(conn, from_currency, to_currency):
    row = conn.execute("""
        SELECT rate, saved_at
        FROM conv_rates
        WHERE from_currency = ? AND to_currency = ?
    """, (from_currency, to_currency)).fetchone()

    if not row:
        return None

    rate, saved_at = row
    age = time.time() - saved_at

