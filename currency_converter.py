import sqlite3
import time

import requests

API_URL = "https://open.er-api.com/v6/latest"
CACHE_SECONDS = 3600
DB_PATH = "currency_cache.db"

SUPPORTED_CURRENCIES = {
    "1": ("USD", "US Dollar"),
    "2": ("EUR", "Euro"),
    "3": ("GBP", "British Pound"),
    "4": ("JPY", "Japanese Yen"),
    "5": ("CAD", "Canadian Dollar"),
    "6": ("AUD", "Australian Dollar"),
    "7": ("CHF", "Swiss Franc"),
    "8": ("CNY", "Chinese Yuan"),
}

def connect_db():
    conn = sqlite3.connect(DB_PATH)

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
        ON CONFLICT(from_currency, to_currency) DO UPDATE SET
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

def choose_currency(prompt):
    print(f"{prompt}")

    for number, (code, name) in SUPPORTED_CURRENCIES.items():
        print(f"{number}. {code} - {name}")

    choice = input("Choose currency: ").strip()

    if choice not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Invalid currency code.")

    return SUPPORTED_CURRENCIES[choice][0]

def get_amount():
    raw_amount = input("Enter amount: ").strip()

    try:
        amount = float(raw_amount)
    except ValueError:
        raise ValueError("Invalid amount.")

    if amount < 0:
        raise ValueError("Cannot be negative.")

    return amount

def convert_currency(conn):
    try:
        from_currency = choose_currency("From currency: ")
        to_currency = choose_currency("To currency: ")
        amount = get_amount()

        rate = get_rate(conn, from_currency, to_currency)
        converted_amount = amount * rate

        print(f"{amount:.2f} {from_currency} = {converted_amount:.2f} {to_currency}")
        print(f"Rate: 1 {from_currency} = {rate:.6f} {to_currency}")

    except requests.RequestException as error:
        print(f"Network/API error: {error}")
    except ValueError as error:
        print(f"Input error: {error}")


def menu():
    print("Welcome to the currency converter.")
    print("1. Convert Currency")
    print("2. Exit")

def main():
    conn = connect_db()

    while True:
        menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            convert_currency(conn)
        elif choice == "2":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")

    conn.close()

if __name__ == "__main__":
    main()