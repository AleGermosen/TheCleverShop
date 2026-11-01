from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from store.models import Cart, CartItem
from store.cart_cookie import (
    get_cart_from_cookie,
    get_cart_items_from_cookie,
    clear_cart_cookie,
    CART_COOKIE_NAME,
)


@receiver(user_logged_in)
def merge_guest_cart_on_login(sender, request, user, **kwargs):
    """
    When a guest user logs in, merge their cookie-based cart
    into their database-backed cart.
    """
    # Check if there's a guest cart cookie
    cart_cookie_name = CART_COOKIE_NAME
    if cart_cookie_name not in request.COOKIES:
        return

    guest_cart = get_cart_from_cookie(request)
    items = guest_cart.get("items", [])
    if not items:
        return

    # Get or create the user's database cart
    cart_obj, _ = Cart.objects.get_or_create(user=user)

    # Merge each guest cart item into the database cart
    for entry in items:
        product_id = entry.get("product_id")
        quantity = int(entry.get("quantity", 1))
        size_id = entry.get("size_id")

        try:
            product = CartItem.model.product.field.related_model.objects.get(id=product_id)
        except Exception:
            continue

        selected_size = None
        if size_id:
            from store.models import ProductSize
            try:
                selected_size = ProductSize.objects.get(id=size_id, product=product)
            except ProductSize.DoesNotExist:
                selected_size = None

        # Check if item already exists in user's cart
        try:
            if selected_size:
                cart_item = CartItem.objects.get(cart=cart_obj, product=product, size=selected_size)
            else:
                cart_item = CartItem.objects.get(cart=cart_obj, product=product, size=None)
            # Add quantities
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # Create new cart item
            CartItem.objects.create(
                cart=cart_obj,
                product=product,
                size=selected_size,
                quantity=quantity,
            )

    # Clear the guest cart cookie after successful merge
    # We set a flag on the request so middleware can clear it in the response
    request._guest_cart_merged = True