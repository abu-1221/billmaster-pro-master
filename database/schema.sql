-- BillMaster Pro - Database Schema
-- Run this SQL in phpMyAdmin or MySQL CLI

-- Create database
CREATE DATABASE IF NOT EXISTS billmaster CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE billmaster;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'staff') DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INT,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock_quantity INT DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'pcs',
    barcode VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT,
    user_id INT,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    tax_rate DECIMAL(5,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    payment_method ENUM('cash', 'card', 'upi', 'bank_transfer', 'credit') DEFAULT 'cash',
    payment_status ENUM('paid', 'pending', 'cancelled') DEFAULT 'paid',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Invoice Items table
CREATE TABLE IF NOT EXISTS invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT,
    product_name VARCHAR(200) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- DEFAULT DATA
-- =====================================================

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password, full_name, email, role) VALUES
('admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Administrator', 'admin@billmaster.com', 'admin')
ON DUPLICATE KEY UPDATE username = username;

-- Insert sample categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic items, gadgets, and accessories'),
('Groceries', 'Food items and daily essentials'),
('Stationery', 'Office and school supplies'),
('Clothing', 'Apparel and fashion items'),
('Home & Kitchen', 'Household and kitchen items')
ON DUPLICATE KEY UPDATE name = name;

-- Insert sample products
INSERT INTO products (name, category_id, price, stock_quantity, unit) VALUES
('Notebook A4', 3, 50.00, 100, 'pcs'),
('Pen Pack (10)', 3, 80.00, 200, 'pack'),
('USB Cable Type-C', 1, 199.00, 50, 'pcs'),
('Wireless Earphones', 1, 999.00, 30, 'pcs'),
('Power Bank 10000mAh', 1, 799.00, 25, 'pcs'),
('Rice Basmati 1kg', 2, 150.00, 75, 'kg'),
('Cooking Oil 1L', 2, 180.00, 60, 'ltr'),
('Sugar 1kg', 2, 45.00, 100, 'kg'),
('T-Shirt Cotton', 4, 399.00, 50, 'pcs'),
('Coffee Mug', 5, 199.00, 40, 'pcs')
ON DUPLICATE KEY UPDATE name = name;

-- Insert sample customers
INSERT INTO customers (name, phone, email, address) VALUES
('John Doe', '9876543210', 'john@example.com', '123 Main Street, City'),
('Jane Smith', '9876543211', 'jane@example.com', '456 Park Avenue, Town'),
('Raj Kumar', '9876543212', 'raj@example.com', '789 MG Road, Metro')
ON DUPLICATE KEY UPDATE name = name;

-- Insert default settings
INSERT INTO settings (setting_key, setting_value) VALUES
('business_name', 'BillMaster Pro Store'),
('business_address', '123 Business Street, City - 100001'),
('business_phone', '+91 98765 43210'),
('business_email', 'contact@billmaster.com'),
('currency_symbol', '₹'),
('tax_rate', '0'),
('invoice_prefix', 'INV')
ON DUPLICATE KEY UPDATE setting_key = setting_key;

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_date ON invoices(created_at);
CREATE INDEX idx_invoices_status ON invoices(payment_status);
CREATE INDEX idx_invoice_items_invoice ON invoice_items(invoice_id);
