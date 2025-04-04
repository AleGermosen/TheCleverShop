// Main JavaScript file for CleverCupid

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Prevent dropdown items with toggle from navigating
    document.querySelectorAll('.dropdown-item.dropdown-toggle').forEach(function(item) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // If on mobile, manually show/hide the submenu
            if (window.innerWidth < 992) {
                const submenu = this.nextElementSibling;
                if (submenu && submenu.classList.contains('dropdown-menu')) {
                    if (submenu.style.display === 'block') {
                        submenu.style.display = 'none';
                    } else {
                        submenu.style.display = 'block';
                    }
                }
            }
        });
    });
    
    // Adjust submenu positions to prevent them from going off-screen
    function adjustSubmenuPositions() {
        document.querySelectorAll('.dropdown-submenu > .dropdown-menu').forEach(function(submenu) {
            const rect = submenu.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                submenu.style.right = '100%';
                submenu.style.left = 'auto';
            } else {
                submenu.style.left = '100%';
                submenu.style.right = 'auto';
            }
        });
    }
    
    // Check positions when window is resized
    window.addEventListener('resize', adjustSubmenuPositions);
    
    // Initial check
    setTimeout(adjustSubmenuPositions, 100);

    // Cart quantity buttons
    document.querySelectorAll('.quantity-input').forEach(function(input) {
        input.addEventListener('change', function() {
            if (this.value < 1) this.value = 1;
            if (this.max && this.value > parseInt(this.max)) this.value = this.max;
        });
    });

    // Add to cart animation
    document.querySelectorAll('.add-to-cart-btn').forEach(function(button) {
        button.addEventListener('click', function(e) {
            const cartBadge = document.querySelector('.cart-badge');
            if (cartBadge) {
                cartBadge.classList.remove('cart-badge');
                void cartBadge.offsetWidth; // Trigger reflow
                cartBadge.classList.add('cart-badge');
            }
        });
    });

    // Product gallery
    const mainImage = document.querySelector('.product-main-image');
    document.querySelectorAll('.gallery-thumb').forEach(function(thumb) {
        thumb.addEventListener('click', function() {
            if (mainImage) {
                mainImage.src = this.src;
                document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Toast notifications
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 3000
        });
    });
    toastList.forEach(toast => toast.show());

    // Search form
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[type="search"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // Profile image preview
    const avatarInput = document.querySelector('#avatar');
    if (avatarInput) {
        avatarInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector('.profile-avatar');
                    if (preview) {
                        preview.src = e.target.result;
                    }
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Form validation
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Checkout form
    const checkoutForm = document.querySelector('#checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            const spinner = document.createElement('div');
            spinner.className = 'spinner-overlay';
            spinner.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            `;
            document.body.appendChild(spinner);

            // Simulate form submission (replace with actual form submission)
            setTimeout(() => {
                spinner.remove();
                this.submit();
            }, 1000);
        });
    }

    // Back to top button
    const backToTop = document.querySelector('#back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 100) {
                backToTop.classList.remove('d-none');
            } else {
                backToTop.classList.add('d-none');
            }
        });

        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
}); 