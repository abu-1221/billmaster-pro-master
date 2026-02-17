<?php
/**
 * BillMaster Pro - Main Entry Point
 * Redirects to the login page or dashboard based on session
 */

// Session configuration
if (session_status() === PHP_SESSION_NONE) {
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

// Check if user is logged in
if (isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true) {
    header('Location: dashboard.html');
} else {
    header('Location: login.html');
}
exit;
?>
