from datetime import date
from flask import Blueprint, jsonify
import database

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@stats_bp.route('/overview', methods=['GET'])
def get_overview_stats():
    """Retrieve financial overview stats including net worth, monthly flow, and top categories."""
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
