<?php
/**
 * Settings API Endpoints
 * BillMaster Pro
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
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

function isAdmin() {
    return isLoggedIn() && isset($_SESSION['role']) && $_SESSION['role'] === 'admin';
}

switch ($action) {
    case 'get':
        // Check if settings table exists
        $tableCheck = $conn->query("SHOW TABLES LIKE 'settings'");
        if ($tableCheck && $tableCheck->num_rows === 0) {
            // Create settings table if it doesn't exist
            $conn->query("
                CREATE TABLE IF NOT EXISTS settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    setting_key VARCHAR(100) UNIQUE,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ");
        }
        
        $result = $conn->query("SELECT setting_key, setting_value FROM settings");
        $settings = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $settings[$row['setting_key']] = $row['setting_value'];
            }
        }
        
        echo json_encode(['success' => true, 'data' => $settings]);
        break;
        
    case 'update':
        if (!isLoggedIn()) {
            echo json_encode(['success' => false, 'message' => 'Please login first']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        
        if (!$data || !is_array($data)) {
            echo json_encode(['success' => false, 'message' => 'Invalid data']);
            break;
        }
        
        foreach ($data as $key => $value) {
            $key = $conn->real_escape_string($key);
            $value = $conn->real_escape_string($value);
            $conn->query("
                INSERT INTO settings (setting_key, setting_value) 
                VALUES ('$key', '$value')
                ON DUPLICATE KEY UPDATE setting_value = '$value'
            ");
        }
        
        echo json_encode(['success' => true, 'message' => 'Settings updated']);
        break;
        
    case 'users':
        if (!isAdmin()) {
            echo json_encode(['success' => false, 'message' => 'Admin access required']);
            break;
        }
        
        $result = $conn->query("SELECT id, username, full_name, email, role, created_at FROM users ORDER BY id ASC");
        $users = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $users[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $users]);
        break;
        
    case 'delete_user':
        if (!isAdmin()) {
            echo json_encode(['success' => false, 'message' => 'Admin access required']);
            break;
        }
        
        $id = intval($_GET['id'] ?? 0);
        
        if ($id <= 1) {
            echo json_encode(['success' => false, 'message' => 'Cannot delete primary admin']);
            break;
        }
        
        if ($conn->query("DELETE FROM users WHERE id = $id")) {
            echo json_encode(['success' => true, 'message' => 'User deleted']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to delete user']);
        }
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
