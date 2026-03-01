/**
 * BillMaster Pro - Core Application JavaScript
 * Professional, Clean, Fully Functional
 */

// Detect if running from file system (won't work - needs server)
const isFileProtocol = window.location.protocol === 'file:';

// Auto-detect API base URL - Python Flask backend
const API_BASE = (() => {
    // If running from file system, use localhost:5000 as fallback
    if (window.location.protocol === 'file:') {
        return 'http://localhost:5000/api';
    }
    // For local and hosted servers, use relative path
    return window.location.origin + '/api';
})();

// API Helper Functions
const api = {
    async request(endpoint, options = {}) {
        // Check if running from file system
        if (isFileProtocol) {
            console.error('Cannot make API requests from file:// protocol. Please use http://localhost:8080');
            return { 
                success: false, 
                message: 'Please access this app through http://localhost:8080 (not from file explorer)' 
            };
        }
        
        const url = `${API_BASE}/${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // Important: Include cookies for session handling
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // Check if response is ok
            if (!response.ok) {
                console.error('API Response Error:', response.status, response.statusText);
                return { success: false, message: `Server error: ${response.status}` };
            }
            
            const text = await response.text();
            
            // Try to parse as JSON
            try {
                return JSON.parse(text);
            } catch (parseError) {
                console.error('JSON Parse Error:', text.substring(0, 200));
                return { success: false, message: 'Invalid server response' };
            }
        } catch (error) {
            console.error('API Error:', error);
            
            // More specific error messages
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                return { 
                    success: false, 
                    message: 'Cannot connect to server. Make sure Python Flask server is running at http://localhost:5000' 
                };
            }
            
            return { success: false, message: 'Connection error. Please try again.' };
        }
    },
    
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

// Toast Notifications
const toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = 3000) {
        this.init();
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast toast-${type}`;
        toastEl.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
        `;
        
        this.container.appendChild(toastEl);
        
        setTimeout(() => {
            toastEl.style.opacity = '0';
            toastEl.style.transform = 'translateX(100%)';
            setTimeout(() => toastEl.remove(), 300);
        }, duration);
    },
    
    success(message) { this.show(message, 'success'); },
    error(message) { this.show(message, 'error'); },
    warning(message) { this.show(message, 'warning'); },
    info(message) { this.show(message, 'info'); }
};

// Modal Functions
const modal = {
    open(id) {
        const modalEl = document.getElementById(id);
        if (modalEl) {
            modalEl.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    close(id) {
        const modalEl = document.getElementById(id);
        if (modalEl) {
            modalEl.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
};

// Authentication
const auth = {
    async check() {
        return await api.get('auth.php?action=check');
    },
    
    async login(username, password) {
        return await api.post('auth.php?action=login', { username, password });
    },
    
    async logout() {
        try {
            const result = await api.get('auth.php?action=logout');
            // Always redirect to login, regardless of response
            window.location.replace('login.html');
            return result;
        } catch (error) {
            // Even on error, redirect to login
            window.location.replace('login.html');
            return { success: true };
        }
    },
    
    async requireAuth() {
        try {
            const result = await this.check();
            if (!result || !result.success) {
                window.location.replace('login.html');
                return null;
            }
            return result.user;
        } catch (error) {
            console.error('Auth check failed:', error);
            window.location.replace('login.html');
            return null;
        }
    }
};

// Utility Functions
const utils = {
    formatCurrency(amount, symbol = '₹') {
        const num = parseFloat(amount) || 0;
        return `${symbol}${num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    },
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    },
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },
    
    getInitials(name) {
        if (!name) return '?';
        return name.split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);
    }
};

// Sidebar Toggle for Mobile
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    const overlay = document.querySelector('.mobile-overlay');
    
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay?.classList.toggle('active');
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar?.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
    
    // Close sidebar on nav click (mobile)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                sidebar?.classList.remove('open');
                overlay?.classList.remove('active');
            }
        });
    });
}

// Initialize User Info in Sidebar
async function initUserInfo() {
    const result = await auth.check();
    if (result.success && result.user) {
        const userName = document.querySelector('.user-name');
        const userRole = document.querySelector('.user-role');
        const userAvatar = document.querySelector('.user-avatar');
        
        if (userName) userName.textContent = result.user.full_name || 'User';
        if (userRole) userRole.textContent = result.user.role || 'staff';
        if (userAvatar) userAvatar.textContent = utils.getInitials(result.user.full_name);
    }
}

// Initialize Shop Name in Sidebar
async function initShopName() {
    try {
        const result = await api.get('settings.php?action=get');
        if (result.success && result.data && result.data.shop_name) {
            const sidebarBrands = document.querySelectorAll('.sidebar-brand h1');
            sidebarBrands.forEach((el) => {
                el.textContent = result.data.shop_name;
            });
        }
    } catch (error) {
        console.error('Failed to load shop name:', error);
    }
}

// Close modals on outside click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay') && e.target.classList.contains('active')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initShopName();
});

// Export as global object
window.BillMaster = {
    api,
    toast,
    modal,
    auth,
    utils
};
