from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
import os
import random
from decimal import Decimal

from store.models import Category, Product, ProductImage

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create products
        self.create_products(categories)
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))

    def create_categories(self):
        categories = []
        category_data = [
            {'name': 'Electronics', 'description': 'Latest gadgets and electronic devices'},
            {'name': 'Clothing', 'description': 'Fashion and apparel for all seasons'},
            {'name': 'Home & Kitchen', 'description': 'Everything for your home'},
            {'name': 'Books', 'description': 'Books across all genres'},
            {'name': 'Sports', 'description': 'Sports equipment and accessories'},
        ]
        
        for data in category_data:
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': slugify(data['name']),
                    'description': data['description']
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        return categories

    def create_products(self, categories):
        # Sample product data
        products_data = [
            {
                'name': 'Smartphone X',
                'description': 'Latest smartphone with advanced features',
                'price': Decimal('699.99'),
                'stock': 50,
                'featured': True,
                'category': categories[0]  # Electronics
            },
            {
                'name': 'Laptop Pro',
                'description': 'Powerful laptop for professionals',
                'price': Decimal('1299.99'),
                'stock': 30,
                'featured': True,
                'category': categories[0]  # Electronics
            },
            {
                'name': 'Wireless Headphones',
                'description': 'Noise-cancelling wireless headphones',
                'price': Decimal('199.99'),
                'stock': 100,
                'featured': False,
                'category': categories[0]  # Electronics
            },
            {
                'name': 'Men\'s Casual T-Shirt',
                'description': 'Comfortable cotton t-shirt',
                'price': Decimal('19.99'),
                'stock': 200,
                'featured': False,
                'category': categories[1]  # Clothing
            },
            {
                'name': 'Women\'s Dress',
                'description': 'Elegant dress for special occasions',
                'price': Decimal('59.99'),
                'stock': 75,
                'featured': True,
                'category': categories[1]  # Clothing
            },
            {
                'name': 'Coffee Maker',
                'description': 'Automatic coffee maker with timer',
                'price': Decimal('49.99'),
                'stock': 40,
                'featured': False,
                'category': categories[2]  # Home & Kitchen
            },
            {
                'name': 'Blender',
                'description': 'High-speed blender for smoothies and more',
                'price': Decimal('79.99'),
                'stock': 60,
                'featured': True,
                'category': categories[2]  # Home & Kitchen
            },
            {
                'name': 'Bestselling Novel',
                'description': 'Latest bestselling novel from a popular author',
                'price': Decimal('14.99'),
                'stock': 150,
                'featured': True,
                'category': categories[3]  # Books
            },
            {
                'name': 'Cooking Book',
                'description': 'Comprehensive guide to cooking',
                'price': Decimal('24.99'),
                'stock': 80,
                'featured': False,
                'category': categories[3]  # Books
            },
            {
                'name': 'Yoga Mat',
                'description': 'Non-slip yoga mat for exercise',
                'price': Decimal('29.99'),
                'stock': 120,
                'featured': False,
                'category': categories[4]  # Sports
            },
            {
                'name': 'Running Shoes',
                'description': 'Comfortable running shoes for all terrains',
                'price': Decimal('89.99'),
                'stock': 90,
                'featured': True,
                'category': categories[4]  # Sports
            },
        ]
        
        for data in products_data:
            product, created = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': slugify(data['name']),
                    'description': data['description'],
                    'price': data['price'],
                    'stock': data['stock'],
                    'featured': data['featured'],
                    'category': data['category']
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name}')
                
                # Create a placeholder image for the product
                # In a real application, you would use actual image files
                # For now, we'll just create the product without an image 