"""
Customers API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows

customers_bp = Blueprint('customers', __name__)

def is_logged_in():
    return session.get('logged_in', False)

@customers_bp.route('/customers.php', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def customers_handler():
    """Handle customer requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'list':
        return list_customers()
    elif action == 'get':
        return get_customer()
    elif action == 'create':
        return create_customer()
    elif action == 'update':
        return update_customer()
    elif action == 'delete':
        return delete_customer()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

def list_customers():
    """List all customers with order stats"""
    try:
        search = request.args.get('search', '')
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        if search:
            search_param = f'%{search}%'
            cursor.execute("""
                SELECT c.*, 
                       COUNT(DISTINCT i.id) as total_orders,
                       COALESCE(SUM(i.total_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                WHERE c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?
                GROUP BY c.id 
                ORDER BY c.name ASC
            """, (search_param, search_param, search_param))
        else:
            cursor.execute("""
                SELECT c.*, 
                       COUNT(DISTINCT i.id) as total_orders,
                       COALESCE(SUM(i.total_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                GROUP BY c.id 
                ORDER BY c.name ASC
            """)
        
        customers = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': customers})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_customer():
    """Get single customer with recent invoices"""
    try:
        cust_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (cust_id,))
        row = cursor.fetchone()
        customer = dict_from_row(row) if row else None
        
        if customer:
            # Get recent invoices
            cursor.execute("""
                SELECT * FROM invoices 
                WHERE customer_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (cust_id,))
            invoices = dict_list_from_rows(cursor.fetchall())
            customer['invoices'] = invoices
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'data': customer})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Customer not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def create_customer():
    """Create new customer"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Customer name is required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address) 
            VALUES (?, ?, ?, ?)
        """, (name, phone, email, address))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Customer created', 'id': new_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def update_customer():
    """Update existing customer"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json() or {}
        cust_id = data.get('id', 0)
        
        if not cust_id:
            return jsonify({'success': False, 'message': 'Invalid customer ID'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        # Build update query dynamically
        updates = []
        params = []
        
        if 'name' in data:
            updates.append("name = ?")
            params.append(data['name'])
        if 'phone' in data:
            updates.append("phone = ?")
            params.append(data['phone'])
        if 'email' in data:
            updates.append("email = ?")
            params.append(data['email'])
        if 'address' in data:
            updates.append("address = ?")
            params.append(data['address'])
        
        if not updates:
            return jsonify({'success': False, 'message': 'No fields to update'})
        
        params.append(cust_id)
        sql = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Customer updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def delete_customer():
    """Delete customer"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        cust_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Customer deleted'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
