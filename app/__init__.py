from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy

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
            if user and user.password_hash == password:
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'danger')
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            username = request.form['username']
            user = User(email=email, password_hash=password, username=username)
            db.session.add(user)
            db.session.commit()
            flash('Signup successful! Please log in.', 'success')
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
            user.username = request.form['username']
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
        cart_item = CartItem(user_id=user.id, product_id=product_id)
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
        purchase = Purchase(user_id=user.id, product_id=cart_item.product_id)
        db.session.add(purchase)
        db.session.delete(cart_item)
        db.session.commit()
        flash('Purchase successful!', 'success')
        return redirect(url_for('purchases'))

    return app

app = create_app()

with app.app_context():
    from app.models import User, Product, Purchase, CartItem
    db.create_all()