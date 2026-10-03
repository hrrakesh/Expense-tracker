import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_NAME = "expense_tracker.db"
DEFAULT_TURSO_URL = "libsql://tracker-rakeshhr.aws-ap-south-1.turso.io"

TURSO_URL = os.environ.get("TURSO_DATABASE_URL", DEFAULT_TURSO_URL).strip()
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()

try:
    import libsql_client
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False

class TursoRow(dict):
    """Row wrapper that supports both dict-style row['col'] and index-style row[0]."""
    def __init__(self, columns, values):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

class TursoCursor:
    def __init__(self, client):
        self.client = client
        self.lastrowid = None
        self.rowcount = 0
        self._rows = []
        self._columns = ()
        self._idx = 0

    def execute(self, sql, params=None):
        if params is None:
            res = self.client.execute(sql)
        else:
            args = list(params) if isinstance(params, (tuple, list)) else params
            res = self.client.execute(sql, args)
        self.lastrowid = res.last_insert_rowid
        self.rowcount = res.rows_affected
        self._columns = res.columns
        self._rows = [TursoRow(res.columns, row) for row in res.rows]
        self._idx = 0
        return self

    def executemany(self, sql, seq_of_params):
        for params in seq_of_params:
            self.execute(sql, params)
        return self

    def fetchone(self):
        if self._idx < len(self._rows):
            row = self._rows[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        rows = self._rows[self._idx:]
        self._idx = len(self._rows)
        return rows

class TursoConnection:
    def __init__(self, url, auth_token):
        # Convert libsql:// scheme to https:// for HTTP protocol
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        self.client = libsql_client.create_client_sync(url=url, auth_token=auth_token)

    def cursor(self):
        return TursoCursor(self.client)

    def execute(self, sql, params=None):
        return self.cursor().execute(sql, params)

    def commit(self):
        pass

    def close(self):
        self.client.close()

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DATABASE_NAME)

def is_using_turso():
    return bool(HAS_LIBSQL and TURSO_URL and TURSO_TOKEN)

def get_db():
    if is_using_turso():
        return TursoConnection(TURSO_URL, TURSO_TOKEN)
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def check_db_connection():
    """
    Test database connection by executing a lightweight query.
    Returns True if connection is successful, False otherwise.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        conn.close()
        return bool(row)
    except Exception:
        return False


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
