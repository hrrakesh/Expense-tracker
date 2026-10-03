from flask import current_app

def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    allowed_extensions = current_app.config.get(
        'ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'}
    )
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
