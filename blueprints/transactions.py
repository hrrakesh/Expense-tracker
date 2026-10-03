from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
import database

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transactions_bp.route('/date/<date_str>', methods=['GET'])
def get_transactions_for_date(date_str):
    """Retrieve all transactions for a specific date, optionally filtered by account."""
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

@transactions_bp.route('', methods=['POST'])
@transactions_bp.route('/', methods=['POST'])
def add_transaction():
    """Record a new credit or debit transaction with calendar locking enforcement."""
    data = request.get_json() or {}
    
    account_id = data.get('account_id')
    category_id = data.get('category_id') or None
    tx_type = data.get('type')  # 'credit' or 'debit'
    tx_date = data.get('date')  # YYYY-MM-DD
    time_str = data.get('time', datetime.now().strftime('%H:%M'))
    description = data.get('description', '').strip()
    
    today_str = date.today().isoformat()
    start_year = current_app.config.get('START_YEAR', 2026)
    start_month = current_app.config.get('START_MONTH', 10)
    min_date_str = f"{start_year:04d}-{start_month:02d}-01"

    # CRITICAL RULES: Calendar starts at 2026-10-01; no future dates beyond today allowed
    if not tx_date:
        return jsonify({'error': 'Transaction date is required'}), 400

    if tx_date < min_date_str:
        return jsonify({
            'error': f'The tracking system starts from October 1, {start_year}. Dates prior to October {start_year} are not accessible.'
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

@transactions_bp.route('/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    """Update an existing transaction."""
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
    start_year = current_app.config.get('START_YEAR', 2026)
    start_month = current_app.config.get('START_MONTH', 10)
    min_date_str = f"{start_year:04d}-{start_month:02d}-01"

    if not tx_date:
        return jsonify({'error': 'Transaction date is required'}), 400

    if tx_date < min_date_str:
        return jsonify({'error': f'Dates prior to October {start_year} are not accessible.'}), 400

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
        'message': "Transaction updated successfully!"
    })

@transactions_bp.route('/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    """Delete a transaction by ID."""
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Transaction removed'})
