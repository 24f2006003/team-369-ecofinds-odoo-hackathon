from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
from app.config import Config
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User, Product, Purchase, CartItem
    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Create database tables
    with app.app_context():
        db.create_all()
        # Create demo user if it doesn't exist
        if not User.query.filter_by(email='demo@ecofinds.com').first():
            user = User(
                email='demo@ecofinds.com',
                username='DemoUser',
                phone_number='+1234567890',
                is_email_verified=True,
                is_phone_verified=True
            )
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            
            if not user:
                flash('No account found with this email. Please sign up first.', 'warning')
                return redirect(url_for('signup'))
            
            if user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
                return redirect(url_for('login'))
            
        return render_template('auth/login.html')

    @app.route('/signup')
    def signup():
        return render_template('auth/register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/products')
    def product_list():
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        query = Product.query
        if search:
            query = query.filter(Product.title.ilike(f'%{search}%'))
        if category:
            query = query.filter_by(category=category)
        products = query.all()
        return render_template('product_list.html', products=products)

    @app.route('/products/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', product=product)

    @app.route('/products/new', methods=['GET', 'POST'])
    @login_required
    def new_product():
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            price = request.form['price']
            category = request.form['category']
            image_url = request.form['image_url']
            new_product = Product(title=title, description=description, price=price, category=category, image_url=image_url, owner_id=current_user.id)
            db.session.add(new_product)
            db.session.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('product_list'))
        return render_template('new_product.html')

    @app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
    @login_required
    def edit_product(product_id):
        product = Product.query.get_or_404(product_id)
        if product.owner_id != current_user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('product_list'))
        if request.method == 'POST':
            product.title = request.form['title']
            product.description = request.form['description']
            product.price = request.form['price']
            product.category = request.form['category']
            product.image_url = request.form['image_url']
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('product_list'))
        return render_template('edit_product.html', product=product)

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        return render_template('cart.html', cart_items=cart_items)

    @app.route('/purchases')
    @login_required
    def purchases():
        purchases = Purchase.query.filter_by(user_id=current_user.id).all()
        return render_template('purchases.html', purchases=purchases)

    return app

app = create_app()

with app.app_context():
    from app.models import User, Product, Purchase, CartItem
    db.create_all()
    # Insert dummy products if table is empty
    if Product.query.count() == 0:
        demo_products = [
            Product(title='Eco Water Bottle', description='Reusable water bottle made from recycled materials.', price=129.99, category='Eco-Friendly', image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRZ1rOtZUOy4m3hbbgp27D_IKXBkaO2_mwXQ&s', owner_id=1),
            Product(title='Bamboo Toothbrush', description='Biodegradable toothbrush with bamboo handle.', price=39.49, category='Eco-Friendly', image_url='https://m.media-amazon.com/images/I/71edeKpYPpL.jpg', owner_id=1),
            Product(title='Recycled Notebook', description='Notebook made from 100% recycled paper.', price=59.99, category='Recycled', image_url='https://images2.habeco.si/Upload/Product/sonora-plus---recycled-paper-notebook-pen_8494_productmain.webp', owner_id=1),
            Product(title='Water Saver Showerhead', description='Showerhead that reduces water usage by 40%.', price=1999.99, category='Water Saving', image_url='https://m.media-amazon.com/images/I/81eF1mDe5gL.jpg', owner_id=1),
        ]
        # Ensure at least one user exists for owner_id=1
        if not User.query.get(1):
            user = User(
                email='demo@ecofinds.com',
                username='DemoUser',
                phone_number='+1234567890',
                is_email_verified=True,
                is_phone_verified=True
            )
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()
        for prod in demo_products:
            db.session.add(prod)
        db.session.commit()