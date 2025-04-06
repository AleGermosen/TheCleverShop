/**
 * Cart functionality for both logged-in and guest users
 */

// Initialize cart when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get authentication status from the data attribute on body tag
    const isLoggedIn = document.body.getAttribute('data-user-authenticated') === 'true';
    
    if (!isLoggedIn) {
        // Initialize guest cart if not existing
        if (!localStorage.getItem('guestCart')) {
            localStorage.setItem('guestCart', JSON.stringify({
                items: [],
                lastUpdated: new Date().toISOString()
            }));
        }
        
        // Load and display guest cart items if we're on the cart page
        const cartTable = document.querySelector('.cart-table');
        if (cartTable) {
            loadGuestCart();
            setupGuestCartControls();
        }
    }
    
    // Setup quantity button handlers for all users
    setupQuantityButtons();
});

/**
 * Set up the quantity buttons for logged-in and guest users
 */
function setupQuantityButtons() {
    // Track which items are being updated to prevent multiple rapid clicks
    const updatingItems = new Set();
    
    // Handle quantity buttons with delegated event handling
    document.addEventListener('click', function(event) {
        // Check if clicked element or its parent is a quantity button
        const button = event.target.closest('.quantity-btn');
        if (!button) return;
        
        event.preventDefault(); // Prevent any default action
        
        const itemId = button.dataset.itemId;
        // Skip if this item is already being updated
        if (updatingItems.has(itemId)) {
            console.log(`Item ${itemId} update already in progress, skipping`);
            return;
        }
        
        const action = button.dataset.action;
        const display = button.parentElement.querySelector('.quantity-display');
        
        // Mark this item as being updated
        updatingItems.add(itemId);
        
        // Flash the button to show it's been clicked
        button.classList.add('active');
        setTimeout(() => button.classList.remove('active'), 200);
        
        // Check if user is logged in
        const isLoggedIn = document.body.getAttribute('data-user-authenticated') === 'true';
        
        if (isLoggedIn) {
            // Use server-side cart update for logged-in users
            updateQuantity(itemId, action, display)
                .finally(() => {
                    // Remove from updating set whether successful or not
                    setTimeout(() => {
                        updatingItems.delete(itemId);
                        console.log(`Item ${itemId} update completed, ready for more updates`);
                    }, 500); // Add small delay to prevent too rapid clicks
                });
        } else {
            // Use localStorage cart update for guest users
            let currentValue = parseInt(display.textContent.trim());
            let maxValue = parseInt(display.dataset.max || 100);
            let newValue = currentValue;

            if (action === 'increase') {
                newValue = Math.min(currentValue + 1, maxValue);
            } else if (action === 'decrease') {
                newValue = Math.max(currentValue - 1, 1);
            }

            if (newValue !== currentValue) {
                updateGuestCartItemQuantity(itemId, newValue);
                // Re-render the cart display
                loadGuestCart();
            }
            
            // Remove from updating set
            setTimeout(() => {
                updatingItems.delete(itemId);
            }, 500);
        }
    });
}

/**
 * Update quantity for logged-in users via server API
 */
