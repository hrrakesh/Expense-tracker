import sqlite3
import os
from datetime import datetime

DATABASE_NAME = "expense_tracker.db"

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DATABASE_NAME)

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Accounts table (Bank / Wallet / Cash)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        account_type TEXT DEFAULT 'bank',
        initial_balance REAL DEFAULT 0.0,
        logo TEXT,
        color TEXT DEFAULT '#4F46E5',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('debit', 'credit', 'both')),
        icon TEXT DEFAULT '🏷️',
        color TEXT DEFAULT '#64748B',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        category_id INTEGER,
        type TEXT NOT NULL CHECK(type IN ('credit', 'debit')),
        amount REAL NOT NULL CHECK(amount > 0),
        date TEXT NOT NULL,
        time TEXT DEFAULT '',
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    )
    """)

    # Check if categories table is empty, if so, seed default categories
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            # Debit (Expense)
            ('Food & Dining', 'debit', '🍔', '#EF4444'),
            ('Groceries', 'debit', '🛒', '#F59E0B'),
            ('Shopping', 'debit', '🛍️', '#EC4899'),
            ('Bills & Utilities', 'debit', '💡', '#3B82F6'),
            ('Transportation', 'debit', '🚗', '#8B5CF6'),
            ('Entertainment', 'debit', '🎬', '#10B981'),
            ('Health & Medical', 'debit', '💊', '#14B8A6'),
            ('Rent & Housing', 'debit', '🏠', '#6366F1'),
            ('Travel', 'debit', '✈️', '#0EA5E9'),
            ('Personal Care', 'debit', '💅', '#D946EF'),
            ('Other Expenses', 'debit', '📦', '#64748B'),
            # Credit (Income)
            ('Salary', 'credit', '💼', '#10B981'),
            ('Freelance / Side Gig', 'credit', '💻', '#059669'),
            ('Investments & Dividends', 'credit', '📈', '#14B8A6'),
            ('Gifts & Rewards', 'credit', '🎁', '#F59E0B'),
            ('Cashback & Refunds', 'credit', '💰', '#84CC16'),
            ('Other Income', 'credit', '💵', '#22C55E')
        ]
        cursor.executemany("""
            INSERT INTO categories (name, type, icon, color)
            VALUES (?, ?, ?, ?)
        """, default_categories)


    conn.commit()
    conn.close()

def get_accounts_with_balances():
    """Returns all accounts with dynamically calculated current balance and transaction totals."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.name,
            a.account_type,
            a.initial_balance,
            a.logo,
            a.color,
            a.created_at,
            COALESCE(SUM(CASE WHEN t.type = 'credit' THEN t.amount ELSE 0 END), 0) AS total_credits,
            COALESCE(SUM(CASE WHEN t.type = 'debit' THEN t.amount ELSE 0 END), 0) AS total_debits,
            (a.initial_balance + 
             COALESCE(SUM(CASE WHEN t.type = 'credit' THEN t.amount ELSE 0 END), 0) - 
             COALESCE(SUM(CASE WHEN t.type = 'debit' THEN t.amount ELSE 0 END), 0)) AS current_balance
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.account_id
        GROUP BY a.id
        ORDER BY a.id ASC
    """)
    rows = cursor.fetchall()
    accounts = [dict(row) for row in rows]
    conn.close()
    return accounts

def get_monthly_day_summaries(year, month):
    """
    Returns an aggregated dictionary of credits and debits per day for a given year & month.
    Key: 'YYYY-MM-DD', Value: {'credits': float, 'debits': float, 'count': int}
    """
    conn = get_db()
    cursor = conn.cursor()
    month_str = f"{year:04d}-{month:02d}%"
    cursor.execute("""
        SELECT 
            date,
            SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as total_credit,
            SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as total_debit,
            COUNT(*) as tx_count
        FROM transactions
        WHERE date LIKE ?
        GROUP BY date
    """, (month_str,))
    rows = cursor.fetchall()
    summary = {}
    for r in rows:
        summary[r['date']] = {
            'credit': float(r['total_credit'] or 0),
            'debit': float(r['total_debit'] or 0),
            'count': int(r['tx_count'] or 0)
        }
    conn.close()
    return summary

def get_transactions_by_date(date_str, account_id=None):
    """Returns all transactions for a specific date, optionally filtered by account."""
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT 
            t.id,
            t.account_id,
            t.category_id,
            t.type,
            t.amount,
            t.date,
            t.time,
            t.description,
            t.created_at,
            a.name AS account_name,
            a.logo AS account_logo,
            a.color AS account_color,
            c.name AS category_name,
            c.icon AS category_icon,
            c.color AS category_color
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.date = ?
    """
    params = [date_str]
    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
        
    query += " ORDER BY t.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    transactions = [dict(row) for row in rows]
    conn.close()
    return transactions
