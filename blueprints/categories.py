from flask import Blueprint, request, jsonify
import database

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@categories_bp.route('', methods=['GET'])
@categories_bp.route('/', methods=['GET'])
def get_categories():
    """Retrieve all categories sorted by type and name."""
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY type ASC, name ASC")
    rows = cursor.fetchall()
    categories = [dict(r) for r in rows]
    conn.close()
    return jsonify(categories)

@categories_bp.route('', methods=['POST'])
@categories_bp.route('/', methods=['POST'])
def add_category():
    """Create a new expense or income category."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    cat_type = data.get('type', 'debit')
    icon = data.get('icon', '🏷️').strip()
    color = data.get('color', '#64748B')

    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    if cat_type not in ('debit', 'credit', 'both'):
        return jsonify({'error': 'Invalid category type'}), 400

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO categories (name, type, icon, color)
        VALUES (?, ?, ?, ?)
    """, (name, cat_type, icon or '🏷️', color))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True, 
        'category': {
            'id': new_id, 
            'name': name, 
            'type': cat_type, 
            'icon': icon, 
            'color': color
        }
    }), 201

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category by ID."""
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Category deleted successfully'})
