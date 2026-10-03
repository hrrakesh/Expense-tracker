"""
Data Migration Script: Local SQLite -> Turso Cloud Database
Migrates all accounts, categories, and transactions from local expense_tracker.db to Turso.
"""
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

import database

def migrate():
    local_db_path = database.get_db_path()
    if not os.path.exists(local_db_path):
        print(f"[!] Local database file not found at: {local_db_path}")
        return

    if not database.is_using_turso():
        print("[!] Turso is not configured. Please check your .env file for TURSO_AUTH_TOKEN.")
        return

    print("[-] Connecting to Local SQLite database...")
    local_conn = sqlite3.connect(local_db_path)
    local_conn.row_factory = sqlite3.Row
    local_cur = local_conn.cursor()

    print("[-] Connecting to Turso Cloud database...")
    turso_conn = database.get_db()
    turso_cur = turso_conn.cursor()

    # Ensure schema is initialized on Turso
    database.init_db()

    # 1. Migrate Categories
    local_cur.execute("SELECT id, name, type, icon, color, created_at FROM categories")
    local_categories = local_cur.fetchall()
    print(f"[-] Migrating {len(local_categories)} categories...")
    for cat in local_categories:
        turso_cur.execute("""
            INSERT OR REPLACE INTO categories (id, name, type, icon, color, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cat['id'], cat['name'], cat['type'], cat['icon'], cat['color'], cat['created_at']))

    # 2. Migrate Accounts
    local_cur.execute("SELECT id, name, account_type, initial_balance, logo, color, created_at FROM accounts")
    local_accounts = local_cur.fetchall()
    print(f"[-] Migrating {len(local_accounts)} accounts...")
    for acc in local_accounts:
        turso_cur.execute("""
            INSERT OR REPLACE INTO accounts (id, name, account_type, initial_balance, logo, color, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (acc['id'], acc['name'], acc['account_type'], acc['initial_balance'], acc['logo'], acc['color'], acc['created_at']))

    # 3. Migrate Transactions
    local_cur.execute("SELECT id, account_id, category_id, type, amount, date, time, description, created_at FROM transactions")
    local_txs = local_cur.fetchall()
    print(f"[-] Migrating {len(local_txs)} transactions...")
    for tx in local_txs:
        turso_cur.execute("""
            INSERT OR REPLACE INTO transactions (id, account_id, category_id, type, amount, date, time, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx['id'], tx['account_id'], tx['category_id'], tx['type'], tx['amount'], tx['date'], tx['time'], tx['description'], tx['created_at']))

    local_conn.close()
    turso_conn.close()

    print("[+] Migration completed successfully! All records are now in Turso Cloud.")

if __name__ == "__main__":
    migrate()
