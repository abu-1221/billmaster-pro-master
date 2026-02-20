"""
Analytics API Routes
BillMaster Pro - Python/Flask Backend (SQLite)
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, dict_from_row, dict_list_from_rows

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics.php', methods=['GET', 'OPTIONS'])
def analytics_handler():
    """Handle analytics requests - maintains PHP-style URL for frontend compatibility"""
    if request.method == 'OPTIONS':
        return '', 200
    
    action = request.args.get('action', '')
    
    if action == 'dashboard':
        return dashboard_stats()
    elif action == 'sales_chart':
        return sales_chart()
    elif action == 'payment_methods':
        return payment_methods()
    elif action == 'top_products':
        return top_products()
    elif action == 'low_stock':
        return low_stock()
    elif action == 'hourly_sales':
        return hourly_sales()
    elif action == 'recent_invoices':
        return recent_invoices()
    elif action == 'monthly':
        return monthly_stats()
    elif action == 'customer_stats':
        return customer_stats()
    elif action == 'summary':
        return summary()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

def dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Today's stats
        cursor.execute("""
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_revenue
            FROM invoices 
            WHERE DATE(created_at) = DATE('now')
        """)
        today = dict_from_row(cursor.fetchone()) or {'invoices': 0, 'revenue': 0, 'paid_revenue': 0, 'pending_revenue': 0}
        
        # Yesterday's stats
        cursor.execute("""
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE DATE(created_at) = DATE('now', '-1 day')
        """)
        yesterday = dict_from_row(cursor.fetchone()) or {'invoices': 0, 'revenue': 0}
        
        # This month's stats
        cursor.execute("""
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """)
        month = dict_from_row(cursor.fetchone()) or {'invoices': 0, 'revenue': 0}
        
        # Products count
        cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
        products = dict_from_row(cursor.fetchone())['cnt']
        
        # Customers count
        cursor.execute("SELECT COUNT(*) as cnt FROM customers")
        customers = dict_from_row(cursor.fetchone())['cnt']
        
        # Items sold today
        cursor.execute("""
            SELECT COALESCE(SUM(ii.quantity), 0) as items_sold
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE DATE(i.created_at) = DATE('now')
        """)
        items_sold = dict_from_row(cursor.fetchone())['items_sold']
        
        cursor.close()
        conn.close()
        
        # Calculate growth percentage
        revenue_growth = 0
        if float(yesterday['revenue']) > 0:
            revenue_growth = round(((float(today['revenue']) - float(yesterday['revenue'])) / float(yesterday['revenue'])) * 100, 1)
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'invoices': int(today['invoices']),
                    'revenue': float(today['revenue']),
                    'paid_revenue': float(today['paid_revenue']),
                    'pending_revenue': float(today['pending_revenue']),
                    'items_sold': int(items_sold)
                },
                'yesterday': {
                    'invoices': int(yesterday['invoices']),
                    'revenue': float(yesterday['revenue'])
                },
                'month': {
                    'invoices': int(month['invoices']),
                    'revenue': float(month['revenue'])
                },
                'revenue_growth': revenue_growth,
                'products': int(products),
                'customers': int(customers)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def sales_chart():
    """Get sales data for chart"""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        data = []
        
        for i in range(days - 1, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(total_amount), 0) as total,
                    COUNT(*) as count,
                    COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid
                FROM invoices 
                WHERE DATE(created_at) = ?
            """, (date,))
            row = dict_from_row(cursor.fetchone()) or {'total': 0, 'count': 0, 'paid': 0}
            data.append({
                'date': date,
                'total': float(row['total']),
                'count': int(row['count']),
                'paid': float(row['paid'])
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def payment_methods():
    """Get payment methods breakdown"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                payment_method, 
                SUM(total_amount) as total, 
                COUNT(*) as count
            FROM invoices
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY payment_method
            ORDER BY total DESC
        """)
        rows = dict_list_from_rows(cursor.fetchall())
        
        # Calculate percentage
        total_sum = sum(float(row['total']) for row in rows) if rows else 0
        data = []
        for row in rows:
            row['total'] = float(row['total']) if row['total'] else 0
            row['count'] = int(row['count'])
            row['percentage'] = round(row['total'] * 100 / total_sum, 1) if total_sum > 0 else 0
            data.append(row)
        
        cursor.close()
        conn.close()
        
        if not data:
            data = [{'payment_method': 'cash', 'total': 0, 'count': 0, 'percentage': 0}]
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def top_products():
    """Get top selling products"""
    try:
        limit = request.args.get('limit', 5, type=int)
        days = request.args.get('days', 30, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id,
                p.name, 
                p.price as unit_price,
                SUM(ii.quantity) as sold, 
                SUM(ii.total_price) as revenue,
                ROUND(AVG(ii.unit_price), 2) as avg_price
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.created_at >= DATE('now', ? || ' days')
            GROUP BY p.id, p.name, p.price
            ORDER BY revenue DESC
            LIMIT ?
        """, (f'-{days}', limit))
        data = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Convert types
        for row in data:
            row['sold'] = int(row['sold'])
            row['revenue'] = float(row['revenue'])
            row['unit_price'] = float(row['unit_price'])
            row['avg_price'] = float(row['avg_price'])
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def low_stock():
    """Get products with low stock"""
    try:
        threshold = request.args.get('threshold', 10, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, stock_quantity, unit, price
            FROM products
            WHERE is_active = 1 AND stock_quantity <= ?
            ORDER BY stock_quantity ASC
            LIMIT 10
        """, (threshold,))
        data = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Convert types
        for row in data:
            row['stock_quantity'] = int(row['stock_quantity'])
            row['price'] = float(row['price'])
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def hourly_sales():
    """Get hourly sales breakdown for today"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                CAST(strftime('%H', created_at) AS INTEGER) as hour,
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE DATE(created_at) = DATE('now')
            GROUP BY hour
            ORDER BY hour ASC
        """)
        result = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Initialize all hours with 0
        hourly_data = {i: {'hour': i, 'invoices': 0, 'revenue': 0} for i in range(24)}
        
        # Fill in actual data
        for row in result:
            hour = int(row['hour'])
            hourly_data[hour] = {
                'hour': hour,
                'invoices': int(row['invoices']),
                'revenue': float(row['revenue'])
            }
        
        return jsonify({'success': True, 'data': list(hourly_data.values())})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def recent_invoices():
    """Get recent invoices"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                i.id,
                i.invoice_number,
                i.total_amount,
                i.payment_method,
                i.payment_status,
                i.created_at,
                c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.created_at DESC
            LIMIT ?
        """, (limit,))
        data = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Convert types
        for row in data:
            row['total_amount'] = float(row['total_amount'])
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def monthly_stats():
    """Get monthly statistics"""
    try:
        months = request.args.get('months', 6, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        data = []
        
        for i in range(months - 1, -1, -1):
            date = datetime.now() - timedelta(days=i*30)
            month = date.strftime('%Y-%m')
            cursor.execute("""
                SELECT 
                    COUNT(*) as invoices,
                    COALESCE(SUM(total_amount), 0) as revenue,
                    COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid
                FROM invoices 
                WHERE strftime('%Y-%m', created_at) = ?
            """, (month,))
            row = dict_from_row(cursor.fetchone()) or {'invoices': 0, 'revenue': 0, 'paid': 0}
            data.append({
                'month': month,
                'month_name': date.strftime('%b %Y'),
                'invoices': int(row['invoices']),
                'revenue': float(row['revenue']),
                'paid': float(row['paid'])
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def customer_stats():
    """Get top customers by spending"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.phone,
                COUNT(i.id) as total_orders,
                COALESCE(SUM(i.total_amount), 0) as total_spent,
                MAX(i.created_at) as last_order
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            GROUP BY c.id, c.name, c.phone
            HAVING total_orders > 0
            ORDER BY total_spent DESC
            LIMIT ?
        """, (limit,))
        data = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        
        # Convert objects
        for row in data:
            row['total_orders'] = int(row['total_orders'])
            row['total_spent'] = float(row['total_spent'])
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def summary():
    """Get complete summary for reports"""
    try:
        period = request.args.get('period', 'today')
        
        # Build date filter
        if period == 'today':
            date_filter = "DATE(created_at) = DATE('now')"
        elif period == 'week':
            date_filter = "created_at >= DATE('now', '-7 days')"
        elif period == 'month':
            date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        elif period == 'year':
            date_filter = "strftime('%Y', created_at) = strftime('%Y', 'now')"
        else:
            date_filter = "1=1"
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_amount,
                COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_amount,
                COALESCE(AVG(total_amount), 0) as avg_order_value,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM invoices 
            WHERE {date_filter}
        """)
        summary_data = dict_from_row(cursor.fetchone()) or {}
        
        # Items sold
        cursor.execute(f"""
            SELECT COALESCE(SUM(ii.quantity), 0) as items_sold
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE {date_filter}
        """)
        items_result = dict_from_row(cursor.fetchone())
        items_sold = items_result['items_sold'] if items_result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'period': period,
                'total_invoices': int(summary_data.get('total_invoices', 0)),
                'total_revenue': float(summary_data.get('total_revenue', 0)),
                'paid_amount': float(summary_data.get('paid_amount', 0)),
                'pending_amount': float(summary_data.get('pending_amount', 0)),
                'avg_order_value': float(summary_data.get('avg_order_value', 0)),
                'unique_customers': int(summary_data.get('unique_customers', 0)),
                'items_sold': int(items_sold)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
