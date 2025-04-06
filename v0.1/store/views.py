from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
import json
import stripe

from .models import Category, Product, Cart, CartItem, Order, OrderItem, ShippingAddress, ProductSize
from .forms import ShippingAddressForm

def home(request):
    featured_products = Product.objects.filter(featured=True)[:8]
    categories = Category.objects.filter(parent=None)
    
    # Get products with images for each category to display in rotating format
    categories_with_products = []
    for category in categories:
        # Get all subcategories
        subcategories = list(category.get_subcategories())
        categories_to_include = [category] + subcategories
        
        # Get all products for this category and its subcategories, not just those with images
        products = Product.objects.filter(
            category__in=categories_to_include
        ).distinct()[:5]  # Limit to 5 products per category
        
        # Always include the category even if it has no products with images
        categories_with_products.append({
            'category': category,
            'products': products
        })
    
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'categories_with_products': categories_with_products
    })

def product_list(request):
    products = Product.objects.all().order_by('name')  # Default sorting by name A-Z
    root_categories = Category.objects.filter(parent=None)
    all_categories = Category.objects.all()
    
    # If this is a POST request for adding to cart, process it
    if request.method == 'POST' and 'product_id' in request.POST:
        product_id = request.POST.get('product_id')
        return add_to_cart(request, product_id)
    
    # Filter by category
    category_slug = request.GET.get('category')
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        # Get products from both the category and all its subcategories
        categories_to_include = [current_category]
        subcategories = current_category.get_subcategories()
        categories_to_include.extend(subcategories)
        products = products.filter(category__in=categories_to_include)
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'root_categories': root_categories,
        'all_categories': all_categories,
        'current_category': current_category,
        'search_query': search_query,
        'sort_by': sort_by
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Find related products - consider both category and parent category relationships
    if product.category.is_subcategory:
        # If product is in a subcategory, get products from same subcategory and sibling subcategories
        related_products = Product.objects.filter(
            Q(category=product.category) |  # Same subcategory
            Q(category__parent=product.category.parent)  # Sibling subcategories
        ).exclude(id=product.id).distinct()[:4]
    else:
        # If product is in a main category, get products from same category and its subcategories
        subcategories = product.category.get_subcategories()
        categories_to_include = [product.category] + list(subcategories)
        related_products = Product.objects.filter(
            category__in=categories_to_include
        ).exclude(id=product.id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.get_subcategories()
    
    # If this is a POST request for adding to cart, process it
    if request.method == 'POST' and 'product_id' in request.POST:
        product_id = request.POST.get('product_id')
        return add_to_cart(request, product_id)
    
    # Get products from both the category and all its subcategories
    categories_to_include = [category]
    categories_to_include.extend(subcategories)
    products = Product.objects.filter(category__in=categories_to_include).order_by('name')  # Default sorting by name A-Z
    
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    return render(request, 'store/category_detail.html', {
        'category': category,
        'subcategories': subcategories,
        'products': products,
        'sort_by': sort_by
    })

def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
    tax_rate = Decimal('0.10')  # 10% tax rate
    tax_amount = subtotal * tax_rate
    total = subtotal + shipping_cost + tax_amount
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'cart_total': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total_amount': total,
        'cart_total_with_shipping': total
    })

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    size_id = request.POST.get('size_id')
    selected_size = None
    
    # Check if size was selected and validate it
    if size_id:
        try:
            selected_size = get_object_or_404(ProductSize, id=size_id, product=product)
            
            # Check if selected size is in stock
            if not selected_size.is_in_stock:
                messages.error(request, f"Sorry, {product.name} in size {selected_size.get_size_display()} is out of stock.")
                return redirect('store:product_detail', slug=product.slug)
                
            # Make sure requested quantity doesn't exceed stock for the size
            if quantity > selected_size.stock:
                messages.warning(request, f"Only {selected_size.stock} units available for {selected_size.get_size_display()}. Quantity adjusted.")
                quantity = selected_size.stock
                
        except (ProductSize.DoesNotExist, ValueError):
            messages.error(request, "Invalid size selection.")
            return redirect('store:product_detail', slug=product.slug)
    else:
        # If product requires size but none was selected
        if product.has_sizes:
            messages.error(request, "Please select a size.")
            return redirect('store:product_detail', slug=product.slug)
        
        # Check product stock if not using sizes
        if quantity > product.stock:
            messages.warning(request, f"Only {product.stock} units available. Quantity adjusted.")
            quantity = product.stock
    
    # Check if product with same size is already in cart
    cart_item = None
    try:
        if selected_size:
            cart_item = CartItem.objects.get(cart=cart, product=product, size=selected_size)
        else:
            cart_item = CartItem.objects.get(cart=cart, product=product, size=None)
    except CartItem.DoesNotExist:
        # Item not in cart, create new one
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            size=selected_size,
            quantity=quantity
        )
    else:
        # Item exists, update quantity
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f"{product.name} has been added to your cart.")
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': cart.total_items
        })
    
    # For normal form submissions, redirect to cart
    return redirect('store:cart')

