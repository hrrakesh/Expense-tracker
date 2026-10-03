import os
from flask import Flask
from config import Config
import database
from blueprints import register_blueprints

def create_app(config_class=Config):
    """FinTrackPro Application Factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database on startup
    with app.app_context():
        database.init_db()

    # Register all modular blueprints
    register_blueprints(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
