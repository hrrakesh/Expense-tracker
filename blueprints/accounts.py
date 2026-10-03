import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import database
from .helpers import allowed_file

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')

@accounts_bp.route('', methods=['GET'])
@accounts_bp.route('/', methods=['GET'])
def get_accounts():
    """Retrieve all accounts with dynamic balance calculations."""
    accounts = database.get_accounts_with_balances()
    return jsonify(accounts)

@accounts_bp.route('', methods=['POST'])
@accounts_bp.route('/', methods=['POST'])
def add_account():
    """Create a new bank/wallet/cash account."""
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
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Check if a custom logo image was uploaded
    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = f"account_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(upload_folder, filename)
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

@accounts_bp.route('/<int:account_id>', methods=['PUT', 'POST'])
def update_account(account_id):
    """Update an existing account's details, balance, or logo."""
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

    upload_folder = current_app.config['UPLOAD_FOLDER']

    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = f"account_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
            if account['logo'] and account['logo'].startswith('/static/uploads/logos/'):
                old_file = os.path.join(upload_folder, os.path.basename(account['logo']))
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

@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an account and remove any custom uploaded logo file."""
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT logo FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Account not found'}), 404

    upload_folder = current_app.config['UPLOAD_FOLDER']

    # If it's a custom uploaded file, delete it from disk
    if row['logo'] and row['logo'].startswith('/static/uploads/logos/'):
        filename = os.path.basename(row['logo'])
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Account and all associated records deleted'})
