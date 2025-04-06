/**
 * Guest Cart functionality for non-logged in users
 * Stores cart data in localStorage to persist between page reloads
 */

// Initialize guest cart when page loads
document.addEventListener('DOMContentLoaded', function() {
    initGuestCart();
    updateCartCount();

    // Add event listener for Add to Cart form for non-logged in users
    setupAddToCartForm();

    // Setup cart page functionality if we're on the cart page
    const cartTable = document.querySelector('.cart-table');
    if (cartTable) {
        renderGuestCart();
        setupCartControls();
    }
});

/**
 * Initialize the guest cart in localStorage if it doesn't exist
 */
function initGuestCart() {
    if (!localStorage.getItem('guestCart')) {
        localStorage.setItem('guestCart', JSON.stringify({
            items: [],
            lastUpdated: new Date().toISOString()
        }));
    }
}

/**
 * Update the cart count in the navigation bar
 */
function updateCartCount() {
    const cartCountBadge = document.querySelector('.cart-count');
    if (cartCountBadge) {
        const guestCart = JSON.parse(localStorage.getItem('guestCart')) || { items: [] };
        let count = 0;
        
        // Sum quantities of all items
        guestCart.items.forEach(item => {
            count += item.quantity;
        });
        
        cartCountBadge.textContent = count;
    }
}

/**
 * Set up the Add to Cart form for non-logged in users
 */
function setupAddToCartForm() {
    // Only proceed if user is not logged in (check via the body data attribute)
    const isLoggedIn = document.body.getAttribute('data-user-authenticated') === 'true';
    if (isLoggedIn) return;
    
    const addToCartForm = document.querySelector('form[action*="add-to-cart"]');
    if (!addToCartForm) return;
    
    // Override form submit to use localStorage instead
    addToCartForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get product data from hidden inputs or data attributes
        const productId = addToCartForm.getAttribute('data-product-id');
        const productName = addToCartForm.getAttribute('data-product-name');
        const productPrice = parseFloat(addToCartForm.getAttribute('data-product-price'));
        const productCategory = addToCartForm.getAttribute('data-product-category');
        const productImage = addToCartForm.getAttribute('data-product-image');
        const maxQuantity = parseInt(addToCartForm.getAttribute('data-product-stock')) || 10;
        
        // Get quantity from input
        const quantityInput = document.getElementById('quantity');
        const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
        
        // Get selected size if any
        let size = null;
        let sizeId = null;
        let finalPrice = productPrice;
        
        const sizeInput = document.querySelector('input[name="size_id"]:checked');
        if (sizeInput) {
            sizeId = sizeInput.value;
            size = sizeInput.getAttribute('data-size-name');
            const sizePrice = parseFloat(sizeInput.getAttribute('data-price'));
            if (!isNaN(sizePrice)) {
                finalPrice = sizePrice;
            }
        }
        
        // Add to guest cart
        addToGuestCart(productId, productName, finalPrice, quantity, size, sizeId, productCategory, productImage, maxQuantity);
        
        // Show success message
        const successToast = document.createElement('div');
        successToast.className = 'position-fixed bottom-0 end-0 p-3';
        successToast.style.zIndex = '9999';
        successToast.innerHTML = `
            <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <strong class="me-auto">Added to Cart</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${productName} has been added to your cart.
                </div>
            </div>
        `;
        document.body.appendChild(successToast);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            successToast.remove();
        }, 3000);
        
        // Update cart count
        updateCartCount();
    });
}

/**
 * Add a product to the guest cart
 */
function addToGuestCart(productId, name, price, quantity, size, sizeId, category, image, maxQuantity) {
    // Get current cart
    const guestCart = JSON.parse(localStorage.getItem('guestCart')) || {
        items: [],
        lastUpdated: new Date().toISOString()
    };
    
    // Check if product already in cart
    let found = false;
    for (const item of guestCart.items) {
        if (item.product_id == productId && (item.size_id == sizeId || (!item.size_id && !sizeId))) {
            // Update quantity
            item.quantity += quantity;
            found = true;
            break;
        }
    }
    
    // Add new item if not found
    if (!found) {
        guestCart.items.push({
            product_id: productId,
            name: name,
            price: price,
            quantity: quantity,
            category: category,
            image: image,
            size: size,
            size_id: sizeId,
            max_quantity: maxQuantity
        });
    }
    
    // Update timestamp
    guestCart.lastUpdated = new Date().toISOString();
    
    // Save to localStorage
    localStorage.setItem('guestCart', JSON.stringify(guestCart));
}

/**
 * Render the guest cart on the cart page
 */
