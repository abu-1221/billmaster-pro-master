"""
Categories API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, admin_required, login_required

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories.php', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def categories_handler():
    """Handle category requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'list':
        return list_categories()
    elif action == 'get':
        return get_category()
    elif action == 'create':
        return create_category()
    elif action == 'update':
        return update_category()
    elif action == 'delete':
        return delete_category()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

@login_required
def list_categories():
    """List all categories with product count"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, COUNT(p.id) as product_count 
            FROM categories c 
            LEFT JOIN products p ON c.id = p.category_id AND p.is_active = 1
            GROUP BY c.id 
            ORDER BY c.name ASC
        """)
        categories = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': categories})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_category():
    """Get single category by ID"""
    try:
        cat_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        category = dict_from_row(row) if row else None
        cursor.close()
        conn.close()
        
        if category:
            return jsonify({'success': True, 'data': category})
        else:
            return jsonify({'success': False, 'message': 'Category not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def create_category():
    """Create new category"""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Category name is required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Category created', 'id': new_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def update_category():
    """Update existing category"""
    try:
        data = request.get_json() or {}
        cat_id = data.get('id', 0)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not cat_id or not name:
            return jsonify({'success': False, 'message': 'Valid ID and name required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("UPDATE categories SET name = ?, description = ? WHERE id = ?", 
                      (name, description, cat_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Category updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def delete_category():
    """Delete category"""
    try:
        cat_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Check if category has products
        cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category_id = ? AND is_active = 1", (cat_id,))
        result = dict_from_row(cursor.fetchone())
        
        if result and result['cnt'] > 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot delete: category has active products'})
        
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Category deleted'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
