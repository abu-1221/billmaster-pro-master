"""
Products API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows, log_activity, admin_required, login_required

products_bp = Blueprint('products', __name__)


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

@login_required
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
        
        sql = """
            SELECT p.*, c.name as category_name 
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

@login_required
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

@admin_required
def create_product():
    """Create new product"""
    try:
        data = request.get_json() or {}
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category_id = data.get('category_id')
        price = float(data.get('price', 0))
        cost_price = float(data.get('cost_price', 0))
        stock_quantity = int(data.get('stock_quantity', 0))
        min_stock_level = int(data.get('min_stock_level', 5))
        unit = data.get('unit', 'pcs').strip()
        barcode = data.get('barcode', '').strip()
        is_active = 1 if data.get('is_active', True) else 0
        
        if not name or price <= 0:
            return jsonify({'success': False, 'message': 'Name and valid price are required'})
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (name, description, category_id, price, cost_price, stock_quantity, min_stock_level, unit, barcode, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, int(category_id) if category_id else None, price, cost_price, stock_quantity, min_stock_level, unit, barcode, is_active))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        log_activity(conn, session.get('user_id', 1), 'CREATE', 'PRODUCTS', f"Created product: {name} (ID: {new_id})")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product created successfully', 'id': new_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to create product: {str(e)}'})

@admin_required
def update_product():
    """Update existing product"""
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
        if 'cost_price' in data:
            updates.append("cost_price = ?")
            params.append(float(data['cost_price']))
        if 'stock_quantity' in data:
            updates.append("stock_quantity = ?")
            params.append(int(data['stock_quantity']))
        if 'min_stock_level' in data:
            updates.append("min_stock_level = ?")
            params.append(int(data['min_stock_level']))
        if 'unit' in data:
            updates.append("unit = ?")
            params.append(data['unit'])
        if 'barcode' in data:
            updates.append("barcode = ?")
            params.append(data['barcode'])
        if 'is_active' in data:
            updates.append("is_active = ?")
            params.append(1 if data['is_active'] else 0)
        
        if not updates:
            return jsonify({'success': False, 'message': 'No fields to update'})
        
        params.append(prod_id)
        sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        
        log_activity(conn, session.get('user_id', 1), 'UPDATE', 'PRODUCTS', f"Updated product ID: {prod_id}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def delete_product():
    """Soft delete product (mark as inactive)"""
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
        
        log_activity(conn, session.get('user_id', 1), 'DELETE', 'PRODUCTS', f"Soft-deleted product ID: {prod_id}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def update_stock():
    """Update product stock quantity"""
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
        
        log_activity(conn, session.get('user_id', 1), 'STOCK_UPDATE', 'PRODUCTS', f"Updated stock for ID: {prod_id} (Op: {operation}, Qty: {quantity})")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
