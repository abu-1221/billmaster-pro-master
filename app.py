"""
BillMaster Pro - Main Flask Application
Professional Production Version
"""

from flask import Flask, redirect, session, send_from_directory, jsonify, request
from flask_cors import CORS
import os
from datetime import timedelta, datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import route blueprints
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.invoices import invoices_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.expenses import expenses_bp
from routes.system import system_bp

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'billmaster_pro_secure_production_key_2024_!@#')

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True if os.environ.get('VERCEL') or os.environ.get('RENDER') else False

# Enable CORS
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(categories_bp, url_prefix='/api')
app.register_blueprint(customers_bp, url_prefix='/api')
app.register_blueprint(products_bp, url_prefix='/api')
app.register_blueprint(invoices_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(settings_bp, url_prefix='/api')
app.register_blueprint(expenses_bp, url_prefix='/api')
app.register_blueprint(system_bp, url_prefix='/api')

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api'):
        return jsonify({"success": False, "message": "API endpoint not found", "path": request.path}), 404
    return send_from_directory('static', 'index.html' if os.path.exists('static/index.html') else 'dashboard.html')

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error occurred", "error": str(e)}), 500

@app.route('/')
def index():
    if session.get('logged_in'):
        role = session.get('role', 'staff')
        target = 'dashboard.html' if role == 'admin' else 'billing.html'
    else:
        target = 'login.html'
    return send_from_directory('static', target)

# Catch-all for HTML pages and assets
@app.route('/<path:path>')
def serve_static(path):
    # Security: check if path exists in static folder
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Default to dashboard if logged in, else login
    return index()

@app.route('/api/health')
def health():
    return jsonify({
        "status": "active", 
        "service": "BillMaster Pro Core",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Use environment port if available (for Render/Heroku/Vercel)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
