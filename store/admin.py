from django.contrib import admin
from django.utils.safestring import mark_safe
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminMixin, SortableAdminBase
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, ShippingAddress

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'created_at', 'updated_at']
    list_filter = ['parent', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['parent']

class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'order', 'get_image_preview']
    readonly_fields = ['get_image_preview']
    
    def get_image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: contain;" />')
        return "No Image"
    get_image_preview.short_description = 'Preview'

@admin.register(ProductImage)
class ProductImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['get_product_name', 'get_image_preview', 'order']
    list_filter = ['product']
    search_fields = ['product__name']
    
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product'
    
    def get_image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: contain;" />')
        return "No Image"
    get_image_preview.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ['name', 'display_category', 'display_primary_image', 'price', 'stock', 'featured', 'created_at']
    list_filter = ['category__parent', 'category', 'featured', 'created_at']
    list_editable = ['price', 'stock', 'featured']
    search_fields = ['name', 'short_description', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'price', 'old_price', 'stock', 'featured')
        }),
        ('Descriptions', {
            'fields': ('short_description', 'description'),
            'description': 'Enter both a short summary for product listings and a detailed description for the product page.'
        }),
    )
    
    def display_category(self, obj):
        if obj.category.is_subcategory:
            return f"{obj.category.parent.name} › {obj.category.name}"
        return obj.category.name
    display_category.short_description = 'Category'
    
    def display_primary_image(self, obj):
        if obj.image_url:
            return mark_safe(f'<img src="{obj.image_url}" width="50" height="50" style="object-fit: contain;" />')
        return "No Image"
    display_primary_image.short_description = 'Primary Image'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['cart__user__username', 'product__name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    readonly_fields = ['order_number']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name']

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'city', 'state', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'address', 'city']
