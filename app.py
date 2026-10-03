import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-expense-tracker-2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'logos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max logo size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
with app.app_context():
    database.init_db()

@app.route('/')
def index():
    today = date.today().isoformat()
    return render_template('index.html', today=today)

# ----------------- ACCOUNTS API -----------------
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = database.get_accounts_with_balances()
    return jsonify(accounts)

@app.route('/api/accounts', methods=['POST'])
def add_account():
    name = request.form.get('name', '').strip()
    account_type = request.form.get('account_type', 'bank')
    color = request.form.get('color', '#4F46E5')
    preset_logo = request.form.get('preset_logo', '')
    
    try:
        initial_balance = float(request.form.get('initial_balance', 0.0))
    except ValueError:
        return jsonify({'error': 'Invalid initial balance value'}), 400

    if not name:
        return jsonify({'error': 'Account name is required'}), 400

    logo_path = preset_logo or 'preset_bank'
    
    # Check if a custom logo image was uploaded
    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"account_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            logo_path = f"/static/uploads/logos/{filename}"

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (name, account_type, initial_balance, logo, color)
        VALUES (?, ?, ?, ?, ?)
    """, (name, account_type, initial_balance, logo_path, color))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': new_id, 'message': 'Account created successfully!'}), 201

@app.route('/api/accounts/<int:account_id>', methods=['PUT', 'POST'])
def update_account(account_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    account = cursor.fetchone()
    if not account:
        conn.close()
        return jsonify({'error': 'Account not found'}), 404

    name = request.form.get('name', account['name']).strip()
    account_type = request.form.get('account_type', account['account_type'])
    color = request.form.get('color', account['color'])
    preset_logo = request.form.get('preset_logo', '')
    
    try:
        initial_balance = float(request.form.get('initial_balance', account['initial_balance']))
    except ValueError:
        initial_balance = account['initial_balance']

    if not name:
        return jsonify({'error': 'Account name cannot be empty'}), 400

    logo_path = account['logo']
    if preset_logo:
        logo_path = preset_logo

    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = f"account_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            if account['logo'] and account['logo'].startswith('/static/uploads/logos/'):
                old_file = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(account['logo']))
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except OSError:
                        pass
            logo_path = f"/static/uploads/logos/{filename}"

    cursor.execute("""
        UPDATE accounts
        SET name = ?, account_type = ?, initial_balance = ?, logo = ?, color = ?
        WHERE id = ?
    """, (name, account_type, initial_balance, logo_path, color, account_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'Account "{name}" updated successfully!'})

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT logo FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Account not found'}), 404

    # If it's a custom uploaded file, delete it from disk
    if row['logo'] and row['logo'].startswith('/static/uploads/logos/'):
        filename = os.path.basename(row['logo'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Account and all associated records deleted'})

# ----------------- CATEGORIES API -----------------
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY type ASC, name ASC")
    rows = cursor.fetchall()
    categories = [dict(r) for r in rows]
    conn.close()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    cat_type = data.get('type', 'debit')
    icon = data.get('icon', '🏷️').strip()
    color = data.get('color', '#64748B')

    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    if cat_type not in ('debit', 'credit', 'both'):
        return jsonify({'error': 'Invalid category type'}), 400

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO categories (name, type, icon, color)
        VALUES (?, ?, ?, ?)
    """, (name, cat_type, icon or '🏷️', color))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True, 
        'category': {
            'id': new_id, 
            'name': name, 
            'type': cat_type, 
            'icon': icon, 
            'color': color
        }
    }), 201

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Category deleted successfully'})

# ----------------- CALENDAR & TRANSACTIONS API -----------------
START_YEAR = 2026
START_MONTH = 10

@app.route('/api/calendar/month', methods=['GET'])
def get_calendar_month():
    today = date.today()
    try:
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    # RULE: Calendar starts strictly at Oct 2026, no previous months allowed
    if year < START_YEAR or (year == START_YEAR and month < START_MONTH):
        year, month = START_YEAR, START_MONTH

    # RULE: Cannot see future months; unlocks next month only when that month arrives
    if year > today.year or (year == today.year and month > today.month):
        year, month = today.year, today.month

    summaries = database.get_monthly_day_summaries(year, month)
    
    # Calculate month grand totals
    total_credit = sum(day['credit'] for day in summaries.values())
    total_debit = sum(day['debit'] for day in summaries.values())

    can_go_prev = not (year == START_YEAR and month == START_MONTH)
    can_go_next = not (year == today.year and month == today.month)

    return jsonify({
        'year': year,
        'month': month,
        'today': today.isoformat(),
        'start_year': START_YEAR,
        'start_month': START_MONTH,
        'can_go_prev': can_go_prev,
        'can_go_next': can_go_next,
        'summaries': summaries,
        'month_total_credit': total_credit,
        'month_total_debit': total_debit,
        'month_net': total_credit - total_debit
    })

