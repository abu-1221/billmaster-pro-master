<?php
/**
 * Products API Endpoints
 * BillMaster Pro
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// Start session
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

require_once __DIR__ . '/../config/database.php';

$conn = getConnection();
$action = $_GET['action'] ?? $_POST['action'] ?? '';

// Simple auth check
function isLoggedIn() {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}

switch ($action) {
    case 'list':
        $categoryId = $_GET['category_id'] ?? null;
        $search = $_GET['search'] ?? '';
        $activeOnly = isset($_GET['active_only']) && $_GET['active_only'] === 'false' ? false : true;
        
        $sql = "SELECT p.*, c.name as category_name FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1";
        
        if ($activeOnly) {
            $sql .= " AND p.is_active = 1";
        }
        if ($categoryId) {
            $sql .= " AND p.category_id = " . intval($categoryId);
        }
        if ($search) {
            $search = $conn->real_escape_string($search);
            $sql .= " AND (p.name LIKE '%$search%' OR p.barcode LIKE '%$search%')";
        }
        
        $sql .= " ORDER BY p.name ASC";
        $result = $conn->query($sql);
        
        $products = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $products[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $products]);
        break;
        
    case 'get':
        $id = intval($_GET['id'] ?? 0);
        $sql = "SELECT p.*, c.name as category_name FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE p.id = $id";
        $result = $conn->query($sql);
        
        if ($result && $result->num_rows === 1) {
            echo json_encode(['success' => true, 'data' => $result->fetch_assoc()]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Product not found']);
        }
        break;
        
    case 'create':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        
        $name = $conn->real_escape_string($data['name'] ?? '');
        $description = $conn->real_escape_string($data['description'] ?? '');
        $categoryId = !empty($data['category_id']) ? intval($data['category_id']) : 'NULL';
        $price = floatval($data['price'] ?? 0);
        $stockQuantity = intval($data['stock_quantity'] ?? 0);
        $unit = $conn->real_escape_string($data['unit'] ?? 'pcs');
        $barcode = $conn->real_escape_string($data['barcode'] ?? '');
        $isActive = isset($data['is_active']) ? ($data['is_active'] ? 1 : 0) : 1;
        
        if (empty($name) || $price <= 0) {
            echo json_encode(['success' => false, 'message' => 'Name and valid price are required']);
            break;
        }
        
        $categoryValue = $categoryId === 'NULL' ? 'NULL' : $categoryId;
        $sql = "INSERT INTO products (name, description, category_id, price, stock_quantity, unit, barcode, is_active) 
                VALUES ('$name', '$description', $categoryValue, $price, $stockQuantity, '$unit', '$barcode', $isActive)";
        
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Product created successfully', 'id' => $conn->insert_id]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to create product: ' . $conn->error]);
        }
        break;
        
    case 'update':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        $id = intval($data['id'] ?? 0);
        
        if ($id <= 0) {
            echo json_encode(['success' => false, 'message' => 'Invalid product ID']);
            break;
        }
        
        $updates = [];
        if (isset($data['name'])) $updates[] = "name = '" . $conn->real_escape_string($data['name']) . "'";
        if (isset($data['description'])) $updates[] = "description = '" . $conn->real_escape_string($data['description']) . "'";
        if (isset($data['category_id'])) {
            $catId = empty($data['category_id']) ? 'NULL' : intval($data['category_id']);
            $updates[] = "category_id = $catId";
        }
        if (isset($data['price'])) $updates[] = "price = " . floatval($data['price']);
        if (isset($data['stock_quantity'])) $updates[] = "stock_quantity = " . intval($data['stock_quantity']);
        if (isset($data['unit'])) $updates[] = "unit = '" . $conn->real_escape_string($data['unit']) . "'";
        if (isset($data['barcode'])) $updates[] = "barcode = '" . $conn->real_escape_string($data['barcode']) . "'";
        if (isset($data['is_active'])) $updates[] = "is_active = " . ($data['is_active'] ? 1 : 0);
        
        if (empty($updates)) {
            echo json_encode(['success' => false, 'message' => 'No fields to update']);
            break;
        }
        
        $sql = "UPDATE products SET " . implode(', ', $updates) . " WHERE id = $id";
        
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Product updated successfully']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to update product']);
        }
        break;
        
    case 'delete':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $id = intval($_GET['id'] ?? 0);
        
        if ($id <= 0) {
            echo json_encode(['success' => false, 'message' => 'Invalid product ID']);
            break;
        }
        
        // Soft delete - just mark as inactive
        $sql = "UPDATE products SET is_active = 0 WHERE id = $id";
        
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Product deleted successfully']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to delete product']);
        }
        break;
        
    case 'update_stock':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        $id = intval($data['id'] ?? 0);
        $quantity = intval($data['quantity'] ?? 0);
        $operation = $data['operation'] ?? 'set';
        
        if ($id <= 0) {
            echo json_encode(['success' => false, 'message' => 'Invalid product ID']);
            break;
        }
        
        switch ($operation) {
            case 'add':
                $sql = "UPDATE products SET stock_quantity = stock_quantity + $quantity WHERE id = $id";
                break;
            case 'subtract':
                $sql = "UPDATE products SET stock_quantity = GREATEST(0, stock_quantity - $quantity) WHERE id = $id";
                break;
            default:
                $sql = "UPDATE products SET stock_quantity = $quantity WHERE id = $id";
        }
        
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Stock updated successfully']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to update stock']);
        }
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
