from .main import main_bp
from .auth import auth_bp
from .accounts import accounts_bp
from .categories import categories_bp
from .calendar import calendar_bp
from .transactions import transactions_bp
from .stats import stats_bp

def register_blueprints(app):
    """Register all modular application blueprints with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(stats_bp)

__all__ = [
    'register_blueprints',
    'main_bp',
    'auth_bp',
    'accounts_bp',
    'categories_bp',
    'calendar_bp',
    'transactions_bp',
    'stats_bp'
]
