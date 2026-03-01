/**
 * BillMaster Pro - Core Application JavaScript
 * Professional, Clean, Fully Functional
 */

// Detect if running from file system (won't work - needs server)
<<<<<<< HEAD
const isFileProtocol = window.location.protocol === 'file:';

// Auto-detect API base URL - Python Flask backend
const API_BASE = (() => {
    // If running from file system, use localhost:5000 as fallback
    if (window.location.protocol === 'file:') {
        return 'http://localhost:5000/api';
    }
    // For local and hosted servers, use relative path
    return window.location.origin + '/api';
=======
const isFileProtocol = window.location.protocol === "file:";

// Auto-detect API base URL - Python Flask backend
const API_BASE = (() => {
  // If running from file system, use localhost:5000 as fallback
  if (window.location.protocol === "file:") {
    return "http://localhost:5000/api";
  }
  // For local and hosted servers, use relative path
  return window.location.origin + "/api";
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
})();

// API Helper Functions
const api = {
<<<<<<< HEAD
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
=======
  async request(endpoint, options = {}) {
    // Check if running from file system
    if (isFileProtocol) {
      console.error(
        "Cannot make API requests from file:// protocol. Please use http://localhost:8080",
      );
      return {
        success: false,
        message:
          "Please access this app through http://localhost:8080 (not from file explorer)",
      };
    }

    const url = `${API_BASE}/${endpoint}`;
    const config = {
      headers: { "Content-Type": "application/json" },
      credentials: "include", // Important: Include cookies for session handling
      ...options,
    };

    try {
      const response = await fetch(url, config);

      // Check if response is ok
      if (!response.ok) {
        console.error(
          "API Response Error:",
          response.status,
          response.statusText,
        );
        return { success: false, message: `Server error: ${response.status}` };
      }

      const text = await response.text();

      // Try to parse as JSON
      try {
        return JSON.parse(text);
      } catch (parseError) {
        console.error("JSON Parse Error:", text.substring(0, 200));
        return { success: false, message: "Invalid server response" };
      }
    } catch (error) {
      console.error("API Error:", error);

      // More specific error messages
      if (
        error.name === "TypeError" &&
        error.message.includes("Failed to fetch")
      ) {
        return {
          success: false,
          message:
            "Cannot connect to server. Make sure Python Flask server is running at http://localhost:5000",
        };
      }

      return { success: false, message: "Connection error. Please try again." };
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, data) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};

// Toast Notifications
const toast = {
<<<<<<< HEAD
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
=======
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    }
  },

  show(message, type = "info", duration = 3000) {
    this.init();

    const icons = {
      success: "check-circle",
      error: "alert-circle",
      warning: "alert-triangle",
      info: "info",
    };

    const toastEl = document.createElement("div");
    toastEl.className = `toast toast-${type}`;
    toastEl.innerHTML = `
            <span class="toast-icon">
                <i data-lucide="${icons[type]}" style="width: 18px; height: 18px;"></i>
            </span>
            <span class="toast-message">${message}</span>
        `;

    this.container.appendChild(toastEl);
    if (typeof lucide !== "undefined") {
      lucide.createIcons();
    }

    setTimeout(() => {
      toastEl.style.opacity = "0";
      toastEl.style.transform = "translateX(100%)";
      setTimeout(() => toastEl.remove(), 300);
    }, duration);
  },

  success(message) {
    this.show(message, "success");
  },
  error(message) {
    this.show(message, "error");
  },
  warning(message) {
    this.show(message, "warning");
  },
  info(message) {
    this.show(message, "info");
  },
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};

// Modal Functions
const modal = {
<<<<<<< HEAD
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
=======
  open(id) {
    const modalEl = document.getElementById(id);
    if (modalEl) {
      modalEl.classList.add("active");
      document.body.style.overflow = "hidden";
    }
  },

  close(id) {
    const modalEl = document.getElementById(id);
    if (modalEl) {
      modalEl.classList.remove("active");
      document.body.style.overflow = "";
    }
  },
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};

// Authentication
const auth = {
<<<<<<< HEAD
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
=======
  async check() {
    return await api.get("auth.php?action=check");
  },

  async login(username, password) {
    return await api.post("auth.php?action=login", { username, password });
  },

  async logout() {
    try {
      const result = await api.get("auth.php?action=logout");
      // Always redirect to login, regardless of response
      window.location.replace("login.html");
      return result;
    } catch (error) {
      // Even on error, redirect to login
      window.location.replace("login.html");
      return { success: true };
    }
  },

  async requireAuth() {
    try {
      const result = await this.check();
      if (!result || !result.success) {
        window.location.replace("login.html");
        return null;
      }
      return result.user;
    } catch (error) {
      console.error("Auth check failed:", error);
      window.location.replace("login.html");
      return null;
    }
  },
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};

// Utility Functions
const utils = {
<<<<<<< HEAD
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
=======
  formatCurrency(amount, symbol = "₹") {
    const num = parseFloat(amount) || 0;
    return `${symbol}${num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
  },

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  },

  formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  escapeHtml(text) {
    const div = document.createElement("div");
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
    if (!name) return "?";
    return name
      .split(" ")
      .map((word) => word[0])
      .join("")
      .toUpperCase()
      .substring(0, 2);
  },
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};

// Sidebar Toggle for Mobile
function initSidebar() {
<<<<<<< HEAD
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
=======
  const sidebar = document.querySelector(".sidebar");
  const toggle = document.querySelector(".sidebar-toggle");
  const overlay = document.querySelector(".mobile-overlay");

  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      overlay?.classList.toggle("active");
    });
  }

  if (overlay) {
    overlay.addEventListener("click", () => {
      sidebar?.classList.remove("open");
      overlay.classList.remove("active");
    });
  }

  // Close sidebar on nav click (mobile)
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => {
      if (window.innerWidth <= 1024) {
        sidebar?.classList.remove("open");
        overlay?.classList.remove("active");
      }
    });
  });
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
}

// Initialize User Info in Sidebar
async function initUserInfo() {
<<<<<<< HEAD
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
=======
  const result = await auth.check();
  if (result.success && result.user) {
    const user = result.user;
    const userName = document.querySelector(".user-name");
    const userRole = document.querySelector(".user-role");
    const userAvatar = document.querySelector(".user-avatar");

    if (userName) userName.textContent = user.full_name || "User";
    if (userRole) userRole.textContent = user.role || "staff";
    if (userAvatar)
      userAvatar.textContent = utils.getInitials(user.full_name);

    // Apply role-based restrictions to navigation
    applyRoleRestrictions(user.role);
  }
}

function getDashboardByRole(role) {
  return role === "admin" ? "dashboard.html" : "billing.html";
}

function applyRoleRestrictions(role) {
  const isStaff = role === "staff";
  const pathParts = window.location.pathname.split("/");
  const currentPage = pathParts.pop() || "index.html";

  // System pages that STAFF cannot access
  const adminOnlyPages = [
    "dashboard.html",
    "invoices.html",
    "products.html",
    "expenses.html",
    "categories.html",
    "settings.html",
    "customers.html"
  ];

  // Redirect if staff is on restricted page
  if (isStaff && adminOnlyPages.includes(currentPage)) {
    window.location.replace("billing.html");
    return;
  }

  // Hide restricted sidebar links for Staff
  if (isStaff) {
    document.querySelectorAll(".nav-item").forEach((item) => {
      const href = item.getAttribute("href");
      if (href && adminOnlyPages.includes(href)) {
        item.style.display = "none";
      }
    });

    // Also hide the "System" group if all children are hidden
    const sidebarGroups = document.querySelectorAll(".sidebar-group");
    sidebarGroups.forEach(group => {
      const visibleItems = Array.from(group.querySelectorAll(".nav-item"))
        .filter(item => item.style.display !== "none");
      if (visibleItems.length === 0) {
        group.style.display = "none";
      }
    });
  }
}

// Close modals on outside click
document.addEventListener("click", (e) => {
  if (
    e.target.classList.contains("modal-overlay") &&
    e.target.classList.contains("active")
  ) {
    e.target.classList.remove("active");
    document.body.style.overflow = "";
  }
});

// Close modals on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.active").forEach((modal) => {
      modal.classList.remove("active");
    });
    document.body.style.overflow = "";
  }
});

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initSidebar();
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
});

// Export as global object
window.BillMaster = {
<<<<<<< HEAD
    api,
    toast,
    modal,
    auth,
    utils
=======
  api,
  toast,
  modal,
  auth,
  utils,
  getDashboardByRole
>>>>>>> 4f151ba889a92f5cfc2a6138a048400af67ad5de
};
