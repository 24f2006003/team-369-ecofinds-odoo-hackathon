import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Product, Complaint, ProductRating, CartItem, Purchase
from app.forms import ComplaintForm
from datetime import datetime
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.route('/')
def index():
    categories = ['Eco-Finds', 'Eco-Friendly', 'Recycled', 'Water Saving']
    return render_template('index.html', categories=categories)

@main.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    
    query = Product.query.filter_by(is_sold=False)
    
    if search:
        query = query.filter(
            or_(
                Product.title.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    if city:
        query = query.filter_by(city=city)
    
    if state:
        query = query.filter_by(state=state)
    
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('products.html', 
                         products=products,
                         search=search,
                         category=category,
                         city=city,
                         state=state)

@main.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

@main.route('/submit-complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    form = ComplaintForm()
    if form.validate_on_submit():
        complaint = Complaint(
            user_id=current_user.id,
            subject=form.subject.data,
            description=form.description.data,
            category=form.category.data  # Use category from form
        )
        
        if form.evidence.data:
            filename = secure_filename(form.evidence.data.filename)
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'complaints')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(upload_dir, filename)
            form.evidence.data.save(file_path)
            
            # Store the relative URL
            complaint.evidence_url = f'/static/uploads/complaints/{filename}'
        
        db.session.add(complaint)
        db.session.commit()
        
        flash('Your complaint has been submitted successfully.', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('submit_complaint.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get user's complaints ordered by most recent
        complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    except Exception as e:
        # If there's an error (like missing columns), return an empty list
        print(f"Error fetching complaints: {str(e)}")
        complaints = []
    
    return render_template('dashboard.html', user=current_user, complaints=complaints)

@main.route('/product/<int:product_id>/rate', methods=['GET', 'POST'])
@login_required
def rate_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        rating_value = request.form.get('rating', type=int)
        review_text = request.form.get('review')
        categories = {}
        
        # Get category ratings
        for category in ['quality', 'value', 'durability', 'design', 'performance']:
            score = request.form.get(f'category_{category}', type=int)
            if score:
                categories[category] = score
        
        if not rating_value or rating_value < 1 or rating_value > 5:
            flash('Please provide a valid rating between 1 and 5 stars.', 'danger')
            return redirect(url_for('main.rate_product', product_id=product_id))
        
        # Handle photo uploads
        photos = []
        if 'photos' in request.files:
            for photo in request.files.getlist('photos'):
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', unique_filename)
                    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                    photo.save(photo_path)
                    photos.append(f"/uploads/reviews/{unique_filename}")
        
        # Check if user has already rated this product
        existing_rating = product.get_user_rating(current_user.id)
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_value
            existing_rating.review = review_text
            existing_rating.updated_at = datetime.utcnow()
            if photos:
                existing_rating.photos = photos
            if categories:
                existing_rating.categories = categories
            flash('Your rating has been updated successfully!', 'success')
        else:
            # Create new rating
            new_rating = ProductRating(
                user_id=current_user.id,
                product_id=product_id,
                rating=rating_value,
                review=review_text,
                photos=photos,
                categories=categories
            )
            db.session.add(new_rating)
            flash('Thank you for rating this product!', 'success')
        
        db.session.commit()
        return redirect(url_for('main.rate_product', product_id=product_id))
    
    return render_template('product/rating.html', product=product)

@main.route('/rating/<int:rating_id>/helpful', methods=['POST'])
@login_required
def mark_rating_helpful(rating_id):
    rating = ProductRating.query.get_or_404(rating_id)
    
    if current_user.id == rating.user_id:
        return jsonify({
            'success': False,
            'message': 'You cannot mark your own review as helpful'
        }), 400
    
    if current_user in rating.helpful_voters:
        # Remove helpful vote
        rating.helpful_voters.remove(current_user)
        rating.helpful_votes -= 1
        action = 'removed'
    else:
        # Add helpful vote
        rating.helpful_voters.append(current_user)
        rating.helpful_votes += 1
        action = 'added'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'helpful_votes': rating.helpful_votes
    })

@main.route('/product/<int:product_id>/ratings')
def view_product_ratings(product_id):
    product = Product.query.get_or_404(product_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort', 'recent')  # recent, helpful, highest, lowest
    
    query = ProductRating.query.filter_by(product_id=product_id)
    
    if sort_by == 'helpful':
        query = query.order_by(ProductRating.helpful_votes.desc(), ProductRating.created_at.desc())
    elif sort_by == 'highest':
        query = query.order_by(ProductRating.rating.desc(), ProductRating.created_at.desc())
    elif sort_by == 'lowest':
        query = query.order_by(ProductRating.rating.asc(), ProductRating.created_at.desc())
    else:  # recent
        query = query.order_by(ProductRating.created_at.desc())
    
    ratings = query.paginate(page=page, per_page=per_page)
    
    return render_template('product/rating.html', 
                         product=product,
                         ratings=ratings,
                         sort_by=sort_by)

@main.route('/rating/<int:rating_id>/photo', methods=['POST'])
@login_required
def add_rating_photo(rating_id):
    rating = ProductRating.query.get_or_404(rating_id)
    
    if current_user.id != rating.user_id:
        return jsonify({
            'success': False,
            'message': 'You can only add photos to your own reviews'
        }), 403
    
    if 'photo' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No photo provided'
        }), 400
    
    photo = request.files['photo']
    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reviews', unique_filename)
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        photo.save(photo_path)
        
        photo_url = f"/uploads/reviews/{unique_filename}"
        rating.add_photo(photo_url)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'photo_url': photo_url
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid file type'
    }), 400

