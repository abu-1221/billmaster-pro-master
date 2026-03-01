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
        
        return conn
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

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
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff')),
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_invoice ON invoice_items(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)")
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            gst_percentage REAL DEFAULT 0,
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
            stock_quantity INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            barcode TEXT,
            is_active INTEGER DEFAULT 1,
            gst_percentage REAL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            customer_type TEXT DEFAULT 'individual' CHECK(customer_type IN ('individual', 'business', 'institute')),
            status TEXT DEFAULT 'new' CHECK(status IN ('new', 'regular')),
            default_discount REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
            discount_percentage REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'upi', 'bank_transfer', 'credit')),
            payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('paid', 'pending', 'partial', 'cancelled')),
            payment_details TEXT,
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
            tax_rate REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
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

def get_settings(conn):
    """Get all settings as dictionary"""
    cursor = conn.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM settings")
    settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    cursor.close()
    return settings

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
