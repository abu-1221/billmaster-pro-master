"""
Invoices API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
<<<<<<< HEAD
import sqlite3
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, generate_invoice_number

invoices_bp = Blueprint('invoices', __name__)

def is_logged_in():
    return session.get('logged_in', False)

=======
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, generate_invoice_number, admin_required, login_required, get_settings

invoices_bp = Blueprint('invoices', __name__)

>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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

<<<<<<< HEAD
=======
@admin_required
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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

<<<<<<< HEAD
=======
@login_required
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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
<<<<<<< HEAD
            # Parse payment details
            if invoice.get('payment_details'):
                try:
                    invoice['payment_details'] = json.loads(invoice['payment_details'])
                except:
                    invoice['payment_details'] = {}
            else:
                invoice['payment_details'] = {}

            # Get invoice items
            cursor.execute("""
                SELECT ii.*, p.name as product_name, ii.tax_rate, ii.tax_amount
=======
            # Get invoice items
            cursor.execute("""
                SELECT ii.*, p.name as product_name 
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
                FROM invoice_items ii 
                LEFT JOIN products p ON ii.product_id = p.id 
                WHERE ii.invoice_id = ?
            """, (inv_id,))
            items = dict_list_from_rows(cursor.fetchall())
            invoice['items'] = items
<<<<<<< HEAD
            invoice['discount_percentage'] = invoice.get('discount_percentage', 0)
=======
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'data': invoice})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invoice not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

<<<<<<< HEAD
def create_invoice():
    """Create new invoice with items"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
=======
@login_required
def create_invoice():
    """Create new invoice with items"""
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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
<<<<<<< HEAD
        subtotal = 0
        total_tax_amount = 0
        processed_items = []
=======
        subtotal = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
<<<<<<< HEAD
        # Get global tax rate
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'tax_rate'")
        tax_row = cursor.fetchone()
        global_tax = float(tax_row['setting_value']) if tax_row else 0
        
        for item in items:
            prod_id = int(item['product_id'])
            qty = int(item['quantity'])
            u_price = float(item['unit_price'])
            
            # Fetch effective tax rate for this product
            cursor.execute(f"""
                SELECT p.name, COALESCE(p.gst_percentage, c.gst_percentage, {global_tax}) as effective_gst
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (prod_id,))
            prod_data = cursor.fetchone()
            
            tax_rate = float(prod_data['effective_gst']) if prod_data else 0
            item_subtotal = qty * u_price
            item_tax = item_subtotal * (tax_rate / 100)
            item_total = item_subtotal + item_tax
            
            subtotal += item_subtotal
            total_tax_amount += item_tax
            
            processed_items.append({
                'product_id': prod_id,
                'name': prod_data['name'] if prod_data else 'Unknown',
                'quantity': qty,
                'unit_price': u_price,
                'tax_rate': tax_rate,
                'tax_amount': item_tax,
                'total_price': item_total
            })
            
        discount_percentage = float(data.get('discount_percentage', 0))
        total_before_discount = subtotal + total_tax_amount
        
        if discount_percentage > 0:
            discount_amount = total_before_discount * (discount_percentage / 100)
        else:
            discount_amount = float(data.get('discount_amount', 0))
            if total_before_discount > 0:
                discount_percentage = (discount_amount / total_before_discount) * 100
            
        total_amount = total_before_discount - discount_amount
        
        user_id = get_current_user_id()
        
        try:
            # Insert invoice (retry if invoice_number collides)
            invoice_id = None
            invoice_number = None
            for _ in range(5):
                invoice_number = generate_invoice_number(conn)
                try:
                    payment_details = json.dumps(data.get('payment_details', {}))
                    cursor.execute("""
                        INSERT INTO invoices (invoice_number, customer_id, user_id, subtotal, tax_rate, tax_amount, 
                                             discount_amount, discount_percentage, total_amount, payment_method, payment_status, payment_details) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (invoice_number, customer_id, user_id, subtotal, 0, total_tax_amount,
                          discount_amount, discount_percentage, total_amount, payment_method, payment_status, payment_details))
                    invoice_id = cursor.lastrowid
                    break
                except sqlite3.IntegrityError as e:
                    # Only retry on unique invoice number collisions
                    if "invoice_number" in str(e).lower() or "unique constraint" in str(e).lower():
                        continue
                    raise

            if invoice_id is None:
                raise Exception("Failed to generate a unique invoice number. Please try again.")
            
            # Insert items and update stock
            for item in processed_items:
                product_id = item['product_id']
                quantity = item['quantity']
                unit_price = item['unit_price']
                tax_rate = item['tax_rate']
                tax_amount = item['tax_amount']
                total_price = item['total_price']
                product_name = item['name']
                
                # Insert invoice item
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, tax_rate, tax_amount, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (invoice_id, product_id, product_name, quantity, unit_price, tax_rate, tax_amount, total_price))
=======
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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
                
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

<<<<<<< HEAD
def update_status():
    """Update invoice payment status"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
=======
@admin_required
def update_status():
    """Update invoice payment status"""
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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

<<<<<<< HEAD
=======
@admin_required
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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
