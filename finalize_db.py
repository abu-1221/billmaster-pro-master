import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'billmaster.db')

def finalize_database():
    print(f"Checking database at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("Database doesn't exist yet. It will be created perfectly on first run.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Add missing columns to invoices
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN payment_details TEXT")
        print("Added 'payment_details' column to 'invoices'.")
    except sqlite3.OperationalError:
        pass

    # 2. Add last_login to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        print("Added 'last_login' column to 'users'.")
    except sqlite3.OperationalError:
        pass

    # 3. Add customer fields
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN status TEXT DEFAULT 'new'")
        print("Added 'status' column to 'customers'.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN default_discount REAL DEFAULT 0")
        print("Added 'default_discount' column to 'customers'.")
    except sqlite3.OperationalError:
        pass

    # 4. Add settings
    cursor.execute("SELECT id FROM settings WHERE setting_key = 'upi_id'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)", ('upi_id', ''))
        print("Added 'upi_id' to settings.")

    # 5. Create Indexes for speed
    print("Creating precision indexes for performance...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_invoice ON invoice_items(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)")

    conn.commit()
    conn.close()
    print("✓ Perfect Database Finalization Complete!")

if __name__ == "__main__":
    finalize_database()