@login_required
@require_POST
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    data = json.loads(request.body)
    quantity = int(data.get('quantity', 1))
    
    if quantity > 0:
        # Check if we're using a size
        if cart_item.size:
            # Check against size stock
            if quantity <= cart_item.size.stock:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Only {cart_item.size.stock} units available in this size.'
                })
        else:
            # Check against product stock
            if quantity <= cart_item.product.stock:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Only {cart_item.product.stock} units available.'
                })
        
        # Recalculate cart totals
        cart = cart_item.cart
        cart_items = CartItem.objects.filter(cart=cart)
        subtotal = sum(item.total_price for item in cart_items)
        shipping_cost = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
        tax_rate = Decimal('0.10')  # 10% tax rate
        tax_amount = subtotal * tax_rate
        total = subtotal + shipping_cost + tax_amount
        
        # Return updated values
        return JsonResponse({
            'success': True,
            'item_total': str(cart_item.total_price),
            'subtotal': str(subtotal),
            'shipping_cost': str(shipping_cost),
            'tax_amount': str(tax_amount),
            'total': str(total),
            'free_shipping_eligible': subtotal >= 50,
            'amount_needed_for_free_shipping': str(max(0, 50 - subtotal)),
            'cart_count': cart.total_items
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid quantity'})

@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('store:cart')

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    if not cart_items.exists():
        return redirect('store:cart')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping_cost = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
    tax_rate = Decimal('0.10')  # 10% tax rate
    tax_amount = subtotal * tax_rate
    total = subtotal + shipping_cost + tax_amount
    
    # Initialize Stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'cart_total': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total_amount': total,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    })

@login_required
@require_POST
def process_payment(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('store:cart')
    
    # Check stock availability before proceeding
    for item in cart_items:
        if item.size:
            if item.quantity > item.size.stock:
                messages.error(request, f"Sorry, only {item.size.stock} units of {item.product.name} in size {item.size.get_size_display()} are available.")
                return redirect('store:cart')
        else:
            if item.quantity > item.product.stock:
                messages.error(request, f"Sorry, only {item.product.stock} units of {item.product.name} are available.")
                return redirect('store:cart')
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        shipping_data = data.get('shipping')
        payment_method = data.get('payment_method', 'card')
        
        # Calculate totals
        subtotal = sum(item.total_price for item in cart_items)
        shipping_cost = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
        tax_rate = Decimal('0.10')
        tax_amount = subtotal * tax_rate
        total = subtotal + shipping_cost + tax_amount
        
        # Process payment based on selected method
        if payment_method == 'card':
            # Create Stripe charge
            charge = stripe.Charge.create(
                amount=int(total * 100),  # Convert to cents
                currency='usd',
                source=token,
                description=f'Order for {request.user.email}'
            )
            payment_status = 'paid'
        else:
            # Cash on delivery - no payment processing needed
            payment_status = 'pending'
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            email=shipping_data['email'],
            total_amount=total,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            status='pending',
            payment_method=payment_method,
            payment_status=payment_status
        )
        
        # Create shipping address
        shipping_address = ShippingAddress.objects.create(
            first_name=shipping_data['first_name'],
            last_name=shipping_data['last_name'],
            email=shipping_data['email'],
            address=shipping_data['address'],
            city=shipping_data['city'],
            state=shipping_data['state'],
            zip_code=shipping_data['zip_code'],
            phone=shipping_data['phone']
        )
        
        # Associate shipping address with order
        order.shipping_address = shipping_address
        order.save()
        
        # Create order items
        for item in cart_items:
            # Determine the price based on size
            if item.size:
                price = item.product.price + item.size.price_adjustment
                size_name = item.size.get_size_display()
                
                # Reduce the size-specific stock
                item.size.stock -= item.quantity
                item.size.save()
            else:
                price = item.product.price
                size_name = None
                
                # Reduce the product stock
                item.product.stock -= item.quantity
                item.product.save()
            
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=price,
                quantity=item.quantity,
                size=size_name
            )
        
        # Empty cart after order is placed
        cart_items.delete()
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('store:order_confirmation', args=[order.id])
        })
        
    except stripe.error.CardError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred'})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})

def product_search(request):
    query = request.GET.get('q')
    products = []
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).order_by('name')  # Default sorting by name A-Z
        
        # Sorting
        sort_by = request.GET.get('sort')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'name':
            products = products.order_by('name')
    
    context = {
        'query': query,
        'products': products,
        'sort_by': sort_by if 'sort_by' in locals() else None
    }
    return render(request, 'store/search_results.html', context)

def threed_prints(request):
    """
    View for the 3D Prints page
    """
    # Query products with 3D print tag or specific 3D print category
    # For this example, we're filtering products with "3D Print" in the name or description
    # In a real app, you might want to create a specific tag or category for 3D prints
    products = Product.objects.filter(
        Q(name__icontains="3D Print") | 
        Q(description__icontains="3D Print")
    ).order_by('name')  # Default sorting by name A-Z
    
    # If this is a POST request for adding to cart, process it
    if request.method == 'POST' and 'product_id' in request.POST:
        product_id = request.POST.get('product_id')
        return add_to_cart(request, product_id)
    
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    return render(request, 'store/3d_prints.html', {
        'products': products,
        'title': '3D Prints',
        'sort_by': sort_by
    })
