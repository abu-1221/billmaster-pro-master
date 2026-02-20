<?php
/**
 * Analytics API Endpoints
 * BillMaster Pro - Active Analytics Tracking
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
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

switch ($action) {
    case 'dashboard':
        // Today's stats from actual invoices
        $todayResult = $conn->query("
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_revenue
            FROM invoices 
            WHERE DATE(created_at) = CURDATE()
        ");
        $today = $todayResult ? $todayResult->fetch_assoc() : ['invoices' => 0, 'revenue' => 0, 'paid_revenue' => 0, 'pending_revenue' => 0];
        
        // Yesterday's stats for comparison
        $yesterdayResult = $conn->query("
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE DATE(created_at) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
        ");
        $yesterday = $yesterdayResult ? $yesterdayResult->fetch_assoc() : ['invoices' => 0, 'revenue' => 0];
        
        // This month's stats
        $monthResult = $conn->query("
            SELECT 
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())
        ");
        $month = $monthResult ? $monthResult->fetch_assoc() : ['invoices' => 0, 'revenue' => 0];
        
        // Products count
        $prodResult = $conn->query("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1");
        $products = $prodResult ? $prodResult->fetch_assoc()['cnt'] : 0;
        
        // Customers count
        $custResult = $conn->query("SELECT COUNT(*) as cnt FROM customers");
        $customers = $custResult ? $custResult->fetch_assoc()['cnt'] : 0;
        
        // Total items sold today
        $itemsResult = $conn->query("
            SELECT COALESCE(SUM(ii.quantity), 0) as items_sold
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE DATE(i.created_at) = CURDATE()
        ");
        $itemsSold = $itemsResult ? $itemsResult->fetch_assoc()['items_sold'] : 0;
        
        // Calculate growth percentage
        $revenueGrowth = 0;
        if (floatval($yesterday['revenue']) > 0) {
            $revenueGrowth = round(((floatval($today['revenue']) - floatval($yesterday['revenue'])) / floatval($yesterday['revenue'])) * 100, 1);
        }
        
        echo json_encode([
            'success' => true,
            'data' => [
                'today' => [
                    'invoices' => intval($today['invoices']),
                    'revenue' => floatval($today['revenue']),
                    'paid_revenue' => floatval($today['paid_revenue']),
                    'pending_revenue' => floatval($today['pending_revenue']),
                    'items_sold' => intval($itemsSold)
                ],
                'yesterday' => [
                    'invoices' => intval($yesterday['invoices']),
                    'revenue' => floatval($yesterday['revenue'])
                ],
                'month' => [
                    'invoices' => intval($month['invoices']),
                    'revenue' => floatval($month['revenue'])
                ],
                'revenue_growth' => $revenueGrowth,
                'products' => intval($products),
                'customers' => intval($customers)
            ]
        ]);
        break;
        
    case 'sales_chart':
        $days = intval($_GET['days'] ?? 7);
        $data = [];
        
        for ($i = $days - 1; $i >= 0; $i--) {
            $date = date('Y-m-d', strtotime("-$i days"));
            $result = $conn->query("
                SELECT 
                    COALESCE(SUM(total_amount), 0) as total,
                    COUNT(*) as count,
                    COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid
                FROM invoices 
                WHERE DATE(created_at) = '$date'
            ");
            $row = $result ? $result->fetch_assoc() : ['total' => 0, 'count' => 0, 'paid' => 0];
            $data[] = [
                'date' => $date,
                'total' => floatval($row['total']),
                'count' => intval($row['count']),
                'paid' => floatval($row['paid'])
            ];
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'payment_methods':
        $result = $conn->query("
            SELECT 
                payment_method, 
                SUM(total_amount) as total, 
                COUNT(*) as count,
                ROUND(SUM(total_amount) * 100 / (SELECT SUM(total_amount) FROM invoices WHERE total_amount > 0), 1) as percentage
            FROM invoices
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY payment_method
            ORDER BY total DESC
        ");
        
        $data = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $row['total'] = floatval($row['total']);
                $row['count'] = intval($row['count']);
                $row['percentage'] = floatval($row['percentage'] ?? 0);
                $data[] = $row;
            }
        }
        
        // If no data, provide defaults
        if (empty($data)) {
            $data = [
                ['payment_method' => 'cash', 'total' => 0, 'count' => 0, 'percentage' => 0]
            ];
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'top_products':
        $limit = intval($_GET['limit'] ?? 5);
        $days = intval($_GET['days'] ?? 30);
        
        $result = $conn->query("
            SELECT 
                p.id,
                p.name, 
                p.price as unit_price,
                SUM(ii.quantity) as sold, 
                SUM(ii.total_price) as revenue,
                ROUND(AVG(ii.unit_price), 2) as avg_price
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.created_at >= DATE_SUB(NOW(), INTERVAL $days DAY)
            GROUP BY p.id, p.name, p.price
            ORDER BY revenue DESC
            LIMIT $limit
        ");
        
        $data = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $row['sold'] = intval($row['sold']);
                $row['revenue'] = floatval($row['revenue']);
                $row['unit_price'] = floatval($row['unit_price']);
                $row['avg_price'] = floatval($row['avg_price']);
                $data[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'low_stock':
        $threshold = intval($_GET['threshold'] ?? 10);
        
        $result = $conn->query("
            SELECT id, name, stock_quantity, unit, price
            FROM products
            WHERE is_active = 1 AND stock_quantity <= $threshold
            ORDER BY stock_quantity ASC
            LIMIT 10
        ");
        
        $data = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $row['stock_quantity'] = intval($row['stock_quantity']);
                $row['price'] = floatval($row['price']);
                $data[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'hourly_sales':
        // Sales by hour for today
        $result = $conn->query("
            SELECT 
                HOUR(created_at) as hour,
                COUNT(*) as invoices,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM invoices 
            WHERE DATE(created_at) = CURDATE()
            GROUP BY HOUR(created_at)
            ORDER BY hour ASC
        ");
        
        // Initialize all hours with 0
        $hourlyData = [];
        for ($i = 0; $i < 24; $i++) {
            $hourlyData[$i] = ['hour' => $i, 'invoices' => 0, 'revenue' => 0];
        }
        
        // Fill in actual data
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $hour = intval($row['hour']);
                $hourlyData[$hour] = [
                    'hour' => $hour,
                    'invoices' => intval($row['invoices']),
                    'revenue' => floatval($row['revenue'])
                ];
            }
        }
        
        echo json_encode(['success' => true, 'data' => array_values($hourlyData)]);
        break;
        
    case 'recent_invoices':
        $limit = intval($_GET['limit'] ?? 10);
        
        $result = $conn->query("
            SELECT 
                i.id,
                i.invoice_number,
                i.total_amount,
                i.payment_method,
                i.payment_status,
                i.created_at,
                c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.created_at DESC
            LIMIT $limit
        ");
        
        $data = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $row['total_amount'] = floatval($row['total_amount']);
                $data[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'monthly':
        $months = intval($_GET['months'] ?? 6);
        $data = [];
        
        for ($i = $months - 1; $i >= 0; $i--) {
            $month = date('Y-m', strtotime("-$i months"));
            $result = $conn->query("
                SELECT 
                    COUNT(*) as invoices,
                    COALESCE(SUM(total_amount), 0) as revenue,
                    COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid
                FROM invoices 
                WHERE DATE_FORMAT(created_at, '%Y-%m') = '$month'
            ");
            $row = $result ? $result->fetch_assoc() : ['invoices' => 0, 'revenue' => 0, 'paid' => 0];
            $data[] = [
                'month' => $month,
                'month_name' => date('M Y', strtotime($month . '-01')),
                'invoices' => intval($row['invoices']),
                'revenue' => floatval($row['revenue']),
                'paid' => floatval($row['paid'])
            ];
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'customer_stats':
        // Top customers by spending
        $limit = intval($_GET['limit'] ?? 5);
        
        $result = $conn->query("
            SELECT 
                c.id,
                c.name,
                c.phone,
                COUNT(i.id) as total_orders,
                COALESCE(SUM(i.total_amount), 0) as total_spent,
                MAX(i.created_at) as last_order
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            GROUP BY c.id, c.name, c.phone
            HAVING total_orders > 0
            ORDER BY total_spent DESC
            LIMIT $limit
        ");
        
        $data = [];
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $row['total_orders'] = intval($row['total_orders']);
                $row['total_spent'] = floatval($row['total_spent']);
                $data[] = $row;
            }
        }
        
        echo json_encode(['success' => true, 'data' => $data]);
        break;
        
    case 'summary':
        // Complete summary for reports
        $period = $_GET['period'] ?? 'today';
        
        switch ($period) {
            case 'today':
                $dateFilter = "DATE(created_at) = CURDATE()";
                break;
            case 'week':
                $dateFilter = "created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)";
                break;
            case 'month':
                $dateFilter = "MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())";
                break;
            case 'year':
                $dateFilter = "YEAR(created_at) = YEAR(CURDATE())";
                break;
            default:
                $dateFilter = "1=1";
        }
        
        $result = $conn->query("
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_amount,
                COALESCE(SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_amount,
                COALESCE(AVG(total_amount), 0) as avg_order_value,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM invoices 
            WHERE $dateFilter
        ");
        
        $summary = $result ? $result->fetch_assoc() : [];
        
        // Items sold
        $itemsResult = $conn->query("
            SELECT COALESCE(SUM(ii.quantity), 0) as items_sold
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE $dateFilter
        ");
        $itemsSold = $itemsResult ? $itemsResult->fetch_assoc()['items_sold'] : 0;
        
        echo json_encode([
            'success' => true,
            'data' => [
                'period' => $period,
                'total_invoices' => intval($summary['total_invoices'] ?? 0),
                'total_revenue' => floatval($summary['total_revenue'] ?? 0),
                'paid_amount' => floatval($summary['paid_amount'] ?? 0),
                'pending_amount' => floatval($summary['pending_amount'] ?? 0),
                'avg_order_value' => floatval($summary['avg_order_value'] ?? 0),
                'unique_customers' => intval($summary['unique_customers'] ?? 0),
                'items_sold' => intval($itemsSold)
            ]
        ]);
        break;
        
    default:
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

$conn->close();
?>
