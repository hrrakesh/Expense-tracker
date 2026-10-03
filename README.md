# 💰 FinTrackPro - Smart Expense & Wealth Tracker

A modern, responsive Flask web application for tracking personal finances, bank/wallet accounts, and daily expenses with an interactive calendar locking system, built with **Python Flask**, **Tailwind CSS**, **Lucide Icons**, and **SQLite3**.

---

## ✨ Key Features

1. **🏦 Bank & Wallet Accounts Section (at top)**:
   - Add multiple Bank accounts, Digital Wallets, Cards, or Cash reserves.
   - Attach **custom uploaded logos** (PNG, JPG, SVG, WebP) or pick from built-in preset logos (Bank, Wallet, Card, Cash, PayPal, Apple).
   - Real-time dynamic balance tracking (Initial Balance + Total Credits − Total Debits).
   - One-click account filtering to isolate transactions for a specific bank or wallet.

2. **📅 Locked Calendar Accounting System**:
   - Interactive monthly calendar with weekday alignment and previous/next month navigation.
   - **Date Lock Rule**: Any date in the future (after today) is visible on the calendar but strictly **locked** (grayed out with a lock badge). You cannot add expenses or credits ahead of time.
   - Past dates and **Today** are fully unlocked.
   - Days with transactions display color-coded indicators:
     - 🟢 **Green badge/dots**: Credit (Income/Inflow)
     - 🔴 **Red badge/dots**: Debit (Expense/Outflow)

3. **📊 Click-to-Inspect Date View**:
   - Clicking any unlocked date opens the inspector with:
     - Total Credit & Total Debit breakdown for that specific day.
     - Day Net balance.
     - Action tabs (All, Credit, Debit).
     - Individual transaction cards displaying Category icon, Bank/Wallet logo, Description, Time, Amount, and Delete action.
   - **"+ Add Action"** button to record Credit or Debit for that date:
     - Toggle between **Debit (Expense)** and **Credit (Income)**.
     - Choose Account dropdown with current balances.
     - Select Category with emoji & color badges.
     - Enter Amount and Note.

4. **🏷️ Category Management**:
   - Dedicated Category Manager modal.
   - Grouped by Expense (Debit) and Income (Credit).
   - Create custom categories with custom emoji picker and color accents.
   - Pre-seeded with 17 essential categories (Food, Groceries, Shopping, Salary, Freelance, Investments, etc.).

5. **🗄️ Robust SQLite3 Database**:
   - Stores accounts, categories, and transactions in `expense_tracker.db`.
   - Foreign key constraints with cascade deletes.
   - No desync: balances are calculated dynamically from transactions.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (Python 3.12 is already tested and working)

### 2. Activate the Virtual Environment
Open PowerShell or your terminal in the project directory:

```powershell
.\.venv\Scripts\Activate.ps1
```

*(Or use `.\.venv\Scripts\python.exe` directly)*

### 3. Install Dependencies
Dependencies are already installed in `.venv`. To re-verify:
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Or with the virtual environment:
```powershell
.\.venv\Scripts\python app.py
```

### 5. Open in Your Browser
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser!

---

## 📁 Project Structure

```text
Expense-tracker-app/
│
├── app.py                      # Application factory, configuration & blueprint registration
├── config.py                   # Central app configuration, constants & environment variables
├── database.py                 # SQLite3 / Turso schema, initialization, and queries
├── requirements.txt            # Python dependencies (Flask, Werkzeug, libsql-client, etc.)
├── README.md                   # Documentation and usage guide
├── tracker-app.bat             # Windows one-click desktop launcher
│
├── blueprints/                 # Modular Flask Blueprints
│   ├── __init__.py             # Blueprint package registry
│   ├── main.py                 # Web dashboard root route
│   ├── auth.py                 # PIN verification authentication endpoint
│   ├── accounts.py             # Bank & wallet accounts CRUD and logo upload handling
│   ├── categories.py           # Income & expense categories CRUD
│   ├── calendar.py             # Monthly calendar view & lock boundary logic
│   ├── transactions.py         # Transaction record creation, editing, and deletion
│   ├── stats.py                # Net worth, monthly savings, and top categories stats
│   └── helpers.py              # File upload validation helpers
│
├── static/
│   ├── css/
│   │   └── style.css           # Calendar locking styles, glassmorphism, animations
│   ├── js/
│   │   └── app.js              # Dynamic calendar rendering, accounts, AJAX actions
│   ├── icons/                  # Preset vector SVGs (bank, wallet, card, cash, paypal, apple)
│   └── uploads/
│       └── logos/              # Storage directory for custom uploaded bank logos
│
└── templates/
    └── index.html              # Main responsive dashboard UI with Tailwind & Lucide
```
