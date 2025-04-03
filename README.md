# CleverCupid E-commerce

A modern e-commerce website built with Django.

## Features (Planned)
- User authentication and authorization
- Product catalog with categories
- Shopping cart functionality
- Secure checkout process
- Order management
- User profiles
- Product reviews and ratings
- Search functionality

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Visit http://127.0.0.1:8000/ in your browser

## Project Structure
- `clevercupid/` - Main project directory
- `store/` - Main application for e-commerce functionality
- `accounts/` - User authentication and profile management
- `static/` - Static files (CSS, JavaScript, images)
- `templates/` - HTML templates
- `media/` - User-uploaded files 