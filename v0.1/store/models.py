from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category_detail', args=[self.slug])

    @property
    def is_subcategory(self):
        return self.parent is not None

    def get_subcategories(self):
        return self.children.all()

    def get_root_categories(self):
        return Category.objects.filter(parent=None)

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, 
                                help_text="Select either a main category or a subcategory")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=255, blank=True, help_text="Brief description for product listings (max 255 characters)")
    description = models.TextField(blank=True, help_text="Detailed product description shown on product detail page")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])
    
    @property
    def image(self):
        """Return the primary image (first in order) or a placeholder if no images exist"""
        first_image = self.images.first()
        if first_image:
            return first_image.image
        return None  # Return None when no image is available
    
    @property
    def image_url(self):
        """Return URL of primary image or placeholder URL if no images exist"""
        first_image = self.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return '/static/img/placeholder.png'  # Return a placeholder image path

    @property
    def is_in_stock(self):
        return self.stock > 0 or self.sizes.filter(stock__gt=0).exists()

    @property
    def get_category_display(self):
        """Return category display name with parent if it's a subcategory"""
        if self.category.is_subcategory:
            return f"{self.category.parent.name} › {self.category.name}"
        return self.category.name
        
    @property
    def has_sizes(self):
        """Check if the product has size options"""
        return self.sizes.exists()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    order = models.PositiveIntegerField(default=0, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f'Image for {self.product.name}'

class ProductSize(models.Model):
    """Model for product size options"""
    SIZE_CHOICES = [
        ('xs', 'Extra Small'),
        ('s', 'Small'),
        ('m', 'Medium'),
        ('l', 'Large'),
        ('xl', 'Extra Large'),
        ('xxl', '2XL'),
        ('3xl', '3XL'),
        ('4xl', '4XL'),
        ('5xl', '5XL'),
        ('one-size', 'One Size'),
        # 3D Print specific sizes
        ('small', 'Small (10cm)'),
        ('medium', 'Medium (15cm)'),
        ('large', 'Large (20cm)'),
        ('custom', 'Custom Size'),
    ]
    
    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price adjustment for this size (can be positive or negative)")
    stock = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    
    class Meta:
        unique_together = ('product', 'size')
        verbose_name = 'Product Size'
        verbose_name_plural = 'Product Sizes'
        
    def __str__(self):
        adjustment = ""
        if self.price_adjustment > 0:
            adjustment = f" (+${self.price_adjustment})"
        elif self.price_adjustment < 0:
            adjustment = f" (-${abs(self.price_adjustment)})"
        return f"{self.get_size_display()}{adjustment}"
    
    def get_final_price(self):
        """Calculate the final price including the adjustment"""
        return self.product.price + self.price_adjustment
        
    @property
    def is_in_stock(self):
        return self.stock > 0

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart for {self.user.username}'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        size_str = f" - {self.size.get_size_display()}" if self.size else ""
        return f'{self.quantity} x {self.product.name}{size_str}'

    @property
    def total_price(self):
        if self.size and self.size.price_adjustment:
            # Use size-specific price if available
            return (self.product.price + self.size.price_adjustment) * self.quantity
        return self.product.price * self.quantity

class ShippingAddress(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash on Delivery')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True, default='')
    email = models.EmailField()
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.order_number}'

    @property
    def status_color(self):
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'shipped': 'primary',
            'delivered': 'success',
            'cancelled': 'danger'
        }
        return colors.get(self.status, 'secondary')

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number based on timestamp
            from datetime import datetime
            self.order_number = datetime.now().strftime('%Y%m%d%H%M%S')
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        size_str = f" - {self.size}" if self.size else ""
        return f'{self.quantity} x {self.product.name}{size_str}'

    @property
    def total_price(self):
        return self.price * self.quantity