@app.route('/api/transactions/date/<date_str>', methods=['GET'])
def get_transactions_for_date(date_str):
    account_id = request.args.get('account_id')
    account_id = int(account_id) if account_id else None
    
    transactions = database.get_transactions_by_date(date_str, account_id)
    
    credits = [t for t in transactions if t['type'] == 'credit']
    debits = [t for t in transactions if t['type'] == 'debit']
    total_credit = sum(t['amount'] for t in credits)
    total_debit = sum(t['amount'] for t in debits)
    
    today_str = date.today().isoformat()
    is_locked = date_str > today_str

    return jsonify({
        'date': date_str,
        'today': today_str,
        'is_locked': is_locked,
        'transactions': transactions,
        'credits': credits,
        'debits': debits,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'net': total_credit - total_debit
    })

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.get_json() or {}
    
    account_id = data.get('account_id')
    category_id = data.get('category_id') or None
    tx_type = data.get('type')  # 'credit' or 'debit'
    tx_date = data.get('date')  # YYYY-MM-DD
    time_str = data.get('time', datetime.now().strftime('%H:%M'))
    description = data.get('description', '').strip()
    
    today_str = date.today().isoformat()

    # CRITICAL RULES: Calendar starts at 2026-10-01; no future dates beyond today allowed
    if not tx_date:
        return jsonify({'error': 'Transaction date is required'}), 400

    if tx_date < '2026-10-01':
        return jsonify({
            'error': 'The tracking system starts from October 1, 2026. Dates prior to October 2026 are not accessible.'
        }), 400

    if tx_date > today_str:
        return jsonify({
            'error': f'Date {tx_date} is locked! You can only record transactions for today ({today_str}) or past dates.'
        }), 400

    if not account_id:
        return jsonify({'error': 'Please select an account'}), 400

    if tx_type not in ('credit', 'debit'):
        return jsonify({'error': 'Transaction type must be credit or debit'}), 400

    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount value'}), 400

    conn = database.get_db()
    cursor = conn.cursor()

    # Check account exists
    cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Selected account does not exist'}), 404

    cursor.execute("""
        INSERT INTO transactions (account_id, category_id, type, amount, date, time, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (account_id, category_id, tx_type, amount, tx_date, time_str, description))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'id': new_id,
        'message': f"{tx_type.capitalize()} of ₹{amount:,.2f} recorded successfully!"
    }), 201

@app.route('/api/transactions/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
    tx = cursor.fetchone()
    if not tx:
        conn.close()
        return jsonify({'error': 'Transaction not found'}), 404

    data = request.get_json() or {}
    account_id = data.get('account_id', tx['account_id'])
    category_id = data.get('category_id') or None
    tx_type = data.get('type', tx['type'])
    tx_date = data.get('date', tx['date'])
    description = data.get('description', tx['description']).strip()
    time_str = data.get('time', tx['time'])

    today_str = date.today().isoformat()

    if not tx_date:
        return jsonify({'error': 'Transaction date is required'}), 400

    if tx_date < '2026-10-01':
        return jsonify({'error': 'Dates prior to October 2026 are not accessible.'}), 400

    if tx_date > today_str:
        return jsonify({'error': f'Date {tx_date} is locked! You can only record transactions for today ({today_str}) or past dates.'}), 400

    if tx_type not in ('credit', 'debit'):
        return jsonify({'error': 'Transaction type must be credit or debit'}), 400

    try:
        amount = float(data.get('amount', tx['amount']))
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount value'}), 400

    # Check account exists
    cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Selected account does not exist'}), 404

    cursor.execute("""
        UPDATE transactions
        SET account_id = ?, category_id = ?, type = ?, amount = ?, date = ?, time = ?, description = ?
        WHERE id = ?
    """, (account_id, category_id, tx_type, amount, tx_date, time_str, description, tx_id))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f"Transaction updated successfully!"
    })

@app.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Transaction removed'})

# ----------------- OVERVIEW STATS API -----------------
@app.route('/api/stats/overview', methods=['GET'])
def get_overview_stats():
    conn = database.get_db()
    cursor = conn.cursor()
    
    # Net worth (sum of all current balances)
    accounts = database.get_accounts_with_balances()
    total_net_worth = sum(a['current_balance'] for a in accounts)

    # Monthly stats for current month
    current_month_prefix = date.today().strftime('%Y-%m') + '%'
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as month_credits,
            SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as month_debits,
            COUNT(*) as tx_count
        FROM transactions
        WHERE date LIKE ?
    """, (current_month_prefix,))
    month_row = cursor.fetchone()
    month_credits = month_row['month_credits'] or 0.0
    month_debits = month_row['month_debits'] or 0.0
    tx_count = month_row['tx_count'] or 0

    # Top spending categories for this month
    cursor.execute("""
        SELECT 
            c.name, c.icon, c.color,
            SUM(t.amount) as total_spent
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.type = 'debit' AND t.date LIKE ?
        GROUP BY c.id
        ORDER BY total_spent DESC
        LIMIT 5
    """, (current_month_prefix,))
    top_categories = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        'net_worth': total_net_worth,
        'month_credits': month_credits,
        'month_debits': month_debits,
        'month_savings': month_credits - month_debits,
        'tx_count': tx_count,
        'top_categories': top_categories
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
