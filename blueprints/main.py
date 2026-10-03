from datetime import date
from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main application dashboard."""
    today = date.today().isoformat()
    app_pin = current_app.config.get('APP_PIN', '3201')
    return render_template('index.html', today=today, app_pin=app_pin)
