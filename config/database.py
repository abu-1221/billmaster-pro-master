<<<<<<< HEAD
"""
Database Configuration
BillMaster Pro - Billing & Institute Management System
Python/Flask Backend - SQLite Version
"""

import sqlite3
import bcrypt
import os
from functools import wraps

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'billmaster.db')

def get_connection():
    """Create and return database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Create tables if not exist
        create_tables(conn)
        
=======
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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
        return conn
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

<<<<<<< HEAD
def dict_from_row(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return dict(row)

def dict_list_from_rows(rows):
    """Convert list of sqlite3.Row to list of dictionaries"""
    return [dict(row) for row in rows]

def create_tables(conn):
    """Create all required tables"""
=======
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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
<<<<<<< HEAD
            role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff')),
            last_login TIMESTAMP,
=======
            role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff', 'manager')),
            is_active INTEGER DEFAULT 1,
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
<<<<<<< HEAD
    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_invoice ON invoice_items(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)")
    
=======
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
<<<<<<< HEAD
            name TEXT NOT NULL,
            description TEXT,
            gst_percentage REAL DEFAULT 0,
=======
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            image_url TEXT,
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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
<<<<<<< HEAD
            stock_quantity INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            barcode TEXT,
            is_active INTEGER DEFAULT 1,
            gst_percentage REAL DEFAULT NULL,
=======
            cost_price REAL DEFAULT 0,
            stock_quantity INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            unit TEXT DEFAULT 'pcs',
            barcode TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
<<<<<<< HEAD
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
=======
            customer_number TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT UNIQUE,
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            address TEXT,
            city TEXT,
            customer_type TEXT DEFAULT 'individual' CHECK(customer_type IN ('individual', 'business', 'institute')),
            status TEXT DEFAULT 'new' CHECK(status IN ('new', 'regular')),
<<<<<<< HEAD
            default_discount REAL DEFAULT 0,
=======
            loyalty_points INTEGER DEFAULT 0,
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
<<<<<<< HEAD
=======

    # Migration for existing tables: Add customer_number and status if they don't exist
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN customer_number TEXT UNIQUE")
    except sqlite3.OperationalError: pass
    
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN status TEXT DEFAULT 'new' CHECK(status IN ('new', 'regular'))")
    except sqlite3.OperationalError: pass
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
    
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
<<<<<<< HEAD
            discount_percentage REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'upi', 'bank_transfer', 'credit')),
            payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('paid', 'pending', 'partial', 'cancelled')),
            payment_details TEXT,
=======
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'upi', 'bank_transfer', 'credit')),
            payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('paid', 'pending', 'partial', 'cancelled')),
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
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
<<<<<<< HEAD
            tax_rate REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
=======
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    """)
<<<<<<< HEAD
=======

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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
    
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
    
<<<<<<< HEAD
    # Insert default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO users (username, password, full_name, email, role) 
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', hashed_password, 'Administrator', 'admin@billmaster.com', 'admin'))
        conn.commit()
    
    # Insert default settings if not exists
    default_settings = [
        ('shop_name', 'BillMaster Pro'),
        ('business_name', 'BillMaster Pro'),
        ('business_address', '123 Business Street, City'),
        ('business_phone', '+91 9876543210'),
        ('business_email', 'contact@billmaster.com'),
        ('tax_rate', '18'),
        ('currency_symbol', '₹'),
        ('invoice_prefix', 'INV'),
        ('upi_id', '')
    ]
    
    for key, value in default_settings:
        cursor.execute("SELECT id FROM settings WHERE setting_key = ?", (key,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)", (key, value))
    
    conn.commit()
    
    # Insert sample categories if empty
    cursor.execute("SELECT id FROM categories LIMIT 1")
    if cursor.fetchone() is None:
        sample_categories = [
            ('Beverages', 'Tea, Coffee, Soft Drinks, Juices'),
            ('Snacks', 'Chips, Biscuits, Namkeen'),
            ('Meals', 'Breakfast, Lunch, Dinner items'),
            ('Stationery', 'Pens, Notebooks, Files'),
            ('Services', 'Printing, Xerox, Lamination')
        ]
        for name, description in sample_categories:
            cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        
        # Insert sample products
        sample_products = [
            ('Tea', 'Hot tea', 1, 15.00, 100, 'cups'),
            ('Coffee', 'Hot coffee', 1, 20.00, 100, 'cups'),
            ('Samosa', 'Potato samosa', 2, 10.00, 50, 'pcs'),
            ('Sandwich', 'Veg sandwich', 3, 40.00, 30, 'pcs'),
            ('Notebook', 'Ruled notebook', 4, 30.00, 100, 'pcs'),
            ('Pen', 'Ball pen', 4, 10.00, 200, 'pcs'),
            ('Printing', 'B/W printing', 5, 2.00, 1000, 'pages'),
            ('Xerox', 'Document xerox', 5, 1.00, 1000, 'pages')
        ]
        for name, desc, cat_id, price, stock, unit in sample_products:
            cursor.execute("""
                INSERT INTO products (name, description, category_id, price, stock_quantity, unit) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, desc, cat_id, price, stock, unit))
        conn.commit()
    
    cursor.close()
=======
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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de

def get_settings(conn):
    """Get all settings as dictionary"""
    cursor = conn.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM settings")
    settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    cursor.close()
    return settings

<<<<<<< HEAD
def generate_invoice_number(conn):
    """Generate unique invoice number"""
    from datetime import datetime
    
    settings = get_settings(conn)
    prefix = settings.get('invoice_prefix', 'INV')
    date_str = datetime.now().strftime('%Y%m%d')

    base = f"{prefix}-{date_str}-"
    like_pattern = f"{base}%"

    cursor = conn.cursor()
    try:
        # Find the highest sequence for today (safe even if older invoices were deleted)
        cursor.execute(
            "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY invoice_number DESC LIMIT 1",
            (like_pattern,),
        )
        row = cursor.fetchone()
        if row and row["invoice_number"]:
            last = str(row["invoice_number"])
            try:
                last_seq = int(last.split("-")[-1])
            except Exception:
                last_seq = 0
        else:
            last_seq = 0

        # In case of any weird formatting or concurrency, probe forward until unique
        seq = last_seq + 1
        while True:
            candidate = f"{base}{str(seq).zfill(4)}"
            cursor.execute("SELECT 1 FROM invoices WHERE invoice_number = ? LIMIT 1", (candidate,))
            if cursor.fetchone() is None:
                return candidate
            seq += 1
    finally:
        cursor.close()
=======
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
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
