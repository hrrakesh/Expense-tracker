import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    """FinTrackPro Application Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-expense-tracker-2026')
    BASE_DIR = BASE_DIR
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'logos')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max logo upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'}

    # Application Security PIN (default: 3201)
    APP_PIN = os.environ.get('APP_PIN', '3201')

    # Calendar constraints
    START_YEAR = 2026
    START_MONTH = 10
