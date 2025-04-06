import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clevercupid.settings')
django.setup()

from store.models import Product, ProductSize
from django.db.models import Q

def create_sample_sizes():
    """
    Create sample size options for 3D printed products
    """
    # Get products that might be 3D prints (based on name or category)
    products = Product.objects.filter(
        Q(name__icontains='3d') | 
        Q(name__icontains='print') | 
        Q(category__name__icontains='3d') |
        Q(category__name__icontains='print')
    )
    
    if not products.exists():
        print("No 3D print products found. Adding sizes to first 3 products instead.")
        products = Product.objects.all()[:3]
    
    sizes_created = 0
    
    for product in products:
        print(f"Adding sizes to product: {product.name}")
        
        # Create size options with different prices based on size
        sizes = [
            {'size': 'small', 'price_adjustment': Decimal('-5.00'), 'stock': 10, 'weight': Decimal('0.2')},
            {'size': 'medium', 'price_adjustment': Decimal('0.00'), 'stock': 15, 'weight': Decimal('0.5')},
            {'size': 'large', 'price_adjustment': Decimal('10.00'), 'stock': 5, 'weight': Decimal('1.0')},
            {'size': 'custom', 'price_adjustment': Decimal('20.00'), 'stock': 3, 'weight': Decimal('1.5')},
        ]
        
        for size_data in sizes:
            # Skip if this size already exists for this product
            if ProductSize.objects.filter(product=product, size=size_data['size']).exists():
                print(f"  - Size {size_data['size']} already exists for this product")
                continue
                
            # Create the size
            ProductSize.objects.create(
                product=product,
                size=size_data['size'],
                price_adjustment=size_data['price_adjustment'],
                stock=size_data['stock'],
                weight=size_data['weight']
            )
            sizes_created += 1
            print(f"  - Added {size_data['size']} size (${product.price + size_data['price_adjustment']})")
    
    print(f"Created {sizes_created} new product sizes for {len(products)} products")

if __name__ == '__main__':
    create_sample_sizes() 