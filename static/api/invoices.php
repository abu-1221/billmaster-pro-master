<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') exit(0);

// Start session before including auth
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

require_once __DIR__ . '/../config/database.php';

$conn = getConnection();
$action = $_GET['action'] ?? '';

// Simple auth check function
function checkAuth() {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}

function getCurrentUserId() {
    return $_SESSION['user_id'] ?? 1;
}

switch ($action) {
    case 'list':
        $status = isset($_GET['status']) ? $conn->real_escape_string($_GET['status']) : '';
        $where = $status ? "WHERE i.payment_status = '$status'" : "";
        
        $sql = "SELECT i.*, c.name as customer_name FROM invoices i 
                LEFT JOIN customers c ON i.customer_id = c.id $where
                ORDER BY i.created_at DESC LIMIT 100";
        $result = $conn->query($sql);
        $invoices = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) $invoices[] = $row;
        }
        echo json_encode(['success' => true, 'data' => $invoices]);
        break;
        
    case 'get':
        $id = intval($_GET['id'] ?? 0);
        $sql = "SELECT i.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address
                FROM invoices i LEFT JOIN customers c ON i.customer_id = c.id WHERE i.id = $id";
        $result = $conn->query($sql);
        if ($result && $result->num_rows === 1) {
            $invoice = $result->fetch_assoc();
            $itemsResult = $conn->query("SELECT ii.*, p.name as product_name FROM invoice_items ii 
                                         LEFT JOIN products p ON ii.product_id = p.id 
                                         WHERE ii.invoice_id = $id");
            $items = [];
            if ($itemsResult) {
                while ($row = $itemsResult->fetch_assoc()) $items[] = $row;
            }
            $invoice['items'] = $items;
            echo json_encode(['success' => true, 'data' => $invoice]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Invoice not found']);
        }
        break;
        
    case 'create':
        if (!checkAuth()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        
        if (!$data) {
            echo json_encode(['success' => false, 'message' => 'Invalid data']);
            break;
        }
        
        $customerId = !empty($data['customer_id']) ? intval($data['customer_id']) : 'NULL';
        $items = $data['items'] ?? [];
        $taxRate = floatval($data['tax_rate'] ?? 0);
        $discountAmount = floatval($data['discount_amount'] ?? 0);
        $paymentMethod = $conn->real_escape_string($data['payment_method'] ?? 'cash');
        $paymentStatus = $conn->real_escape_string($data['payment_status'] ?? 'paid');
        
        if (empty($items)) { 
            echo json_encode(['success' => false, 'message' => 'No items in cart']); 
            break; 
        }
        
        // Calculate totals
        $subtotal = 0;
        foreach ($items as $item) {
            $subtotal += floatval($item['quantity']) * floatval($item['unit_price']);
        }
        $taxAmount = $subtotal * ($taxRate / 100);
        $totalAmount = $subtotal + $taxAmount - $discountAmount;
        
        // Generate invoice number
        $prefix = 'INV';
        $dateStr = date('Ymd');
        $countResult = $conn->query("SELECT COUNT(*) as cnt FROM invoices WHERE DATE(created_at) = CURDATE()");
        $count = 1;
        if ($countResult) {
            $row = $countResult->fetch_assoc();
            $count = intval($row['cnt']) + 1;
        }
        $invoiceNumber = $prefix . $dateStr . str_pad($count, 4, '0', STR_PAD_LEFT);
        
        $userId = getCurrentUserId();
        
        // Insert invoice
        $conn->begin_transaction();
        try {
            $sql = "INSERT INTO invoices (invoice_number, customer_id, user_id, subtotal, tax_rate, tax_amount, 
                    discount_amount, total_amount, payment_method, payment_status) 
                    VALUES ('$invoiceNumber', $customerId, $userId, $subtotal, $taxRate, $taxAmount, 
                    $discountAmount, $totalAmount, '$paymentMethod', '$paymentStatus')";
            
            if (!$conn->query($sql)) {
                throw new Exception('Failed to create invoice: ' . $conn->error);
            }
            
            $invoiceId = $conn->insert_id;
            
            // Insert items and update stock
            foreach ($items as $item) {
                $productId = intval($item['product_id']);
                $quantity = intval($item['quantity']);
                $unitPrice = floatval($item['unit_price']);
                $totalPrice = $quantity * $unitPrice;
                
                // Get product name
                $prodResult = $conn->query("SELECT name FROM products WHERE id = $productId");
                $productName = 'Unknown';
                if ($prodResult && $prodResult->num_rows > 0) {
                    $prod = $prodResult->fetch_assoc();
                    $productName = $conn->real_escape_string($prod['name']);
                }
                
                $itemSql = "INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, total_price)
                            VALUES ($invoiceId, $productId, '$productName', $quantity, $unitPrice, $totalPrice)";
                
                if (!$conn->query($itemSql)) {
                    throw new Exception('Failed to add item: ' . $conn->error);
                }
                
                // Update stock
                $conn->query("UPDATE products SET stock_quantity = GREATEST(0, stock_quantity - $quantity) WHERE id = $productId");
            }
            
            $conn->commit();
            echo json_encode(['success' => true, 'invoice_id' => $invoiceId, 'invoice_number' => $invoiceNumber]);
            
        } catch (Exception $e) {
            $conn->rollback();
            echo json_encode(['success' => false, 'message' => $e->getMessage()]);
        }
        break;
        
    case 'update_status':
        if (!checkAuth()) {
            echo json_encode(['success' => false, 'message' => 'Unauthorized']);
            break;
        }
        $data = json_decode(file_get_contents('php://input'), true);
        $id = intval($data['id'] ?? 0);
        $status = $conn->real_escape_string($data['status'] ?? '');
        $conn->query("UPDATE invoices SET payment_status = '$status' WHERE id = $id");
        echo json_encode(['success' => true]);
        break;
        
    case 'today_summary':
        $sql = "SELECT COUNT(*) as total_invoices,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_amount,
                COALESCE(SUM(total_amount), 0) as total_amount
                FROM invoices WHERE DATE(created_at) = CURDATE()";
        $result = $conn->query($sql);
        $data = $result ? $result->fetch_assoc() : ['total_invoices' => 0, 'paid_amount' => 0, 'total_amount' => 0];
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
