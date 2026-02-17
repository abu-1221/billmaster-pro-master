"""
System & Maintenance API Routes
BillMaster Pro - Professional Backend
"""

from flask import Blueprint, request, jsonify, session, send_file
import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection, DB_PATH, dict_list_from_rows, log_activity, admin_required

system_bp = Blueprint('system', __name__)

@system_bp.route('/system.php', methods=['GET', 'POST', 'OPTIONS'])
def system_handler():
    if request.method == 'OPTIONS':
        return '', 200
        
    action = request.args.get('action', '')
    
    if action == 'logs':
        return get_logs()
    elif action == 'db_stats':
        return get_db_stats()
    elif action == 'backup':
        return backup_db()
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})

@admin_required
def get_logs():
    """Get recent activity logs (Admin only)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.*, u.username 
            FROM activity_logs l 
            LEFT JOIN users u ON l.user_id = u.id 
            ORDER BY l.created_at DESC 
            LIMIT ?
        """, (limit,))
        logs = dict_list_from_rows(cursor.fetchall())
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'data': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def get_db_stats():
    """Get database size and record counts"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        tables = ['users', 'products', 'customers', 'invoices', 'expenses']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']
            
        file_size = os.path.getsize(DB_PATH) / (1024 * 1024) # MB
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'counts': stats,
                'db_size_mb': round(file_size, 2),
                'db_path': DB_PATH,
                'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_required
def backup_db():
    """Download a copy of the SQLite database"""
    try:
        backup_filename = f"billmaster_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Log the backup action
        conn = get_connection()
        log_activity(conn, session.get('user_id', 1), 'BACKUP', 'SYSTEM', 'Database backup downloaded')
        conn.close()
        
        return send_file(DB_PATH, as_attachment=True, download_name=backup_filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
