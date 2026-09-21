"""
Invoices API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, generate_invoice_number, admin_required, login_required, get_settings

invoices_bp = Blueprint('invoices', __name__)

def get_current_user_id():
    return session.get('user_id', 1)

@invoices_bp.route('/invoices.php', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def invoices_handler():
    """Handle invoice requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'list':
        return list_invoices()
    elif action == 'get':
        return get_invoice()
    elif action == 'create':
        return create_invoice()
    elif action == 'update_status':
        return update_status()
    elif action == 'today_summary':
        return today_summary()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

@admin_required
def list_invoices():
    """List all invoices with optional status filter"""
    try:
        status = request.args.get('status', '')
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT i.*, c.name as customer_name 
                FROM invoices i 
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.payment_status = ?
                ORDER BY i.created_at DESC 
                LIMIT 100
            """, (status,))
        else:
            cursor.execute("""
                SELECT i.*, c.name as customer_name 
                FROM invoices i 
                LEFT JOIN customers c ON i.customer_id = c.id
                ORDER BY i.created_at DESC 
                LIMIT 100
            """)
        
        invoices = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': invoices})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@login_required
def get_invoice():
    """Get single invoice with items"""
    try:
        inv_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address
            FROM invoices i 
            LEFT JOIN customers c ON i.customer_id = c.id 
            WHERE i.id = ?
        """, (inv_id,))
        row = cursor.fetchone()
        invoice = dict_from_row(row) if row else None
        
        if invoice:
            # Get invoice items
            cursor.execute("""
                SELECT ii.*, p.name as product_name 
                FROM invoice_items ii 
                LEFT JOIN products p ON ii.product_id = p.id 
                WHERE ii.invoice_id = ?
            """, (inv_id,))
            items = dict_list_from_rows(cursor.fetchall())
            invoice['items'] = items
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'data': invoice})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invoice not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@login_required
def create_invoice():
    """Create new invoice with items"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Invalid data'})
        
        customer_id = data.get('customer_id')
        items = data.get('items', [])
        tax_rate = float(data.get('tax_rate', 0))
        discount_amount = float(data.get('discount_amount', 0))
        payment_method = data.get('payment_method', 'cash')
        payment_status = data.get('payment_status', 'paid')
        
        if not items:
            return jsonify({'success': False, 'message': 'No items in cart'})
        
        # Calculate totals
        subtotal = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Check automatic discount for regular customers
        if customer_id and discount_amount == 0:
            cursor.execute("SELECT status FROM customers WHERE id = ?", (customer_id,))
            cust = cursor.fetchone()
            if cust and cust['status'] == 'regular':
                settings = get_settings(conn)
                discount_percent = float(settings.get('regular_customer_discount', 10))
                discount_amount = subtotal * (discount_percent / 100)
                
        tax_amount = subtotal * (tax_rate / 100)
        total_amount = subtotal + tax_amount - discount_amount
        
        # Generate invoice number
        invoice_number = generate_invoice_number(conn)
        user_id = get_current_user_id()
        
        try:
            # Insert invoice
            cursor.execute("""
                INSERT INTO invoices (invoice_number, customer_id, user_id, subtotal, tax_rate, tax_amount, 
                                     discount_amount, total_amount, payment_method, payment_status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_number, customer_id, user_id, subtotal, tax_rate, tax_amount,
                  discount_amount, total_amount, payment_method, payment_status))
            
            invoice_id = cursor.lastrowid
            
            # Insert items and update stock
            for item in items:
                product_id = int(item['product_id'])
                quantity = int(item['quantity'])
                unit_price = float(item['unit_price'])
                total_price = quantity * unit_price
                
                # Get product name
                cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
                prod = cursor.fetchone()
                product_name = prod['name'] if prod else 'Unknown'
                
                # Insert invoice item
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, product_id, product_name, quantity, unit_price, total_price))
                
                # Update stock
                cursor.execute("""
                    UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?
                """, (quantity, product_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'invoice_id': invoice_id, 
                'invoice_number': invoice_number
            })
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': str(e)})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def update_status():
    """Update invoice payment status"""
    try:
        data = request.get_json() or {}
        inv_id = data.get('id', 0)
        status = data.get('status', '')
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("UPDATE invoices SET payment_status = ? WHERE id = ?", (status, inv_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def today_summary():
    """Get today's invoice summary"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_amount,
                COALESCE(SUM(total_amount), 0) as total_amount
            FROM invoices 
            WHERE DATE(created_at) = DATE('now')
        """)
        row = cursor.fetchone()
        data = dict_from_row(row) if row else {'total_invoices': 0, 'paid_amount': 0, 'total_amount': 0}
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
