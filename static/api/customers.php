<?php
/**
 * Customers API Endpoints
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
        $search = isset($_GET['search']) ? $conn->real_escape_string($_GET['search']) : '';
        
        $sql = "SELECT c.*, 
                COUNT(DISTINCT i.id) as total_orders,
                COALESCE(SUM(i.total_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                WHERE 1=1";
        
        if ($search) {
            $sql .= " AND (c.name LIKE '%$search%' OR c.phone LIKE '%$search%' OR c.email LIKE '%$search%')";
        }
        
        $sql .= " GROUP BY c.id ORDER BY c.name ASC";
        $result = $conn->query($sql);
        
        $customers = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $customers[] = $row;
            }
        }
        echo json_encode(['success' => true, 'data' => $customers]);
        break;
        
    case 'get':
        $id = intval($_GET['id'] ?? 0);
        $result = $conn->query("SELECT * FROM customers WHERE id = $id");
        if ($result && $result->num_rows === 1) {
            $customer = $result->fetch_assoc();
            
            // Get recent invoices
            $invoices = [];
            $invResult = $conn->query("SELECT * FROM invoices WHERE customer_id = $id ORDER BY created_at DESC LIMIT 10");
            if ($invResult) {
                while ($row = $invResult->fetch_assoc()) {
                    $invoices[] = $row;
                }
            }
            $customer['invoices'] = $invoices;
            
            echo json_encode(['success' => true, 'data' => $customer]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Customer not found']);
        }
        break;
        
    case 'create':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        $name = $conn->real_escape_string($data['name'] ?? '');
        $phone = $conn->real_escape_string($data['phone'] ?? '');
        $email = $conn->real_escape_string($data['email'] ?? '');
        $address = $conn->real_escape_string($data['address'] ?? '');
        
        if (empty($name)) {
            echo json_encode(['success' => false, 'message' => 'Customer name is required']);
            break;
        }
        
        $sql = "INSERT INTO customers (name, phone, email, address) VALUES ('$name', '$phone', '$email', '$address')";
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Customer created', 'id' => $conn->insert_id]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to create customer']);
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
            echo json_encode(['success' => false, 'message' => 'Invalid customer ID']);
            break;
        }
        
        $updates = [];
        if (isset($data['name'])) $updates[] = "name = '" . $conn->real_escape_string($data['name']) . "'";
        if (isset($data['phone'])) $updates[] = "phone = '" . $conn->real_escape_string($data['phone']) . "'";
        if (isset($data['email'])) $updates[] = "email = '" . $conn->real_escape_string($data['email']) . "'";
        if (isset($data['address'])) $updates[] = "address = '" . $conn->real_escape_string($data['address']) . "'";
        
        if (empty($updates)) {
            echo json_encode(['success' => false, 'message' => 'No fields to update']);
            break;
        }
        
        $sql = "UPDATE customers SET " . implode(', ', $updates) . " WHERE id = $id";
        if ($conn->query($sql)) {
            echo json_encode(['success' => true, 'message' => 'Customer updated']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to update customer']);
        }
        break;
        
    case 'delete':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $id = intval($_GET['id'] ?? 0);
        
        if ($conn->query("DELETE FROM customers WHERE id = $id")) {
            echo json_encode(['success' => true, 'message' => 'Customer deleted']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to delete customer']);
        }
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
