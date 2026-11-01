from django.utils.deprecation import MiddlewareMixin
from store.cart_cookie import clear_cart_cookie, CART_COOKIE_NAME


class GuestCartMergeMiddleware(MiddlewareMixin):
    """
    After a guest user logs in and their cookie cart is merged into
    their database cart, this middleware clears the guest cart cookie
    from the response.
    """

    def process_response(self, request, response):
        if getattr(request, "_guest_cart_merged", False):
            response = clear_cart_cookie(response)
        return response