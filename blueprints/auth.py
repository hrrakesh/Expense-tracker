from flask import Blueprint, request, jsonify, current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/verify-pin', methods=['POST'])
def verify_pin():
    """Verify 4-digit application access PIN."""
    data = request.get_json() or {}
    pin = str(data.get('pin', '')).strip()
    expected_pin = str(current_app.config.get('APP_PIN', '3201')).strip()

    if pin == expected_pin:
        return jsonify({'success': True, 'message': 'PIN verified successfully'})
    return jsonify({'success': False, 'error': 'Invalid PIN'}), 401
