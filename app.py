"""
BillMaster Pro - Main Flask Application
Professional Production Version
"""

from flask import Flask, redirect, session, send_from_directory, jsonify
from flask_cors import CORS
import os
from datetime import timedelta

# Import route blueprints
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.invoices import invoices_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp

# Initialize Flask app
# We explicitly set static_folder to 'static'
app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'billmaster_pro_prod_key_9988')

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

@app.route('/')
def index():
    if session.get('logged_in'):
        return send_from_directory('static', 'dashboard.html')
    return send_from_directory('static', 'login.html')

# Catch-all for HTML pages
@app.route('/<path:path>')
def serve_pages(path):
    if path.endswith('.html'):
        return send_from_directory('static', path)
    return send_from_directory('static', path)

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "service": "billmaster-pro"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