function renderGuestCart() {
    // Only proceed if user is not logged in
    const isLoggedIn = document.body.getAttribute('data-user-authenticated') === 'true';
    if (isLoggedIn) return;
    
    const guestCart = JSON.parse(localStorage.getItem('guestCart')) || { items: [] };
    
    // Check if cart is empty
    if (!guestCart.items.length) {
        // Show empty cart message
        const mainContent = document.querySelector('#content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-cart3 display-1 text-muted"></i>
                    <h3 class="mt-3">Your cart is empty</h3>
                    <p class="text-muted">Looks like you haven't added any items to your cart yet.</p>
                    <a href="/store/products/" class="btn btn-primary mt-3">
                        Start Shopping
                    </a>
                </div>
            `;
        }
        return;
    }
    
    // Get the cart table body
    const cartTableBody = document.querySelector('.cart-table tbody');
    if (!cartTableBody) return;
    
    // Clear existing content
    cartTableBody.innerHTML = '';
    
    // Calculate totals
    let subtotal = 0;
    
    // Add each item to the table
    guestCart.items.forEach((item, index) => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    ${item.image ? `<img src="${item.image}" alt="${item.name}" class="img-thumbnail me-3" style="width: 50px;">` : ''}
                    <div>
                        <h6 class="mb-0">${item.name}</h6>
                        <small class="text-muted">${item.category || ''}</small>
                        ${item.size ? `<small class="d-block text-muted">Size: ${item.size}</small>` : ''}
                    </div>
                </div>
            </td>
            <td class="unit-price">$${item.price.toFixed(2)}</td>
            <td>
                <div class="input-group" style="width: 130px;">
                    <button type="button" class="btn btn-primary btn-sm quantity-btn" data-item-id="${index}" data-action="decrease" style="height: 38px; width: 38px;">
                        <i class="bi bi-dash"></i>
                    </button>
                    <span class="form-control text-center quantity-display" style="background-color: #f8f9fa; font-weight: bold; font-size: 1.1rem; padding-top: 6px;" data-max="${item.max_quantity}" data-item-id="${index}">
                        ${item.quantity}
                    </span>
                    <button type="button" class="btn btn-primary btn-sm quantity-btn" data-item-id="${index}" data-action="increase" style="height: 38px; width: 38px;">
                        <i class="bi bi-plus"></i>
                    </button>
                </div>
            </td>
            <td class="item-total">$${itemTotal.toFixed(2)}</td>
            <td>
                <button type="button" class="btn btn-outline-danger btn-sm remove-item-btn" data-item-id="${index}">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        cartTableBody.appendChild(row);
    });
    
    // Update summary section
    updateCartSummary(subtotal);
}

/**
 * Update the cart summary with calculated totals
 */
function updateCartSummary(subtotal) {
    const shipping = subtotal >= 50 ? 0 : 5;
    const tax = subtotal * 0.1;
    const total = subtotal + shipping + tax;
    
    // Update DOM elements
    const subtotalEl = document.querySelector('.card-body .d-flex:nth-child(2) span:last-child');
    if (subtotalEl) subtotalEl.textContent = '$' + subtotal.toFixed(2);
    
    const shippingEl = document.querySelector('.card-body .d-flex:nth-child(3) span:last-child');
    if (shippingEl) shippingEl.textContent = shipping === 0 ? 'Free' : '$5.00';
    
    const taxEl = document.querySelector('.card-body .d-flex:nth-child(4) span:last-child');
    if (taxEl) taxEl.textContent = '$' + tax.toFixed(2);
    
    const totalEl = document.querySelector('.card-body .d-flex:nth-child(6) strong:last-child');
    if (totalEl) totalEl.textContent = '$' + total.toFixed(2);
    
    // Update free shipping alert
    const freeShippingAlert = document.querySelector('.alert-info');
    if (freeShippingAlert) {
        if (subtotal >= 50) {
            freeShippingAlert.style.display = 'none';
        } else {
            const amountNeeded = (50 - subtotal).toFixed(2);
            freeShippingAlert.innerHTML = `
                <i class="bi bi-info-circle"></i>
                Add $${amountNeeded} more to your cart to get free shipping!
            `;
            freeShippingAlert.style.display = 'block';
        }
    }
}

/**
 * Set up cart controls (quantity buttons, remove buttons)
 */
function setupCartControls() {
    // Only proceed if user is not logged in
    const isLoggedIn = document.body.getAttribute('data-user-authenticated') === 'true';
    if (isLoggedIn) return;
    
    // Handle quantity buttons
    document.addEventListener('click', function(event) {
        const quantityBtn = event.target.closest('.quantity-btn');
        if (!quantityBtn) return;
        
        const itemId = parseInt(quantityBtn.getAttribute('data-item-id'));
        const action = quantityBtn.getAttribute('data-action');
        const display = quantityBtn.parentElement.querySelector('.quantity-display');
        const currentValue = parseInt(display.textContent);
        const maxValue = parseInt(display.getAttribute('data-max') || 100);
        
        let newValue = currentValue;
        
        if (action === 'increase') {
            newValue = Math.min(currentValue + 1, maxValue);
        } else if (action === 'decrease') {
            newValue = Math.max(currentValue - 1, 1);
        }
        
        if (newValue !== currentValue) {
            updateGuestCartItemQuantity(itemId, newValue);
            renderGuestCart(); // Re-render cart
        }
    });
    
    // Handle remove buttons
    document.addEventListener('click', function(event) {
        const removeBtn = event.target.closest('.remove-item-btn');
        if (!removeBtn) return;
        
        const itemId = parseInt(removeBtn.getAttribute('data-item-id'));
        removeGuestCartItem(itemId);
        renderGuestCart(); // Re-render cart
    });
}

/**
 * Update quantity of an item in the guest cart
 */
function updateGuestCartItemQuantity(itemId, newQuantity) {
    const guestCart = JSON.parse(localStorage.getItem('guestCart'));
    if (!guestCart || !guestCart.items || !guestCart.items[itemId]) return;
    
    guestCart.items[itemId].quantity = newQuantity;
    guestCart.lastUpdated = new Date().toISOString();
    
    localStorage.setItem('guestCart', JSON.stringify(guestCart));
    updateCartCount();
}

/**
 * Remove an item from the guest cart
 */
function removeGuestCartItem(itemId) {
    const guestCart = JSON.parse(localStorage.getItem('guestCart'));
    if (!guestCart || !guestCart.items || !guestCart.items[itemId]) return;
    
    guestCart.items.splice(itemId, 1);
    guestCart.lastUpdated = new Date().toISOString();
    
    localStorage.setItem('guestCart', JSON.stringify(guestCart));
    updateCartCount();
} 