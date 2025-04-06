from .models import Category, Cart, CartItem
from django.db.models import Sum

def store_context(request):
    """
    Context processor to add categories and cart information to all templates
    """
    # Get all parent categories
    parent_categories = Category.objects.filter(parent=None)
    
    # Create a dictionary to store parent categories and their subcategories
    categories_with_children = {}
    for parent in parent_categories:
        subcategories = parent.get_subcategories()
        categories_with_children[parent] = subcategories
    
    # Get cart count for authenticated users
    cart_count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Get the sum of all item quantities instead of just counting items
        cart_items = CartItem.objects.filter(cart=cart)
        if cart_items.exists():
            total_quantity = cart_items.aggregate(total=Sum('quantity'))
            cart_count = total_quantity['total'] or 0
    
    return {
        'all_categories': Category.objects.all(),
        'parent_categories': parent_categories,
        'categories_with_children': categories_with_children,
        'cart_count': cart_count
    } 