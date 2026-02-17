"""
Expenses API Routes
BillMaster Pro - Professional Backend
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, log_activity, admin_required

expenses_bp = Blueprint('expenses', __name__)

def get_current_user_id():
    return session.get('user_id', 1)

@expenses_bp.route('/expenses.php', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def expenses_handler():
    """Handle expense requests - maintains PHP-style URL compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'list':
        return list_expenses()
    elif action == 'create':
        return create_expense()
    elif action == 'delete':
        return delete_expense()
    elif action == 'summary':
        return get_summary()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

@admin_required
def list_expenses():
    """List all expenses with filtering"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, u.full_name as recorder_name 
            FROM expenses e 
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.date DESC, e.created_at DESC 
            LIMIT ?
        """, (limit,))
        
        expenses = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': expenses})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def create_expense():
    """Add a new business expense"""
    try:
        data = request.get_json() or {}
        category = data.get('category', '').strip()
        amount = float(data.get('amount', 0))
        description = data.get('description', '').strip()
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if not category or amount <= 0:
            return jsonify({'success': False, 'message': 'Valid category and amount required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        user_id = get_current_user_id()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (category, amount, description, date, user_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (category, amount, description, date, user_id))
        
        conn.commit()
        log_activity(conn, user_id, 'CREATE', 'EXPENSES', f"Added {category} expense: {amount}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Expense recorded successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def delete_expense():
    """Remove an expense entry"""
    try:
        expense_id = request.args.get('id', type=int)
        if not expense_id:
            return jsonify({'success': False, 'message': 'Expense ID missing'})
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        
        log_activity(conn, get_current_user_id(), 'DELETE', 'EXPENSES', f"Deleted expense ID: {expense_id}")
        
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def get_summary():
    """Get expense summary for charts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Category breakdown
        cursor.execute("""
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE date >= DATE('now', '-30 days')
            GROUP BY category
        """)
        breakdown = dict_list_from_rows(cursor.fetchall())
        
        # Total for current month
        cursor.execute("SELECT SUM(amount) as month_total FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
        month_total = dict_from_row(cursor.fetchone())['month_total'] or 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'breakdown': breakdown,
                'monthly_total': float(month_total)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
