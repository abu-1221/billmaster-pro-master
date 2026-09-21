import sqlite3
import os
import bcrypt
from functools import wraps
from datetime import datetime
import json
from flask import session, jsonify

# Database path for SQLite
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'billmaster.db')

def login_required(f):
    """Decorator to ensure user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user has admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Administrative access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_connection():
    """Create and return database connection (PostgreSQL, MySQL or SQLite)"""
    db_url = os.environ.get('DATABASE_URL')
    
    try:
        if db_url:
            if db_url.startswith('postgres'):
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(db_url)
                return conn
            elif db_url.startswith('mysql'):
                import mysql.connector
                # Complete MySQL connection logic
                db_config = os.environ.get('MYSQL_CONFIG')
                if db_config:
                    config = json.loads(db_config)
                    conn = mysql.connector.connect(**config)
                    return conn
        
        # Fallback to SQLite
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        create_tables(conn)
        return conn
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_cursor(conn):
    """Get appropriate cursor for the connection type"""
    if hasattr(conn, 'row_factory'): # SQLite
        return conn.cursor()
    else: # PostgreSQL/MySQL
        try:
            import psycopg2.extras
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except ImportError:
            return conn.cursor(dictionary=True) # MySQL

def dict_from_row(row):
    """Convert row result to dictionary"""
    if row is None:
        return None
    try:
        return dict(row)
    except (TypeError, ValueError):
        return row

def dict_list_from_rows(rows):
    """Convert list of rows to list of dictionaries"""
    if not rows:
        return []
    return [dict_from_row(row) for row in rows]

def create_tables(conn):
    """Create all required tables for BillMaster Pro"""
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff', 'manager')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            price REAL NOT NULL,
            cost_price REAL DEFAULT 0,
            stock_quantity INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            unit TEXT DEFAULT 'pcs',
            barcode TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_number TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT UNIQUE,
            address TEXT,
            city TEXT,
            customer_type TEXT DEFAULT 'individual' CHECK(customer_type IN ('individual', 'business', 'institute')),
            status TEXT DEFAULT 'new' CHECK(status IN ('new', 'regular')),
            loyalty_points INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration for existing tables: Add customer_number and status if they don't exist
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN customer_number TEXT UNIQUE")
    except sqlite3.OperationalError: pass
    
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN status TEXT DEFAULT 'new' CHECK(status IN ('new', 'regular'))")
    except sqlite3.OperationalError: pass
    
    # Invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            user_id INTEGER,
            subtotal REAL NOT NULL,
            tax_rate REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'upi', 'bank_transfer', 'credit')),
            payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('paid', 'pending', 'partial', 'cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Invoice items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date DATE DEFAULT (DATE('now')),
            user_id INTEGER,
            receipt_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Activity Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            module TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Initial Data Logic
    init_db_data(conn)
    cursor.close()

def init_db_data(conn):
    """Seed the database with initial/default data"""
    cursor = conn.cursor()
    
    # Admin User
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", 
                      ('admin', hashed, 'System Administrator', 'admin'))
    
    # Default Settings
    defaults = [
        ('business_name', 'BillMaster Pro'),
        ('business_address', 'Premium Plaza, Sector 15, Digital City'),
        ('business_phone', '+91 90000 12345'),
        ('tax_rate', '18'),
        ('currency_symbol', '₹'),
        ('invoice_prefix', 'BM'),
        ('low_stock_threshold', '10'),
        ('regular_customer_discount', '10')
    ]
    for key, val in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES (?, ?)", (key, val))
    
    # Sample Categories & Products (only if empty)
    cursor.execute("SELECT count(*) as count FROM categories")
    if dict_from_row(cursor.fetchone())['count'] == 0:
        cats = [('Beverages', 'Refreshing drinks'), ('Bakery', 'Freshly baked items'), ('Groceries', 'Daily essentials')]
        for c in cats:
            cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", c)
        
        products = [
            ('Cappuccino', 'Rich espresso with milk', 1, 120.00, 50, 'cup'),
            ('Blueberry Muffin', 'Soft muffin with berries', 2, 85.00, 30, 'pcs'),
            ('Organic Honey', 'Pure forest honey', 3, 450.00, 20, 'bottle')
        ]
        for p in products:
            cursor.execute("INSERT INTO products (name, description, category_id, price, stock_quantity, unit) VALUES (?, ?, ?, ?, ?, ?)", p)

    conn.commit()

def get_settings(conn):
    """Get all settings as dictionary"""
    cursor = conn.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM settings")
    settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    cursor.close()
    return settings

def log_activity(conn, user_id, action, module, details=None):
    """Record user activity in the logs"""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activity_logs (user_id, action, module, details) VALUES (?, ?, ?, ?)",
                  (user_id, action, module, details))
    conn.commit()
    cursor.close()

def generate_invoice_number(conn):
    """Generate professional unique invoice number"""
    settings = get_settings(conn)
    prefix = settings.get('invoice_prefix', 'INV')
    date_str = datetime.now().strftime('%y%m%d')
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM invoices WHERE DATE(created_at) = DATE('now')")
    count = dict_from_row(cursor.fetchone())['count'] + 1
    cursor.close()
    
    return f"{prefix}-{date_str}-{str(count).zfill(4)}"

def generate_customer_number(conn):
    """Generate unique sequential customer number"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM customers")
    count = cursor.fetchone()['count'] + 1
    cursor.close()
    return f"CUST-{str(count).zfill(5)}"
