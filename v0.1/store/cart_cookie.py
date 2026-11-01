"""
Cookie-based shopping cart for guest (non-logged-in) users.

Cart data is stored as JSON in a cookie named ``clevercupid_cart``.
Cookies are sent to the server with every request, so Django can read
and write them entirely server-side — no JavaScript required.

Cookie format::

    {
        "items": [
            {"product_id": 1, "quantity": 2, "size_id": null},
            {"product_id": 3, "quantity": 1, "size_id": 5}
        ]
    }
"""

import json
from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Product, ProductSize

CART_COOKIE_NAME = "clevercupid_cart"
CART_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_cart_from_cookie(request):
    """Parse the cart cookie and return a list of item dicts."""
    raw = request.COOKIES.get(CART_COOKIE_NAME)
    if not raw:
        return {"items": []}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or "items" not in data:
            return {"items": []}
        return data
    except (json.JSONDecodeError, ValueError):
        return {"items": []}


def save_cart_to_cookie(response, cart_data):
    """Write cart data to a cookie on the response."""
    response.set_cookie(
        CART_COOKIE_NAME,
        json.dumps(cart_data, separators=(",", ":")),
        max_age=CART_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
    )
    return response


def clear_cart_cookie(response):
    """Remove the cart cookie from the response."""
    response.delete_cookie(CART_COOKIE_NAME)
    return response


def get_cart_count_from_cookie(request):
    """Return total quantity of items in the cookie cart."""
    cart = get_cart_from_cookie(request)
    return sum(item.get("quantity", 0) for item in cart.get("items", []))


def get_cart_items_from_cookie(request):
    """
    Resolve cookie cart items into full product objects.

    Returns a list of dicts with the same shape as database CartItem
    properties so templates can render them uniformly::

        {
            "product": Product,
            "quantity": int,
            "size": ProductSize or None,
            "total_price": Decimal,
            "item_key": str,   # unique key for update/remove
        }
    """
    cart = get_cart_from_cookie(request)
    items = []

    for entry in cart.get("items", []):
        product_id = entry.get("product_id")
        quantity = int(entry.get("quantity", 1))
        size_id = entry.get("size_id")

        product = get_object_or_404(Product, id=product_id)
        size = None
        if size_id:
            try:
                size = ProductSize.objects.get(id=size_id, product=product)
            except ProductSize.DoesNotExist:
                size = None

        # Use size-adjusted price if a size is selected
        if size:
            unit_price = size.get_final_price()
        else:
            unit_price = product.price

        items.append(
            {
                "product": product,
                "quantity": quantity,
                "size": size,
                "total_price": unit_price * quantity,
                "item_key": f"{product_id}_{size_id or 'none'}",
            }
        )

    return items


def add_item_to_cookie_cart(cart_data, product_id, quantity, size_id=None):
    """Add or update an item in the cookie cart data dict."""
    items = cart_data.setdefault("items", [])
    item_key = f"{product_id}_{size_id or 'none'}"

    for entry in items:
        if entry.get("product_id") == product_id and entry.get("size_id") == size_id:
            entry["quantity"] = int(entry.get("quantity", 0)) + int(quantity)
            return cart_data

    items.append(
        {
            "product_id": int(product_id),
            "quantity": int(quantity),
            "size_id": int(size_id) if size_id else None,
        }
    )
    return cart_data


def update_item_in_cookie_cart(cart_data, item_key, quantity):
    """Update the quantity of an existing cookie cart item."""
    parts = item_key.split("_")
    product_id = int(parts[0])
    size_id = int(parts[1]) if len(parts) > 1 and parts[1] != "none" else None

    for entry in cart_data.get("items", []):
        if entry.get("product_id") == product_id and entry.get("size_id") == size_id:
            entry["quantity"] = int(quantity)
            return cart_data
    return cart_data


def remove_item_from_cookie_cart(cart_data, item_key):
    """Remove an item from the cookie cart data dict."""
    parts = item_key.split("_")
    product_id = int(parts[0])
    size_id = int(parts[1]) if len(parts) > 1 and parts[1] != "none" else None

    cart_data["items"] = [
        entry
        for entry in cart_data.get("items", [])
        if not (entry.get("product_id") == product_id and entry.get("size_id") == size_id)
    ]
    return cart_data


def cart_subtotal_from_cookie(request):
    """Calculate subtotal from cookie cart items."""
    subtotal = Decimal("0.00")
    for item in get_cart_items_from_cookie(request):
        subtotal += item["total_price"]
    return subtotal