from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q
from decimal import Decimal
import stripe

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .forms import ShippingAddressForm

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(featured=True)[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured_products
    })

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
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
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category_detail.html', {
        'category': category,
        'products': products
    })

@login_required
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
    
    # Check if product is already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Product added to cart',
        'cart_count': CartItem.objects.filter(cart=cart).count()
    })

@login_required
@require_POST
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    data = json.loads(request.body)
    quantity = int(data.get('quantity', 1))
    
    if quantity > 0 and quantity <= cart_item.product.stock:
        cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'success': True})
    
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
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    if not cart_items.exists():
        return JsonResponse({'success': False, 'error': 'Cart is empty'})
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        shipping_data = data.get('shipping')
        
        # Calculate totals
        subtotal = sum(item.total_price for item in cart_items)
        shipping_cost = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
        tax_rate = Decimal('0.10')
        tax_amount = subtotal * tax_rate
        total = subtotal + shipping_cost + tax_amount
        
        # Create Stripe charge
        charge = stripe.Charge.create(
            amount=int(total * 100),  # Convert to cents
            currency='usd',
            source=token,
            description=f'Order for {request.user.email}'
        )
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            email=shipping_data['email'],
            total_amount=total,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            status='pending'
        )
        
        # Create shipping address
        order.shipping_address.create(
            first_name=shipping_data['first_name'],
            last_name=shipping_data['last_name'],
            address=shipping_data['address'],
            city=shipping_data['city'],
            state=shipping_data['state'],
            zip_code=shipping_data['zip_code'],
            phone=shipping_data['phone']
        )
        
        # Create order items and clear cart
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            # Update product stock
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()
        
        cart_items.delete()
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('order_confirmation', args=[order.id])
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
        ).filter(available=True)
    
    context = {
        'query': query,
        'products': products,
    }
    return render(request, 'store/search_results.html', context)
