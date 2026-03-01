"""
Authentication API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import bcrypt
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth.php', methods=['GET', 'POST', 'OPTIONS'])
def auth_handler():
    """Handle authentication requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'login':
        return login()
    elif action == 'logout':
        return logout()
    elif action == 'check':
        return check_auth()
    elif action == 'register':
        return register()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

def login():
    """Handle user login"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, full_name, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        user = dict_from_row(row) if row else None
        cursor.close()
        conn.close()
        
        if user:
            # Check password
            stored_password = user['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                # Set session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['role'] = user['role']
                session['logged_in'] = True
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'full_name': user['full_name'],
                        'role': user['role']
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Invalid password'})
        else:
            return jsonify({'success': False, 'message': 'User not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

def check_auth():
    """Check if user is logged in"""
    if session.get('logged_in'):
        return jsonify({
            'success': True,
            'user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role')
            }
        })
    return jsonify({'success': False, 'message': 'Not logged in'})

def register():
    """Register new user (admin only)"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'staff')
        
        if not username or not password or not full_name:
            return jsonify({'success': False, 'message': 'Required fields missing'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Create user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO users (username, password, full_name, email, role) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, full_name, email, role))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User created'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
