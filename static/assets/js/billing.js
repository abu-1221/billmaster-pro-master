/**
 * BillMaster Pro - Billing Module JavaScript
 * Handles POS-style billing interface
 */

let products = [];
let categories = [];
let cart = [];
let selectedCustomer = null;
let settings = {};

// Initialize billing page
async function initBilling() {
    await loadSettings();
    await loadCategories();
    await loadProducts();
    renderProducts();
    renderCart();
    initEventListeners();
}

// Load settings
async function loadSettings() {
    const result = await BillMaster.api.get('settings.php?action=get');
    if (result.success) {
        settings = result.data;
    }
}

// Load categories
async function loadCategories() {
    const result = await BillMaster.api.get('categories.php?action=list');
    if (result.success) {
        categories = result.data;
        renderCategoryFilters();
    }
}

// Load products
async function loadProducts(categoryId = null, search = '') {
    let url = 'products.php?action=list';
    if (categoryId) url += `&category_id=${categoryId}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    
    const result = await BillMaster.api.get(url);
    if (result.success) {
        products = result.data;
        renderProducts();
    }
}

// Render category filters
function renderCategoryFilters() {
    const container = document.getElementById('categoryFilters');
    if (!container) return;
    
    container.innerHTML = `
        <button class="category-btn active" data-category="">All</button>
        ${categories.map(cat => `
            <button class="category-btn" data-category="${cat.id}">${cat.name}</button>
        `).join('')}
    `;
    
    container.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadProducts(btn.dataset.category);
        });
    });
}

// Render products grid
function renderProducts() {
    const container = document.getElementById('productGrid');
    if (!container) return;
    
    if (products.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-state-icon">📦</div>
                <h3 class="empty-state-title">No Products Found</h3>
                <p>Add products to start billing</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = products.map(product => {
        const stockClass = product.stock_quantity <= 0 ? 'out' : product.stock_quantity <= 5 ? 'low' : '';
        const stockText = product.stock_quantity <= 0 ? 'Out of Stock' : `${product.stock_quantity} ${product.unit}`;
        
        return `
            <div class="product-card ${product.stock_quantity <= 0 ? 'opacity-50' : ''}" 
                 data-product-id="${product.id}"
                 onclick="addToCart(${product.id})">
                <div class="product-card-icon">📦</div>
                <div class="product-card-name" title="${BillMaster.utils.escapeHtml(product.name)}">
                    ${BillMaster.utils.escapeHtml(product.name)}
                </div>
                <div class="product-card-price">${BillMaster.utils.formatCurrency(product.price, settings.currency_symbol || '₹')}</div>
                <div class="product-card-stock ${stockClass}">${stockText}</div>
            </div>
        `;
    }).join('');
}

// Add product to cart
function addToCart(productId) {
    const product = products.find(p => p.id == productId);
    if (!product) return;
    
    if (product.stock_quantity <= 0) {
        BillMaster.toast.warning('Product is out of stock');
        return;
    }
    
    const existingItem = cart.find(item => item.product_id == productId);
    
    if (existingItem) {
        if (existingItem.quantity >= product.stock_quantity) {
            BillMaster.toast.warning('Cannot add more than available stock');
            return;
        }
        existingItem.quantity++;
    } else {
        cart.push({
            product_id: product.id,
            product_name: product.name,
            unit_price: parseFloat(product.price),
            quantity: 1,
            max_stock: product.stock_quantity
        });
    }
    
    renderCart();
    BillMaster.toast.success(`${product.name} added to cart`);
}

// Update cart item quantity
function updateQuantity(productId, change) {
    const item = cart.find(i => i.product_id == productId);
    if (!item) return;
    
    const newQty = item.quantity + change;
    
    if (newQty <= 0) {
        removeFromCart(productId);
        return;
    }
    
    if (newQty > item.max_stock) {
        BillMaster.toast.warning('Cannot exceed available stock');
        return;
    }
    
    item.quantity = newQty;
    renderCart();
}

// Set cart item quantity directly
function setQuantity(productId, quantity) {
    const item = cart.find(i => i.product_id == productId);
    if (!item) return;
    
    const qty = parseInt(quantity) || 1;
    
    if (qty <= 0) {
        removeFromCart(productId);
        return;
    }
    
    if (qty > item.max_stock) {
        BillMaster.toast.warning('Cannot exceed available stock');
        item.quantity = item.max_stock;
    } else {
        item.quantity = qty;
    }
    
    renderCart();
}

// Remove item from cart
function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id != productId);
    renderCart();
}

// Clear cart
function clearCart() {
    if (cart.length === 0) return;
    
    if (confirm('Are you sure you want to clear the cart?')) {
        cart = [];
        selectedCustomer = null;
        renderCart();
        BillMaster.toast.info('Cart cleared');
    }
}

// Calculate cart totals
function calculateTotals() {
    const subtotal = cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);
    const taxRate = parseFloat(settings.tax_rate) || 0;
    const taxAmount = subtotal * (taxRate / 100);
    const total = subtotal + taxAmount;
    
    return { subtotal, taxRate, taxAmount, total };
}

// Render cart
function renderCart() {
    const itemsContainer = document.getElementById('cartItems');
    const summaryContainer = document.getElementById('cartSummary');
    const cartCount = document.getElementById('cartCount');
    
    if (!itemsContainer) return;
    
    // Update cart count
    if (cartCount) {
        cartCount.textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
    }
    
    // Render items
    if (cart.length === 0) {
        itemsContainer.innerHTML = `
            <div class="cart-empty">
                <div class="cart-empty-icon">🛒</div>
                <p>Your cart is empty</p>
                <p style="font-size: 0.8rem;">Click on products to add them</p>
            </div>
        `;
    } else {
        const currency = settings.currency_symbol || '₹';
        itemsContainer.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-name">${BillMaster.utils.escapeHtml(item.product_name)}</div>
                    <div class="cart-item-price">${BillMaster.utils.formatCurrency(item.unit_price, currency)} × ${item.quantity}</div>
                </div>
                <div class="cart-item-qty">
                    <button class="qty-btn" onclick="updateQuantity(${item.product_id}, -1)">−</button>
                    <input type="number" class="qty-input" value="${item.quantity}" min="1" max="${item.max_stock}"
                           onchange="setQuantity(${item.product_id}, this.value)">
                    <button class="qty-btn" onclick="updateQuantity(${item.product_id}, 1)">+</button>
                </div>
                <div class="cart-item-total">${BillMaster.utils.formatCurrency(item.unit_price * item.quantity, currency)}</div>
                <button class="cart-item-remove" onclick="removeFromCart(${item.product_id})">✕</button>
            </div>
        `).join('');
    }
    
    // Render summary
    if (summaryContainer) {
        const { subtotal, taxRate, taxAmount, total } = calculateTotals();
        const currency = settings.currency_symbol || '₹';
        
        summaryContainer.innerHTML = `
            <div class="summary-row">
                <span>Subtotal</span>
                <span>${BillMaster.utils.formatCurrency(subtotal, currency)}</span>
            </div>
            ${taxRate > 0 ? `
            <div class="summary-row">
                <span>Tax (${taxRate}%)</span>
                <span>${BillMaster.utils.formatCurrency(taxAmount, currency)}</span>
            </div>
            ` : ''}
            <div class="summary-row total">
                <span>Total</span>
                <span class="amount">${BillMaster.utils.formatCurrency(total, currency)}</span>
            </div>
        `;
    }
    
    // Update customer display
    renderSelectedCustomer();
}

