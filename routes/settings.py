"""
Settings API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows

settings_bp = Blueprint('settings', __name__)

def is_logged_in():
    return session.get('logged_in', False)

def is_admin():
    return is_logged_in() and session.get('role') == 'admin'

@settings_bp.route('/settings.php', methods=['GET', 'POST', 'OPTIONS'])
def settings_handler():
    """Handle settings requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'get':
        return get_settings()
    elif action == 'update':
        return update_settings()
    elif action == 'users':
        return list_users()
    elif action == 'delete_user':
        return delete_user()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

def get_settings():
    """Get all settings"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        rows = dict_list_from_rows(cursor.fetchall())
        settings = {row['setting_key']: row['setting_value'] for row in rows}
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': settings})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def update_settings():
    """Update settings"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'Invalid data'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        for key, value in data.items():
            # Check if setting exists
            cursor.execute("SELECT id FROM settings WHERE setting_key = ?", (key,))
            if cursor.fetchone():
                cursor.execute("UPDATE settings SET setting_value = ? WHERE setting_key = ?", (value, key))
            else:
                cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)", (key, value))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Settings updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def list_users():
    """List all users (admin only)"""
    if not is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, role, created_at FROM users ORDER BY id ASC")
        users = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': users})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def delete_user():
    """Delete user (admin only)"""
    if not is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        user_id = request.args.get('id', 0, type=int)
        
        if user_id <= 1:
            return jsonify({'success': False, 'message': 'Cannot delete primary admin'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User deleted'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
