# The Clever Shop (CleverCupid)

A full-stack e-commerce site for 3D-printed products, built with Django. Its signature feature is a **Three.js hero section that renders the shop's actual STL print files in the browser**, so visitors can rotate real models on the home page.

> Status: v0.1, an early but working storefront. Features and gaps are listed honestly below.

## Architecture

```
v0.1/
├── clevercupid/   Django project: settings, URLs, ASGI/WSGI
├── store/         catalog, cart, checkout, orders
├── accounts/      registration, login, profile, order history, password reset
├── templates/     server-rendered pages (base, store/, accounts/)
└── static/        css, js, STL models, images
```

Server-rendered Django templates for the pages, with plain JavaScript modules for cart behavior and the 3D scene. There is no SPA framework.

## Data model (`store/models.py`)

- **Category** has a self-referencing `parent` key, so categories can nest.
- **Product** has `Decimal` price and old price (for sale display), stock, featured flag, and an auto-generated slug.
- **ProductImage** is ordered and supports multiple images per product.
- **ProductSize** adds per-size price adjustment, stock, and weight, with a `get_final_price()` method.
- **Cart / CartItem** hold per-user carts, with item totals computed in model properties.
- **ShippingAddress, Order, OrderItem** capture an order snapshot: the item price and size are stored on `OrderItem`, so later catalog changes don't rewrite order history. The product link is `SET_NULL` so deleting a product keeps the order.

## Notable pieces

- **3D hero (`static/js/3d_hero.js`, ~720 lines).** Three.js with `OrbitControls` and `STLLoader`, loading models from `static/models/` with a fallback cube if a file fails to load.
- **Guest cart (`static/js/guest-cart.js`).** Anonymous visitors get a cart in `localStorage`, so they can shop without an account. Logged-in users use the database-backed `Cart`.
- **Checkout (`store/views.py`).** The flow runs cart → shipping address → Stripe payment → order confirmation, with card errors handled explicitly.
- **Auth.** `django-allauth` for accounts, plus custom profile and order-history views and a full password-reset email flow.
- **Tooling scripts.** A `populate_db` management command seeds the catalog, and helper scripts use `numpy-stl` to generate sample STL meshes (cube, pyramid) and placeholder images with Pillow.
- **Admin.** Customized Django admin for products, sizes and images (with drag-sorting via `django-admin-sortable2`).

## Stack

Django 5, SQLite, Stripe, django-allauth, crispy-forms (Bootstrap 5), Pillow, numpy-stl, Three.js.

## Known gaps / next steps

- Payments use Stripe's older `Charge` API; migrating to Checkout Sessions or PaymentIntents is the main next step.
- Test files are empty stubs, and the cart and checkout logic need coverage first.
- The 3D hero has debug logging on and should be tuned for mobile performance.
- Move from SQLite to PostgreSQL and add a deployment config.