@main.route('/rating/<int:rating_id>/photo/<path:photo_url>', methods=['DELETE'])
@login_required
def remove_rating_photo(rating_id, photo_url):
    rating = ProductRating.query.get_or_404(rating_id)
    
    if current_user.id != rating.user_id:
        return jsonify({
            'success': False,
            'message': 'You can only remove photos from your own reviews'
        }), 403
    
    rating.remove_photo(photo_url)
    db.session.commit()
    
    return jsonify({
        'success': True
    })

@main.route('/product/<int:product_id>/rating-analytics')
def rating_analytics(product_id):
    product = Product.query.get_or_404(product_id)
    analytics = product.get_rating_analytics()
    
    # Add category labels for better display
    category_labels = {
        'quality': 'Product Quality',
        'value': 'Value for Money',
        'durability': 'Durability',
        'design': 'Design & Style',
        'performance': 'Performance'
    }
    
    analytics['category_labels'] = category_labels
    return jsonify(analytics)

@main.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price', type=float)
        category = request.form.get('category')
        condition = request.form.get('condition')
        image = request.files.get('image')
        
        if not all([title, description, price, category, condition]):
            flash('All fields are required', 'danger')
            return redirect(url_for('main.new_product'))
        
        product = Product(
            title=title,
            description=description,
            price=price,
            category=category,
            condition=condition,
            seller_id=current_user.id
        )
        
        if image:
            filename = secure_filename(image.filename)
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(upload_dir, filename)
            image.save(file_path)
            
            # Store the relative URL
            product.image_url = f'/static/uploads/products/{filename}'
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product listed successfully!', 'success')
        return redirect(url_for('main.products'))
    
    return render_template('new_product.html')

@main.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if current_user.id != product.owner_id:
        flash('You do not have permission to edit this product', 'danger')
        return redirect(url_for('main.products'))
    
    if request.method == 'POST':
        product.title = request.form.get('title')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products', unique_filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                product.image_url = f"/uploads/products/{unique_filename}"
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('main.products'))
    
    return render_template('edit_product.html', product=product)

@main.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if current_user.id != product.owner_id:
        flash('You do not have permission to delete this product', 'danger')
        return redirect(url_for('main.products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('main.products'))

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if current_user.id == product.owner_id:
        flash('You cannot add your own product to cart', 'danger')
        return redirect(url_for('main.products'))
    
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('main.cart'))

@main.route('/update_cart_quantity/<int:cart_item_id>', methods=['POST'])
@login_required
def update_cart_quantity(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if current_user.id != cart_item.user_id:
        flash('You do not have permission to update this cart item', 'danger')
        return redirect(url_for('main.cart'))
    
    action = request.form.get('action')
    
    if action == 'increment':
        cart_item.quantity += 1
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
    
    db.session.commit()
    return redirect(url_for('main.cart'))

@main.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if current_user.id != cart_item.user_id:
        flash('You do not have permission to remove this cart item', 'danger')
        return redirect(url_for('main.cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart', 'success')
    return redirect(url_for('main.cart'))

@main.route('/purchase_cart', methods=['POST'])
@login_required
def purchase_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('main.cart'))
    
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    redeem_eco_points = request.form.get('redeem_eco_points', type=int) or 0
    
    if redeem_eco_points > current_user.eco_points:
        flash('You do not have enough ECO points', 'danger')
        return redirect(url_for('main.cart'))
    
    # Calculate discount from ECO points (1 point = $0.01)
    discount = redeem_eco_points * 0.01
    final_amount = max(0, total_amount - discount)
    
    # Create purchase records
    for item in cart_items:
        purchase = Purchase(
            user_id=current_user.id,
            product_id=item.product.id,
            purchase_price=item.product.price * item.quantity
        )
        db.session.add(purchase)
    
    # Update user's ECO points
    current_user.eco_points -= redeem_eco_points
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    
    flash('Purchase completed successfully!', 'success')
    return redirect(url_for('main.purchases'))

@main.route('/purchases')
@login_required
def purchases():
    user_purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.created_at.desc()).all()
    return render_template('purchases.html', purchases=user_purchases)

@main.route('/profile')
@login_required
def profile():
    user = current_user
    user_purchases = Purchase.query.filter_by(user_id=user.id).order_by(Purchase.created_at.desc()).all()
    user_products = Product.query.filter_by(seller_id=user.id).all()
    user_reviews = ProductRating.query.filter_by(user_id=user.id).all()
    
    return render_template('profile.html', 
                         user=user,
                         purchases=user_purchases,
                         products=user_products,
                         reviews=user_reviews) 