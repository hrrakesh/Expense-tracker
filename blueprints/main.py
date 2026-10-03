from datetime import date
from flask import Blueprint, render_template, current_app, jsonify
import database

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main application dashboard after verifying database connection."""
    # Check for active database connection before loading the page
    if not database.check_db_connection():
        # If DB connection failed, show the blank page
        return ""

    today = date.today().isoformat()
    app_pin = current_app.config.get('APP_PIN', '3201')
    return render_template('index.html', today=today, app_pin=app_pin, db_connected=True)

@main_bp.route('/api/db-status', methods=['GET'])
def db_status():
    """Endpoint to check database connection status."""
    connected = database.check_db_connection()
    if connected:
        return jsonify({
            'status': 'connected',
            'success': True,
            'message': 'Database connected successfully'
        })
    return jsonify({
        'status': 'disconnected',
        'success': False,
        'error': 'Database connection failed'
    }), 503
