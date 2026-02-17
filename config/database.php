<?php
/**
 * Database Configuration
 * BillMaster Pro - Billing & Institute Management System
 */

define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'billmaster_db');

// Create database connection
function getConnection() {
    $conn = new mysqli(DB_HOST, DB_USER, DB_PASS);
    
    if ($conn->connect_error) {
        die(json_encode(['success' => false, 'message' => 'Connection failed: ' . $conn->connect_error]));
    }
    
    // Create database if not exists
    $sql = "CREATE DATABASE IF NOT EXISTS " . DB_NAME;
    $conn->query($sql);
    $conn->select_db(DB_NAME);
    
    // Create tables if not exist
    createTables($conn);
    
    return $conn;
}

function createTables($conn) {
    // Users table
    $conn->query("CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        role ENUM('admin', 'staff') DEFAULT 'staff',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )");
    
    // Categories table
    $conn->query("CREATE TABLE IF NOT EXISTS categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )");
    
    // Products table
    $conn->query("CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        category_id INT,
        price DECIMAL(10, 2) NOT NULL,
        stock_quantity INT DEFAULT 0,
        unit VARCHAR(30) DEFAULT 'pcs',
        barcode VARCHAR(50),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    )");
    
    // Customers table
    $conn->query("CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        phone VARCHAR(20),
        address TEXT,
        city VARCHAR(50),
        customer_type ENUM('individual', 'business', 'institute') DEFAULT 'individual',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )");
    
    // Invoices table
    $conn->query("CREATE TABLE IF NOT EXISTS invoices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_number VARCHAR(30) UNIQUE NOT NULL,
        customer_id INT,
        user_id INT,
        subtotal DECIMAL(12, 2) NOT NULL,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        tax_amount DECIMAL(12, 2) DEFAULT 0,
        discount_amount DECIMAL(12, 2) DEFAULT 0,
        total_amount DECIMAL(12, 2) NOT NULL,
        payment_method ENUM('cash', 'card', 'upi', 'bank_transfer', 'credit') DEFAULT 'cash',
        payment_status ENUM('paid', 'pending', 'partial', 'cancelled') DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )");
    
    // Invoice items table
    $conn->query("CREATE TABLE IF NOT EXISTS invoice_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_id INT NOT NULL,
        product_id INT,
        product_name VARCHAR(150) NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        total_price DECIMAL(12, 2) NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
    )");
    
    // Settings table
    $conn->query("CREATE TABLE IF NOT EXISTS settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        setting_key VARCHAR(50) UNIQUE NOT NULL,
        setting_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )");
    
    // Insert default admin user if not exists
    $result = $conn->query("SELECT id FROM users WHERE username = 'admin'");
    if ($result->num_rows == 0) {
        $hashedPassword = password_hash('admin123', PASSWORD_DEFAULT);
        $conn->query("INSERT INTO users (username, password, full_name, email, role) 
                      VALUES ('admin', '$hashedPassword', 'Administrator', 'admin@billmaster.com', 'admin')");
    }
    
    // Insert default settings if not exists
    $defaultSettings = [
        ['business_name', 'BillMaster Pro'],
        ['business_address', '123 Business Street, City'],
        ['business_phone', '+91 9876543210'],
        ['business_email', 'contact@billmaster.com'],
        ['tax_rate', '18'],
        ['currency_symbol', '₹'],
        ['invoice_prefix', 'INV']
    ];
    
    foreach ($defaultSettings as $setting) {
        $key = $setting[0];
        $value = $setting[1];
        $result = $conn->query("SELECT id FROM settings WHERE setting_key = '$key'");
        if ($result->num_rows == 0) {
            $conn->query("INSERT INTO settings (setting_key, setting_value) VALUES ('$key', '$value')");
        }
    }
    
    // Insert sample categories if empty
    $result = $conn->query("SELECT id FROM categories LIMIT 1");
    if ($result->num_rows == 0) {
        $sampleCategories = [
            ['Beverages', 'Tea, Coffee, Soft Drinks, Juices'],
            ['Snacks', 'Chips, Biscuits, Namkeen'],
            ['Meals', 'Breakfast, Lunch, Dinner items'],
            ['Stationery', 'Pens, Notebooks, Files'],
            ['Services', 'Printing, Xerox, Lamination']
        ];
        foreach ($sampleCategories as $cat) {
            $conn->query("INSERT INTO categories (name, description) VALUES ('{$cat[0]}', '{$cat[1]}')");
        }
    }
}

// Get all settings as associative array
function getSettings($conn) {
    $settings = [];
    $result = $conn->query("SELECT setting_key, setting_value FROM settings");
    while ($row = $result->fetch_assoc()) {
        $settings[$row['setting_key']] = $row['setting_value'];
    }
    return $settings;
}

// Generate invoice number
function generateInvoiceNumber($conn) {
    $settings = getSettings($conn);
    $prefix = $settings['invoice_prefix'] ?? 'INV';
    $date = date('Ymd');
    
    $result = $conn->query("SELECT COUNT(*) as count FROM invoices WHERE DATE(created_at) = CURDATE()");
    $row = $result->fetch_assoc();
    $count = $row['count'] + 1;
    
    return $prefix . '-' . $date . '-' . str_pad($count, 4, '0', STR_PAD_LEFT);
}
?>
