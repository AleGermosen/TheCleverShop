from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('search/', views.product_search, name='search'),
    
    # Cart URLs
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_payment, name='process_payment'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.orders, name='orders'),
] 