async function updateQuantity(itemId, action, display) {
    try {
        console.log(`Updating item ${itemId}: ${action} from ${display.textContent}`);
        
        let currentValue = parseInt(display.textContent.trim());
        let maxValue = parseInt(display.dataset.max);
        let newValue = currentValue;

        if (action === 'increase') {
            newValue = Math.min(currentValue + 1, maxValue);
        } else if (action === 'decrease') {
            newValue = Math.max(currentValue - 1, 1);
        }

        // If the value hasn't changed, don't do anything
        if (newValue === currentValue) {
            console.log('Value unchanged, not updating');
            return;
        }
        
        // Save original value
        const originalValue = currentValue;
        
        // Update the display immediately for visual feedback
        display.textContent = newValue;
        
        // Get price elements to update
        const row = display.closest('tr');
        const priceCell = row.querySelector('.unit-price');
        const totalCell = row.querySelector('.item-total');
        
        // Get unit price and calculate new total
        const unitPrice = parseFloat(priceCell.textContent.replace('$', ''));
        const newTotal = (unitPrice * newValue).toFixed(2);
        
        // Update the total cell immediately for better user feedback
        totalCell.textContent = '$' + newTotal;
        
        // Calculate and update the cart summary immediately
        updateCartSummaryImmediately(unitPrice * (newValue - currentValue));
        
        // Highlight row to show activity
        row.classList.add('table-light');
        
        // Send the update to the server to get accurate price calculations
        const response = await fetch(`/store/cart/update/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                quantity: newValue
            })
        });
        
        // Remove highlight
        row.classList.remove('table-light');
        
        // Check if the response is ok
        if (!response.ok) {
            console.error(`Server responded with ${response.status}: ${response.statusText}`);
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Server response:', data);
        
        if (data.success) {
            // Update with server-calculated total in case there are discounts or other adjustments
            totalCell.textContent = '$' + parseFloat(data.item_total).toFixed(2);
            
            // Update cart summary with accurate server data
            updateCartSummary(data);
        } else {
            // Revert to original value and show error
            display.textContent = originalValue;
            totalCell.textContent = '$' + (unitPrice * originalValue).toFixed(2);
            
            // Revert the cart summary changes
            updateCartSummaryImmediately(unitPrice * (originalValue - newValue));
            
            console.error('Error from server:', data.error);
            alert(data.error || 'Error updating cart');
        }
    } catch (error) {
        console.error('Error updating quantity:', error);
        // If we've made it this far, revert the display value
        display.textContent = originalValue || "1";
        
        // Remove any highlighting
        const row = display.closest('tr');
        if (row) {
            row.classList.remove('table-light');
        }
    }
}

/**
 * Load and display guest cart
 */
function loadGuestCart() {
    const guestCartData = JSON.parse(localStorage.getItem('guestCart'));
    if (!guestCartData || !guestCartData.items || guestCartData.items.length === 0) {
        // Show empty cart message
        const mainContent = document.querySelector('#content');
        if (mainContent) {
            mainContent.innerHTML = `
                <h1 class="mb-4">Shopping Cart</h1>
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
    
    // Calculate cart totals
    let subtotal = 0;
    guestCartData.items.forEach(item => {
        subtotal += item.price * item.quantity;
    });
    
    const shipping = subtotal >= 50 ? 0 : 5;
    const tax = subtotal * 0.1;
    const total = subtotal + shipping + tax;
    
    // Update cart summary
    const subtotalDisplay = document.querySelector('.card-body .d-flex:nth-child(2) span:last-child');
    if (subtotalDisplay) subtotalDisplay.textContent = '$' + subtotal.toFixed(2);
    
    const shippingDisplay = document.querySelector('.card-body .d-flex:nth-child(3) span:last-child');
    if (shippingDisplay) shippingDisplay.textContent = shipping === 0 ? 'Free' : '$5.00';
    
    const taxDisplay = document.querySelector('.card-body .d-flex:nth-child(4) span:last-child');
    if (taxDisplay) taxDisplay.textContent = '$' + tax.toFixed(2);
    
    const totalDisplay = document.querySelector('.card-body .d-flex:nth-child(6) strong:last-child');
    if (totalDisplay) totalDisplay.textContent = '$' + total.toFixed(2);
    
    // Get the tbody element
    const tableBody = document.querySelector('.cart-table tbody');
    if (!tableBody) return;
    
    // Clear existing items
    tableBody.innerHTML = '';
    
    // Add each item to the cart display
    guestCartData.items.forEach((item, index) => {
        const row = document.createElement('tr');
        
        // Calculate item total
        const itemTotal = (item.price * item.quantity).toFixed(2);
        
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
            <td class="item-total">$${itemTotal}</td>
            <td>
                <button type="button" class="btn btn-outline-danger btn-sm remove-item-btn" data-item-id="${index}">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

/**
 * Set up guest cart controls (remove buttons)
 */
function setupGuestCartControls() {
    // Handle remove buttons
    document.addEventListener('click', function(event) {
        const removeBtn = event.target.closest('.remove-item-btn');
        if (!removeBtn) return;
        
        const itemId = parseInt(removeBtn.getAttribute('data-item-id'));
        removeGuestCartItem(itemId);
        loadGuestCart(); // Re-render cart
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
 * Update cart summary immediately based on price difference
 */
function updateCartSummaryImmediately(priceDifference) {
    // Update subtotal
    const subtotalDisplay = document.querySelector('.card-body .d-flex:nth-child(2) span:last-child');
    if (subtotalDisplay) {
        const currentSubtotal = parseFloat(subtotalDisplay.textContent.replace('$', ''));
        const newSubtotal = (currentSubtotal + priceDifference).toFixed(2);
        subtotalDisplay.textContent = '$' + newSubtotal;
        
        // Update shipping (free if subtotal >= 50)
        const shippingDisplay = document.querySelector('.card-body .d-flex:nth-child(3) span:last-child');
        if (shippingDisplay) {
            const newShippingText = parseFloat(newSubtotal) >= 50 ? 'Free' : '$5.00';
            shippingDisplay.textContent = newShippingText;
        }
        
        // Update tax (10%)
        const taxDisplay = document.querySelector('.card-body .d-flex:nth-child(4) span:last-child');
        if (taxDisplay) {
            const newTax = (parseFloat(newSubtotal) * 0.1).toFixed(2);
            taxDisplay.textContent = '$' + newTax;
        }
        
        // Update total
        const totalDisplay = document.querySelector('.card-body .d-flex:nth-child(6) strong:last-child');
        if (totalDisplay) {
            const shippingCost = parseFloat(newSubtotal) >= 50 ? 0 : 5;
            const newTotal = (parseFloat(newSubtotal) + shippingCost + parseFloat(newSubtotal) * 0.1).toFixed(2);
            totalDisplay.textContent = '$' + newTotal;
        }
        
        // Update free shipping alert
        const freeShippingAlert = document.querySelector('.alert-info');
        if (freeShippingAlert) {
            if (parseFloat(newSubtotal) >= 50) {
                freeShippingAlert.style.display = 'none';
            } else {
                const amountNeeded = (50 - parseFloat(newSubtotal)).toFixed(2);
                const messageElement = freeShippingAlert.querySelector('i');
                if (messageElement) {
                    messageElement.nextSibling.textContent = ` Add $${amountNeeded} more to your cart to get free shipping!`;
                }
                freeShippingAlert.style.display = 'block';
            }
        }
    }
}

/**
 * Update cart summary with server data
 */
function updateCartSummary(data) {
    // Update subtotal
    const subtotalDisplay = document.querySelector('.card-body .d-flex:nth-child(2) span:last-child');
    if (subtotalDisplay) {
        subtotalDisplay.textContent = '$' + parseFloat(data.subtotal).toFixed(2);
    }
    
    // Update shipping
    const shippingDisplay = document.querySelector('.card-body .d-flex:nth-child(3) span:last-child');
    if (shippingDisplay) {
        shippingDisplay.textContent = parseFloat(data.shipping_cost) === 0 ? 'Free' : '$' + parseFloat(data.shipping_cost).toFixed(2);
    }
    
    // Update tax
    const taxDisplay = document.querySelector('.card-body .d-flex:nth-child(4) span:last-child');
    if (taxDisplay) {
        taxDisplay.textContent = '$' + parseFloat(data.tax_amount).toFixed(2);
    }
    
    // Update total
    const totalDisplay = document.querySelector('.card-body .d-flex:nth-child(6) strong:last-child');
    if (totalDisplay) {
        totalDisplay.textContent = '$' + parseFloat(data.total).toFixed(2);
    }
    
    // Update free shipping alert
    const freeShippingAlert = document.querySelector('.alert-info');
    if (freeShippingAlert) {
        if (data.free_shipping_eligible) {
            freeShippingAlert.style.display = 'none';
        } else {
            const amountNeeded = parseFloat(data.amount_needed_for_free_shipping).toFixed(2);
            const messageElement = freeShippingAlert.querySelector('i');
            if (messageElement) {
                messageElement.nextSibling.textContent = ` Add $${amountNeeded} more to your cart to get free shipping!`;
            }
            freeShippingAlert.style.display = 'block';
        }
    }
    
    // Update cart count in navbar
    const cartCountBadge = document.querySelector('.cart-count');
    if (cartCountBadge) {
        cartCountBadge.textContent = data.cart_count;
    }
} 