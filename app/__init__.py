from flask import Flask, render_template, request, redirect, url_for, session, flash, g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel, _
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from app.config import Config
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import or_

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    login_manager.login_view = 'auth.login'

    # Configure supported languages
    app.config['LANGUAGES'] = {
        'en': 'English',
        'hi': 'हिंदी',
        'gu': 'ગુજરાતી'
    }

    # Configure Babel
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(app.root_path, 'translations')

    # Register blueprints
    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.chat_routes import chat as chat_blueprint
    app.register_blueprint(chat_blueprint)
    
    from app.rating_routes import rating as rating_blueprint
    app.register_blueprint(rating_blueprint)

    # Import models here to avoid circular imports
    from app.models import User, Product, CartItem, Purchase, ChatMessage, Rating

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
            
            # Create demo user if it doesn't exist
            if not User.query.filter_by(email='demo@ecofinds.com').first():
                try:
                    user = User(
                        email='demo@ecofinds.com',
                        username='John Smith',
                        phone_number='+1234567890',
                        is_email_verified=True,
                        is_phone_verified=True,
                        eco_points=150,
                        profile_img='default_profile.png'
                    )
                    user.set_password('demo123')
                    db.session.add(user)
                    db.session.commit()
                    app.logger.info("Demo user created successfully")
                except Exception as e:
                    app.logger.error(f"Error creating demo user: {str(e)}")
                    db.session.rollback()

            # Create admin user if it doesn't exist
            if not User.query.filter_by(email='admin@ecofinds.com').first():
                try:
                    admin_user = User(
                        email='admin@ecofinds.com',
                        username='Admin',
                        phone_number='+10000000000',
                        is_email_verified=True,
                        is_phone_verified=True,
                        is_admin=True
                    )
                    admin_user.set_password('admin@ecofinds')
                    db.session.add(admin_user)
                    db.session.commit()
                    app.logger.info("Admin user created successfully")
                except Exception as e:
                    app.logger.error(f"Error creating admin user: {str(e)}")
                    db.session.rollback()

            # Add default products if none exist
            if Product.query.count() == 0:
                try:
                    demo_products = [
                        Product(title='Eco Water Bottle', description='Reusable water bottle made from recycled materials.', price=129.99, category='Eco-Friendly', image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRZ1rOtZUOy4m3hbbgp27D_IKXBkaO2_mwXQ&s', owner_id=1),
                        Product(title='Bamboo Toothbrush', description='Biodegradable toothbrush with bamboo handle.', price=39.49, category='Eco-Friendly', image_url='https://m.media-amazon.com/images/I/71edeKpYPpL.jpg', owner_id=1),
                        Product(title='Recycled Notebook', description='Notebook made from 100% recycled paper.', price=59.99, category='Recycled', image_url='https://images2.habeco.si/Upload/Product/sonora-plus---recycled-paper-notebook-pen_8494_productmain.webp', owner_id=1),
                        Product(title='Water Saver Showerhead', description='Showerhead that reduces water usage by 40%.', price=1999.99, category='Water Saving', image_url='https://m.media-amazon.com/images/I/81eF1mDe5gL.jpg', owner_id=1),
                        Product(title='Eco Finds Wooden Water Bottle(750ml)', description='Made from recycled materials, this durable bottle features the Eco Finds logo perfect for sustainable hydration on the go.', price=599, category='Eco-Finds', image_url='https://pplx-res.cloudinary.com/image/upload/v1749017272/gpt4o_images/kfvxpybk0ldixn89rhug.png', owner_id=1),
                        Product(title='T-shirt Eco Finds', description='Show your commitment to sustainability with this comfortable T-shirt, made from recycled and eco-friendly materials and featuring the Eco Finds logo. Perfect for everyday wear while making a positive impact on the planet.', price=299, category='Eco-Finds',image_url='https://pplx-res.cloudinary.com/image/upload/v1749017789/gpt4o_images/bsz1nd5eddn0f7fzfth0.png' , owner_id=1),
                        Product(title='Key Chain Eco Finds', description='Carry your commitment to sustainability everywhere! This landscape keychain features the Eco Finds logo and is crafted from eco-friendly materials—perfect for your keys or bag.', price=99, category='Eco-Finds', image_url='https://pplx-res.cloudinary.com/image/upload/v1749017410/gpt4o_images/niqwd5dplgm4iwwylupe.png' , owner_id=1),
                        Product(title='Eco Finds Black T-shirt', description='Make a statement for sustainability with this black Eco Finds T-shirt. Crafted from recycled and organic materials, it features the Eco Finds logo for a stylish, eco-friendly look you can wear anywhere', price=299, category='Eco-Finds',image_url='https://pplx-res.cloudinary.com/image/upload/v1749024630/gpt4o_images/rbnmez9sdd91glbo0f6i.png' , owner_id=1),
                        Product(title='Eco Finds Wooden Toothbrush', description="Make the switch to sustainability with our Eco Finds wooden toothbrush. Crafted from biodegradable bamboo with BPA-free, soft bristles, it's an eco-friendly choice for a cleaner mouth and a cleaner planet", price=89, category='Eco-Finds', image_url='https://i.postimg.cc/nLBgbmMj/Tooth.png', owner_id=1),
                        Product(title='Eco Finds Hoodie', description='Show your commitment to sustainability with this comfortable T-shirt, made from recycled and eco-friendly materials and featuring the Eco Finds logo. Perfect for everyday wear while making a positive impact on the planet.', price=699, category='Eco-Finds',image_url='https://pplx-res.cloudinary.com/image/upload/v1749017981/gpt4o_images/s3rtl7i6hqrqxorx4zlc.png' , owner_id=1),
                    ]
                    for product in demo_products:
                        db.session.add(product)
                    db.session.commit()
                    app.logger.info("Demo products created successfully")
                except Exception as e:
                    app.logger.error(f"Error creating demo products: {str(e)}")
                    db.session.rollback()
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")

    # Register routes
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
                if user.is_admin:
                    return redirect(url_for('admin_landing'))
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
        user = current_user
        return render_template('dashboard.html', user=user)

    @app.route('/products')
    def products():
        search_query = request.args.get('search', '')
        city_query = request.args.get('city', '')
        state_query = request.args.get('state', '')
        
        query = Product.query
        
        if search_query:
            query = query.filter(
                or_(
                    Product.title.ilike(f'%{search_query}%'),
                    Product.description.ilike(f'%{search_query}%')
                )
            )
        
        if city_query:
            query = query.filter(Product.city.ilike(f'%{city_query}%'))
        
        if state_query:
            query = query.filter(Product.state.ilike(f'%{state_query}%'))
        
        products = query.order_by(Product.created_at.desc()).all()
        return render_template('products.html', products=products)

    @app.route('/products/<int:product_id>')
    def product_detail(product_id):
        try:
            product = Product.query.get_or_404(product_id)
            return render_template('product_detail.html', product=product)
        except Exception as e:
            current_app.logger.error(f'Error in product_detail route: {str(e)}')
            flash('An error occurred while loading the product. Please try again.', 'danger')
            return redirect(url_for('product_list'))

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
        categories = ['Eco-Finds', 'Eco-Friendly', 'Recycled', 'Water Saving']
        return render_template('new_product.html', categories=categories)

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
        categories = ['Eco-Finds', 'Eco-Friendly', 'Recycled', 'Water Saving']
        return render_template('edit_product.html', product=product, categories=categories)

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        return render_template('cart.html', cart_items=cart_items)

    @app.route('/add_to_cart/<int:product_id>', methods=['POST'])
    @login_required
    def add_to_cart(product_id):
        try:
            product = Product.query.get_or_404(product_id)
            cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            
            if cart_item:
                cart_item.quantity += 1
            else:
                cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
                db.session.add(cart_item)
            
            db.session.commit()
            flash('Product added to cart!', 'success')
            return redirect(url_for('product_list'))
        except Exception as e:
            current_app.logger.error(f'Error in add_to_cart: {str(e)}')
            db.session.rollback()
            flash('An error occurred while adding the product to cart', 'danger')
            return redirect(url_for('product_list'))

    @app.route('/purchases')
    @login_required
    def purchases():
        purchases = Purchase.query.filter_by(user_id=current_user.id).all()
        return render_template('purchases.html', purchases=purchases)

    @app.route('/admin-landing')
    @login_required
    def admin_landing():
        if not current_user.is_admin:
            return redirect(url_for('dashboard'))
        return render_template('admin_landing.html')

    @babel.localeselector
    def get_locale():
        # Try to get the language from the session
        if 'lang' in session:
            return session['lang']
        # Try to get the language from the user's browser
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

    @app.route('/set_language/<lang_code>')
    def set_language(lang_code):
        if lang_code not in app.config['LANGUAGES']:
            lang_code = 'en'
        session['lang'] = lang_code
        g.lang_code = lang_code
        return redirect(request.referrer or url_for('home'))

    return app