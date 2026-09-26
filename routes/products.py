"""
Products API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows

products_bp = Blueprint('products', __name__)

def is_logged_in():
    return session.get('logged_in', False)

@products_bp.route('/products.php', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def products_handler():
    """Handle product requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '') or request.form.get('action', '')
    
    if action == 'list':
        return list_products()
    elif action == 'get':
        return get_product()
    elif action == 'create':
        return create_product()
    elif action == 'update':
        return update_product()
    elif action == 'delete':
        return delete_product()
    elif action == 'update_stock':
        return update_stock()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

def list_products():
    """List all products with optional filters"""
    try:
        category_id = request.args.get('category_id')
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'true') != 'false'
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Get global tax rate from settings
        global_tax = "0"
        try:
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'tax_rate'")
            row = cursor.fetchone()
            if row:
                global_tax = row['setting_value']
        except:
            pass

        sql = f"""
            SELECT p.*, c.name as category_name, c.gst_percentage as category_gst,
                   COALESCE(p.gst_percentage, c.gst_percentage, {global_tax}) as effective_gst
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE 1=1
        """
        params = []
        
        if active_only:
            sql += " AND p.is_active = 1"
        
        if category_id:
            sql += " AND p.category_id = ?"
            params.append(int(category_id))
        
        if search:
            sql += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])
        
        sql += " ORDER BY p.name ASC"
        
        cursor.execute(sql, params)
        products = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Convert is_active to boolean
        for prod in products:
            if 'is_active' in prod:
                prod['is_active'] = bool(prod['is_active'])
        
        return jsonify({'success': True, 'data': products})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_product():
    """Get single product by ID"""
    try:
        prod_id = request.args.get('id', 0, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.id = ?
        """, (prod_id,))
        row = cursor.fetchone()
        product = dict_from_row(row) if row else None
        cursor.close()
        conn.close()
        
        if product:
            if 'is_active' in product:
                product['is_active'] = bool(product['is_active'])
            return jsonify({'success': True, 'data': product})
        else:
            return jsonify({'success': False, 'message': 'Product not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def create_product():
    """Create new product"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json() or {}
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category_id = data.get('category_id')
        price = float(data.get('price', 0))
        stock_quantity = int(data.get('stock_quantity', 0))
        unit = data.get('unit', 'pcs').strip()
        barcode = data.get('barcode', '').strip()
        is_active = 1 if data.get('is_active', True) else 0
        gst_percentage = data.get('gst_percentage')
        if gst_percentage is not None:
            gst_percentage = float(gst_percentage)
        
        if not name or price <= 0:
            return jsonify({'success': False, 'message': 'Name and valid price are required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (name, description, category_id, price, stock_quantity, unit, barcode, is_active, gst_percentage) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, int(category_id) if category_id else None, price, stock_quantity, unit, barcode, is_active, gst_percentage))
        
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product created successfully', 'id': new_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to create product: {str(e)}'})

def update_product():
    """Update existing product"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json() or {}
        prod_id = data.get('id', 0)
        
        if not prod_id:
            return jsonify({'success': False, 'message': 'Invalid product ID'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        # Build update query dynamically
        updates = []
        params = []
        
        if 'name' in data:
            updates.append("name = ?")
            params.append(data['name'])
        if 'description' in data:
            updates.append("description = ?")
            params.append(data['description'])
        if 'category_id' in data:
            updates.append("category_id = ?")
            params.append(int(data['category_id']) if data['category_id'] else None)
        if 'price' in data:
            updates.append("price = ?")
            params.append(float(data['price']))
        if 'stock_quantity' in data:
            updates.append("stock_quantity = ?")
            params.append(int(data['stock_quantity']))
        if 'unit' in data:
            updates.append("unit = ?")
            params.append(data['unit'])
        if 'barcode' in data:
            updates.append("barcode = ?")
            params.append(data['barcode'])
        if 'is_active' in data:
            updates.append("is_active = ?")
            params.append(1 if data['is_active'] else 0)
        if 'gst_percentage' in data:
            updates.append("gst_percentage = ?")
            val = data['gst_percentage']
            params.append(float(val) if val is not None and val != "" else None)
        
        if not updates:
            return jsonify({'success': False, 'message': 'No fields to update'})
        
        params.append(prod_id)
        sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def delete_product():
    """Soft delete product (mark as inactive)"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        prod_id = request.args.get('id', 0, type=int)
        
        if not prod_id:
            return jsonify({'success': False, 'message': 'Invalid product ID'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (prod_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def update_stock():
    """Update product stock quantity"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json() or {}
        prod_id = data.get('id', 0)
        quantity = int(data.get('quantity', 0))
        operation = data.get('operation', 'set')
        
        if not prod_id:
            return jsonify({'success': False, 'message': 'Invalid product ID'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        if operation == 'add':
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", 
                          (quantity, prod_id))
        elif operation == 'subtract':
            cursor.execute("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", 
                          (quantity, prod_id))
        else:
            cursor.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", 
                          (quantity, prod_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
