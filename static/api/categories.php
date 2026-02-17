<?php
/**
 * Categories API Endpoints
 * BillMaster Pro
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

require_once __DIR__ . '/../config/database.php';

$conn = getConnection();
$action = $_GET['action'] ?? '';

function isLoggedIn() {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}

switch ($action) {
    case 'list':
        $sql = "SELECT c.*, COUNT(p.id) as product_count FROM categories c 
                LEFT JOIN products p ON c.id = p.category_id AND p.is_active = 1
                GROUP BY c.id ORDER BY c.name ASC";
        $result = $conn->query($sql);
        $categories = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $categories[] = $row;
            }
        }
        echo json_encode(['success' => true, 'data' => $categories]);
        break;
        
    case 'get':
        $id = intval($_GET['id'] ?? 0);
        $result = $conn->query("SELECT * FROM categories WHERE id = $id");
        if ($result && $result->num_rows === 1) {
            echo json_encode(['success' => true, 'data' => $result->fetch_assoc()]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Category not found']);
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
        
        if (empty($name)) {
            echo json_encode(['success' => false, 'message' => 'Category name is required']);
            break;
        }
        
        $sql = "INSERT INTO categories (name, description) VALUES ('$name', '$description')";
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Category created', 'id' => $conn->insert_id]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to create category']);
        }
        break;
        
    case 'update':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        $id = intval($data['id'] ?? 0);
        $name = $conn->real_escape_string($data['name'] ?? '');
        $description = $conn->real_escape_string($data['description'] ?? '');
        
        if ($id <= 0 || empty($name)) {
            echo json_encode(['success' => false, 'message' => 'Valid ID and name required']);
            break;
        }
        
        $sql = "UPDATE categories SET name = '$name', description = '$description' WHERE id = $id";
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Category updated']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to update category']);
        }
        break;
        
    case 'delete':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $id = intval($_GET['id'] ?? 0);
        
        // Check if category has products
        $check = $conn->query("SELECT COUNT(*) as cnt FROM products WHERE category_id = $id AND is_active = 1");
        $row = $check->fetch_assoc();
        if ($row['cnt'] > 0) {
            echo json_encode(['success' => false, 'message' => 'Cannot delete: category has active products']);
            break;
        }
        
        if ($conn->query("DELETE FROM categories WHERE id = $id")) {
            echo json_encode(['success' => true, 'message' => 'Category deleted']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to delete category']);
        }
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
