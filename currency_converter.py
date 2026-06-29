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

def get_cached_rate(conn, from_currency, to_currency):
    row = conn.execute("""
        SELECT rate, saved_at
        FROM conv_rates
        WHERE from_currency = ? AND to_currency = ?
    """, (from_currency, to_currency)).fetchone()

    if not row:
        return None

    rate, saved_at = row
    age = time.time() - saved_at

    if age > CACHE_SECONDS:
        return None

    return rate


def save_cached_rate(conn, from_currency, to_currency, rate):
    conn.execute("""
        INSERT INTO conv_rates (from_currency, to_currency, rate, saved_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (from_currency, to_currency) DO NOTHING SET
            rate = excluded.rate,
            saved_at = excluded.saved_at
    """, (from_currency, to_currency, rate, int(time.time())))
    conn.commit()

def fetch_rate(from_currency, to_currency):
    params = {"from": from_currency, "to": to_currency, "amount": 1,}

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data.get("success", True):
        raise ValueError("API returned an error.")

    result = data.get("result")

    if result is None:
        raise ValueError("Could not find exchange rate.")

    return float(result)


def get_rate(conn, from_currency, to_currency):
    cached_rate = get_cached_rate(conn, from_currency, to_currency)

    if cached_rate is not None:
        print("Using cached rate.")
        return cached_rate
    rate = fetch_rate(from_currency, to_currency)
    save_cached_rate(conn, from_currency, to_currency, rate)
    return rate

def menu():
    print("Welcome to the currency converter.")
    print("1. Convert Currency")