// Render selected customer
function renderSelectedCustomer() {
    const container = document.getElementById('selectedCustomer');
    if (!container) return;
    
    if (selectedCustomer) {
        container.innerHTML = `
            <div class="selected-customer">
                <div class="selected-customer-info">
                    <div class="selected-customer-icon">👤</div>
                    <div>
                        <div class="selected-customer-name">${BillMaster.utils.escapeHtml(selectedCustomer.name)}</div>
                        <div class="selected-customer-phone">${selectedCustomer.phone || 'No phone'}</div>
                    </div>
                </div>
                <button class="btn btn-sm btn-ghost" onclick="clearCustomer()">✕</button>
            </div>
        `;
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Search customers
async function searchCustomers(query) {
    const dropdown = document.getElementById('customerDropdown');
    if (!dropdown) return;
    
    if (query.length < 2) {
        dropdown.style.display = 'none';
        return;
    }
    
    const result = await BillMaster.api.get(`customers.php?action=search&q=${encodeURIComponent(query)}`);
    
    if (result.success && result.data.length > 0) {
        dropdown.innerHTML = result.data.map(customer => `
            <div class="customer-dropdown-item" onclick="selectCustomer(${JSON.stringify(customer).replace(/"/g, '&quot;')})">
                <span>👤</span>
                <div>
                    <div style="font-weight: 500;">${BillMaster.utils.escapeHtml(customer.name)}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${customer.phone || customer.email || ''}</div>
                </div>
            </div>
        `).join('');
        dropdown.style.display = 'block';
    } else {
        dropdown.innerHTML = `
            <div class="customer-dropdown-item" onclick="openNewCustomerModal()">
                <span>➕</span>
                <div>Add new customer</div>
            </div>
        `;
        dropdown.style.display = 'block';
    }
}

// Select customer
function selectCustomer(customer) {
    selectedCustomer = customer;
    document.getElementById('customerSearch').value = '';
    document.getElementById('customerDropdown').style.display = 'none';
    renderSelectedCustomer();
}

// Clear customer
function clearCustomer() {
    selectedCustomer = null;
    renderSelectedCustomer();
}

// Open checkout modal
function openCheckout() {
    if (cart.length === 0) {
        BillMaster.toast.warning('Please add items to cart first');
        return;
    }
    
    const { subtotal, taxRate, taxAmount, total } = calculateTotals();
    const currency = settings.currency_symbol || '₹';
    
    const checkoutSummary = document.getElementById('checkoutSummary');
    if (checkoutSummary) {
        checkoutSummary.innerHTML = `
            <div class="summary-row"><span>Subtotal</span><span>${BillMaster.utils.formatCurrency(subtotal, currency)}</span></div>
            ${taxRate > 0 ? `<div class="summary-row"><span>Tax (${taxRate}%)</span><span>${BillMaster.utils.formatCurrency(taxAmount, currency)}</span></div>` : ''}
            <div class="summary-row total"><span>Total</span><span class="amount">${BillMaster.utils.formatCurrency(total, currency)}</span></div>
        `;
    }
    
    BillMaster.modal.open('checkoutModal');
}

// Process payment
async function processPayment() {
    const paymentMethod = document.getElementById('paymentMethod').value;
    const paymentStatus = document.getElementById('paymentStatus').value;
    
    const { subtotal, taxRate, taxAmount, total } = calculateTotals();
    
    const invoiceData = {
        customer_id: selectedCustomer?.id || null,
        items: cart.map(item => ({
            product_id: item.product_id,
            product_name: item.product_name,
            quantity: item.quantity,
            unit_price: item.unit_price
        })),
        tax_rate: taxRate,
        discount_amount: 0,
        payment_method: paymentMethod,
        payment_status: paymentStatus
    };
    
    BillMaster.loader.show('Processing payment...');
    
    const result = await BillMaster.api.post('invoices.php?action=create', invoiceData);
    
    BillMaster.loader.hide();
    BillMaster.modal.close('checkoutModal');
    
    if (result.success) {
        BillMaster.toast.success('Invoice created successfully!');
        
        // Show print option
        if (confirm('Invoice created! Do you want to print the receipt?')) {
            printInvoice(result.invoice_id);
        }
        
        // Reset cart
        cart = [];
        selectedCustomer = null;
        renderCart();
        loadProducts(); // Refresh stock
    } else {
        BillMaster.toast.error(result.message || 'Failed to create invoice');
    }
}

// Print invoice
async function printInvoice(invoiceId) {
    const result = await BillMaster.api.get(`invoices.php?action=get&id=${invoiceId}`);
    
    if (!result.success) {
        BillMaster.toast.error('Failed to load invoice');
        return;
    }
    
    const invoice = result.data;
    const s = invoice.settings;
    const currency = s.currency_symbol || '₹';
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invoice ${invoice.invoice_number}</title>
            <style>
                body { font-family: 'Courier New', monospace; font-size: 12px; max-width: 80mm; margin: 0 auto; padding: 10px; }
                .header { text-align: center; border-bottom: 1px dashed #000; padding-bottom: 10px; margin-bottom: 10px; }
                .header h2 { margin: 0 0 5px; font-size: 16px; }
                .info { margin-bottom: 10px; }
                .items { border-top: 1px dashed #000; border-bottom: 1px dashed #000; padding: 10px 0; margin: 10px 0; }
                .item { display: flex; justify-content: space-between; margin-bottom: 5px; }
                .totals { text-align: right; }
                .total-line { display: flex; justify-content: space-between; }
                .grand-total { font-weight: bold; border-top: 1px solid #000; padding-top: 5px; margin-top: 5px; }
                .footer { text-align: center; margin-top: 15px; font-size: 11px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>${s.business_name || 'BillMaster Pro'}</h2>
                <p>${s.business_address || ''}</p>
                <p>${s.business_phone || ''}</p>
            </div>
            
            <div class="info">
                <p><strong>Invoice:</strong> ${invoice.invoice_number}</p>
                <p><strong>Date:</strong> ${BillMaster.utils.formatDateTime(invoice.created_at)}</p>
                ${invoice.customer_name ? `<p><strong>Customer:</strong> ${invoice.customer_name}</p>` : ''}
            </div>
            
            <div class="items">
                ${invoice.items.map(item => `
                    <div class="item">
                        <span>${item.product_name}</span>
                        <span>${item.quantity} × ${currency}${parseFloat(item.unit_price).toFixed(2)}</span>
                    </div>
                `).join('')}
            </div>
            
            <div class="totals">
                <div class="total-line"><span>Subtotal:</span><span>${currency}${parseFloat(invoice.subtotal).toFixed(2)}</span></div>
                ${parseFloat(invoice.tax_amount) > 0 ? `
                <div class="total-line"><span>Tax (${invoice.tax_rate}%):</span><span>${currency}${parseFloat(invoice.tax_amount).toFixed(2)}</span></div>
                ` : ''}
                <div class="total-line grand-total"><span>TOTAL:</span><span>${currency}${parseFloat(invoice.total_amount).toFixed(2)}</span></div>
            </div>
            
            <div class="footer">
                <p>Payment: ${invoice.payment_method.toUpperCase()} - ${invoice.payment_status.toUpperCase()}</p>
                <p>Thank you for your business!</p>
            </div>
            
            <script>window.print(); window.close();</script>
        </body>
        </html>
    `);
}

// Initialize event listeners
function initEventListeners() {
    // Product search
    const productSearch = document.getElementById('productSearch');
    if (productSearch) {
        productSearch.addEventListener('input', BillMaster.utils.debounce((e) => {
            loadProducts(null, e.target.value);
        }, 300));
    }
    
    // Customer search
    const customerSearch = document.getElementById('customerSearch');
    if (customerSearch) {
        customerSearch.addEventListener('input', BillMaster.utils.debounce((e) => {
            searchCustomers(e.target.value);
        }, 300));
        
        customerSearch.addEventListener('blur', () => {
            setTimeout(() => {
                document.getElementById('customerDropdown').style.display = 'none';
            }, 200);
        });
    }
}

// New customer modal
function openNewCustomerModal() {
    document.getElementById('customerDropdown').style.display = 'none';
    BillMaster.modal.open('newCustomerModal');
}

// Save new customer
async function saveNewCustomer() {
    const name = document.getElementById('newCustomerName').value.trim();
    const phone = document.getElementById('newCustomerPhone').value.trim();
    const email = document.getElementById('newCustomerEmail').value.trim();
    
    if (!name) {
        BillMaster.toast.error('Please enter customer name');
        return;
    }
    
    const result = await BillMaster.api.post('customers.php?action=create', {
        name, phone, email, customer_type: 'individual'
    });
    
    if (result.success) {
        BillMaster.toast.success('Customer added successfully');
        BillMaster.modal.close('newCustomerModal');
        
        // Select the new customer
        selectedCustomer = { id: result.id, name, phone, email };
        renderSelectedCustomer();
        
        // Clear form
        document.getElementById('newCustomerName').value = '';
        document.getElementById('newCustomerPhone').value = '';
        document.getElementById('newCustomerEmail').value = '';
    } else {
        BillMaster.toast.error(result.message || 'Failed to add customer');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initBilling);
