<?php
// Start output buffering to prevent header issues
ob_start();

// Session configuration - must be set before session_start()
if (session_status() === PHP_SESSION_NONE) {
    // Set session cookie parameters for better security
    session_set_cookie_params([
        'lifetime' => 86400, // 24 hours
        'path' => '/',
        'domain' => '',
        'secure' => false, // Set to true in production with HTTPS
        'httponly' => true,
        'samesite' => 'Lax'
    ]);
    session_start();
}

// Get the origin for CORS
$origin = isset($_SERVER['HTTP_ORIGIN']) ? $_SERVER['HTTP_ORIGIN'] : '';

// Set proper CORS headers
header('Content-Type: application/json');
if ($origin) {
    header('Access-Control-Allow-Origin: ' . $origin);
} else {
    header('Access-Control-Allow-Origin: *');
}
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept, X-Requested-With');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit(0);
}

require_once __DIR__ . '/../config/database.php';

$action = $_GET['action'] ?? '';

switch ($action) {
    case 'login':
        $data = json_decode(file_get_contents('php://input'), true);
        $username = $data['username'] ?? '';
        $password = $data['password'] ?? '';
        
        if (empty($username) || empty($password)) {
            echo json_encode(['success' => false, 'message' => 'Username and password required']);
            break;
        }
        
        $conn = getConnection();
        $stmt = $conn->prepare("SELECT id, username, password, full_name, role FROM users WHERE username = ?");
        $stmt->bind_param("s", $username);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 1) {
            $user = $result->fetch_assoc();
            if (password_verify($password, $user['password'])) {
                $_SESSION['user_id'] = $user['id'];
                $_SESSION['username'] = $user['username'];
                $_SESSION['full_name'] = $user['full_name'];
                $_SESSION['role'] = $user['role'];
                $_SESSION['logged_in'] = true;
                
                echo json_encode(['success' => true, 'message' => 'Login successful', 'user' => [
                    'id' => $user['id'],
                    'username' => $user['username'],
                    'full_name' => $user['full_name'],
                    'role' => $user['role']
                ]]);
            } else {
                echo json_encode(['success' => false, 'message' => 'Invalid password']);
            }
        } else {
            echo json_encode(['success' => false, 'message' => 'User not found']);
        }
        $conn->close();
        break;
        
    case 'logout':
        session_unset();
        session_destroy();
        echo json_encode(['success' => true, 'message' => 'Logged out']);
        break;
        
    case 'check':
        if (isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true) {
            echo json_encode(['success' => true, 'user' => [
                'id' => $_SESSION['user_id'],
                'username' => $_SESSION['username'],
                'full_name' => $_SESSION['full_name'],
                'role' => $_SESSION['role']
            ]]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Not logged in']);
        }
        break;
        
    case 'register':
        if (!isset($_SESSION['logged_in']) || $_SESSION['role'] !== 'admin') {
            echo json_encode(['success' => false, 'message' => 'Admin access required']);
            break;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        $username = trim($data['username'] ?? '');
        $password = $data['password'] ?? '';
        $fullName = trim($data['full_name'] ?? '');
        $email = trim($data['email'] ?? '');
        $role = $data['role'] ?? 'staff';
        
        if (empty($username) || empty($password) || empty($fullName)) {
            echo json_encode(['success' => false, 'message' => 'Required fields missing']);
            break;
        }
        
        $conn = getConnection();
        
        // Check if username exists
        $check = $conn->prepare("SELECT id FROM users WHERE username = ?");
        $check->bind_param("s", $username);
        $check->execute();
        if ($check->get_result()->num_rows > 0) {
            echo json_encode(['success' => false, 'message' => 'Username already exists']);
            $conn->close();
            break;
        }
        
        $hashedPassword = password_hash($password, PASSWORD_DEFAULT);
        $stmt = $conn->prepare("INSERT INTO users (username, password, full_name, email, role) VALUES (?, ?, ?, ?, ?)");
        $stmt->bind_param("sssss", $username, $hashedPassword, $fullName, $email, $role);
        
        if ($stmt->execute()) {
            echo json_encode(['success' => true, 'message' => 'User created']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to create user']);
        }
        $conn->close();
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}
?>
