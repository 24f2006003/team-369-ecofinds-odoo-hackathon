from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from app.models import User, Product, Purchase, CartItem

    CATEGORIES = [
        'Eco-Friendly',
        'Recycled',
        'Water Saving',
    ]

    def current_user():
        if 'user_id' in session:
            return User.query.get(session['user_id'])
        return None

    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        g.user = User.query.get(user_id) if user_id else None

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
            
            if user.password_hash == password:
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
                return redirect(url_for('login'))
            
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            username = request.form['username']
            
            # Check if user already exists
            existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
            if existing_user:
                if existing_user.email == email:
                    flash('An account with this email already exists. Please login instead.', 'warning')
                else:
                    flash('This username is already taken. Please choose another one.', 'warning')
                return redirect(url_for('signup'))
            
            # Create new user
            user = User(email=email, password_hash=password, username=username)
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please login to continue.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form.get('password')
            user.username = username
            user.email = email
            if password:
                user.password_hash = password
            # Handle profile image upload
            if 'profile_img' in request.files:
                file = request.files['profile_img']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    img_path = os.path.join(app.static_folder, 'img', filename)
                    file.save(img_path)
                    user.profile_img = filename
            db.session.commit()
            flash('Profile updated!', 'success')
        return render_template('dashboard.html', user=user)

    @app.route('/products', methods=['GET'])
    def product_list():
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        query = Product.query
        if search:
            query = query.filter(Product.title.ilike(f'%{search}%'))
        if category:
            query = query.filter_by(category=category)
        products = query.all()
        return render_template('product_list.html', products=products, categories=CATEGORIES, selected_category=category, search=search)

    @app.route('/products/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', product=product)

    @app.route('/products/new', methods=['GET', 'POST'])
    def new_product():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            price = request.form['price']
            category = request.form['category']
            image_url = request.form['image_url']
            new_product = Product(title=title, description=description, price=price, category=category, image_url=image_url, owner_id=user.id)
            db.session.add(new_product)
            db.session.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('product_list'))
        return render_template('new_product.html', categories=CATEGORIES)

    @app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
    def edit_product(product_id):
        user = current_user()
        product = Product.query.get_or_404(product_id)
        if not user or product.owner_id != user.id:
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
        return render_template('edit_product.html', product=product, categories=CATEGORIES)

    @app.route('/products/delete/<int:product_id>', methods=['POST'])
    def delete_product(product_id):
        user = current_user()
        product = Product.query.get_or_404(product_id)
        if not user or product.owner_id != user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('product_list'))
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
        return redirect(url_for('product_list'))

    @app.route('/cart')
    def cart():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        return render_template('cart.html', cart_items=cart_items)

    @app.route('/cart/add/<int:product_id>', methods=['POST'])
    def add_to_cart(product_id):
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        cart_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        db.session.commit()
        flash('Added to cart!', 'success')
        return redirect(url_for('cart'))

    @app.route('/cart/remove/<int:cart_item_id>', methods=['POST'])
    def remove_from_cart(cart_item_id):
        user = current_user()
        cart_item = CartItem.query.get_or_404(cart_item_id)
        if not user or cart_item.user_id != user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('cart'))
        db.session.delete(cart_item)
        db.session.commit()
        flash('Removed from cart!', 'success')
        return redirect(url_for('cart'))

    @app.route('/cart/update/<int:cart_item_id>', methods=['POST'])
    def update_cart_quantity(cart_item_id):
        user = current_user()
        cart_item = CartItem.query.get_or_404(cart_item_id)
        if not user or cart_item.user_id != user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('cart'))
        action = request.form.get('action')
        if action == 'increment':
            cart_item.quantity += 1
        elif action == 'decrement':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                db.session.delete(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))

    @app.route('/purchases')
    def purchases():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        purchases = Purchase.query.filter_by(user_id=user.id).all()
        return render_template('purchases.html', purchases=purchases)

    @app.route('/purchase/<int:cart_item_id>', methods=['POST'])
    def purchase(cart_item_id):
        user = current_user()
        cart_item = CartItem.query.get_or_404(cart_item_id)
        if not user or cart_item.user_id != user.id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('cart'))
        purchase = Purchase(user_id=user.id, product_id=cart_item.product_id, purchase_price=cart_item.product.price)
        db.session.add(purchase)
        db.session.delete(cart_item)
        db.session.commit()
        flash('Purchase successful!', 'success')
        return redirect(url_for('purchases'))

    @app.route('/cart/purchase', methods=['POST'])
    def purchase_cart():
        user = current_user()
        if not user:
            return redirect(url_for('login'))
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        if not cart_items:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart'))
        redeem_points = int(request.form.get('redeem_eco_points', 0))
        total_spent = 0
        for item in cart_items:
            for _ in range(item.quantity):
                purchase = Purchase(user_id=user.id, product_id=item.product_id, purchase_price=item.product.price)
                db.session.add(purchase)
                total_spent += item.product.price
            db.session.delete(item)
        # ECO Points: 1 point per Rs. 10 spent
        points_earned = int(total_spent // 10)
        user.eco_points += points_earned
        # Redeem ECO Points
        if redeem_points > 0 and redeem_points <= user.eco_points:
            user.eco_points -= redeem_points
        db.session.commit()
        flash(f'Purchase successful! You earned {points_earned} ECO Points.', 'success')
        return redirect(url_for('purchases'))

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
            user = User(email='demo@ecofinds.com', password_hash='demo', username='DemoUser')
            db.session.add(user)
            db.session.commit()
        for prod in demo_products:
            db.session.add(prod)
        db.session.commit()