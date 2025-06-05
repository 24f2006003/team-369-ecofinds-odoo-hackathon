import os
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.main import bp
from app.models import Product, Category, Bid, ChatMessage, Order, ProductRating, Complaint, Dispute, Notification, User, CartItem, Rating
from app.utils import secure_filename
from datetime import datetime, timedelta
from flask_babel import _

@bp.route('/')
def index():
    """Home page"""
    categories = Category.query.all()
    return render_template('index.html', categories=categories)

@bp.route('/products')
def products():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_sold=False)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))
    
    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()
    
    return render_template('products.html', 
                         title='Products', 
                         products=products,
                         categories=categories,
                         selected_category=category_id,
                         search=search)

@bp.route('/product/<int:id>')
def product(id):
    """View a single product"""
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', title=product.title, product=product)

@bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create a new product"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        condition = request.form.get('condition')
        price = request.form.get('price', type=float)
        city = request.form.get('city')
        state = request.form.get('state')
        image_url = request.form.get('image_url')
        
        # Handle image upload
        image = request.files.get('image')
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = url_for('static', filename=f'uploads/{filename}')
        
        # Create new product
        product = Product(
            title=title,
            description=description,
            category_id=category_id,
            condition=condition,
            price=price,
            seller_id=current_user.id,
            city=city,
            state=state,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(_('Product added successfully!'), 'success')
        return redirect(url_for('main.product', id=product.id))
    
    categories = Category.query.all()
    return render_template('new_product.html', title='New Product', categories=categories)

@bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """Edit an existing product"""
    product = Product.query.get_or_404(id)
    
    if product.seller != current_user:
        flash('You can only edit your own products.', 'danger')
        return redirect(url_for('main.product', id=product.id))
    
    if request.method == 'POST':
        product.title = request.form.get('title')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.category_id = request.form.get('category_id', type=int)
        product.condition = request.form.get('condition')
        
        # Handle image upload
        image = request.files.get('image')
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            product.image_url = url_for('static', filename=f'uploads/{filename}')
        
        db.session.commit()
        flash('Your product has been updated!', 'success')
        return redirect(url_for('main.product', id=product.id))
    
    categories = Category.query.all()
    return render_template('edit_product.html', title='Edit Product', 
                         product=product, categories=categories)

@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    """Delete a product"""
    product = Product.query.get_or_404(id)
    
    if product.seller != current_user:
        flash('You can only delete your own products.', 'danger')
        return redirect(url_for('main.product', id=product.id))
    
    db.session.delete(product)
    db.session.commit()
    flash('Your product has been deleted.', 'success')
    return redirect(url_for('main.products'))

@bp.route('/product/<int:id>/bid', methods=['POST'])
@login_required
def place_bid(id):
    """Place a bid on an auction product"""
    product = Product.query.get_or_404(id)
    
    if not product.is_auction:
        return jsonify({'error': 'This product is not available for auction'}), 400
    
    if not product.is_auction_active():
        return jsonify({'error': 'This auction is not active'}), 400
    
    if product.seller_id == current_user.id:
        return jsonify({'error': 'You cannot bid on your own product'}), 400
    
    try:
        amount = float(request.form.get('amount'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid bid amount'}), 400
    
    bid = Bid(
        product_id=product.id,
        user_id=current_user.id,
        amount=amount
    )
    
    if not bid.is_valid():
        return jsonify({
            'error': 'Invalid bid amount',
            'min_bid': product.get_current_highest_bid() + product.auction_min_bid_increment
        }), 400
    
    # Update previous winning bid
    previous_winning = Bid.query.filter_by(
        product_id=product.id,
        is_winning=True
    ).first()
    if previous_winning:
        previous_winning.is_winning = False
    
    bid.is_winning = True
    db.session.add(bid)
    
    # Create notification for seller
    seller = User.query.get(product.seller_id)
    seller.create_notification(
        type='bid',
        title='New Bid',
        message=f'You have received a new bid of ${amount:.2f} on {product.title}',
        link=url_for('main.product', id=product.id)
    )
    
    # Extend auction if needed
    if product.extend_auction():
        flash('Auction has been extended due to new bid!', 'info')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Bid placed successfully',
        'bid': {
            'amount': bid.amount,
            'created_at': bid.created_at.isoformat()
        }
    })

@bp.route('/product/<int:id>/auction/start', methods=['POST'])
@login_required
def start_auction(id):
    """Start an auction for a product"""
    product = Product.query.get_or_404(id)
    
    if product.seller_id != current_user.id:
        return jsonify({'error': 'You can only start auctions for your own products'}), 403
    
    if product.is_auction:
        return jsonify({'error': 'This product is already an auction'}), 400
    
    try:
        start_price = float(request.form.get('start_price'))
        duration_hours = int(request.form.get('duration_hours', 24))
        min_increment = float(request.form.get('min_increment', 1.0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid auction parameters'}), 400
    
    product.is_auction = True
    product.auction_start_price = start_price
    product.auction_end_time = datetime.utcnow() + timedelta(hours=duration_hours)
    product.auction_min_bid_increment = min_increment
    product.auction_status = 'active'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Auction started successfully',
        'auction': {
            'start_price': product.auction_start_price,
            'end_time': product.auction_end_time.isoformat(),
            'min_increment': product.auction_min_bid_increment
        }
    })

@bp.route('/product/<int:id>/auction/end', methods=['POST'])
@login_required
def end_auction(id):
    """End an auction manually"""
    product = Product.query.get_or_404(id)
    
    if product.seller_id != current_user.id:
        return jsonify({'error': 'You can only end auctions for your own products'}), 403
    
    if not product.is_auction or not product.is_auction_active():
        return jsonify({'error': 'This product is not an active auction'}), 400
    
    product.auction_status = 'ended'
    
    # Get winning bid
    winning_bid = Bid.query.filter_by(
        product_id=product.id,
        is_winning=True
    ).first()
    
    if winning_bid:
        # Create purchase record
        order = Order(
            user_id=winning_bid.user_id,
            product_id=product.id,
            price=winning_bid.amount,
            quantity=1,
            status='purchased'
        )
        db.session.add(order)
        product.is_sold = True
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Auction ended successfully',
        'winning_bid': winning_bid.amount if winning_bid else None
    })

@bp.route('/product/<int:id>/auction/bids')
def get_auction_bids(id):
    """Get all bids for an auction"""
    product = Product.query.get_or_404(id)
    
    if not product.is_auction:
        return jsonify({'error': 'This product is not an auction'}), 400
    
    bids = Bid.query.filter_by(product_id=product.id).order_by(Bid.amount.desc()).all()
    
    return jsonify({
        'bids': [{
            'amount': bid.amount,
            'user': bid.user.username,
            'created_at': bid.created_at.isoformat(),
            'is_winning': bid.is_winning
        } for bid in bids]
    })

@bp.route('/chat')
@login_required
def chat_list():
    """List all chat conversations"""
    # Get all products the user has chatted about
    chats = db.session.query(Product, ChatMessage).\
        join(ChatMessage, Product.id == ChatMessage.product_id).\
        filter(
            (ChatMessage.sender_id == current_user.id) |
            (Product.seller_id == current_user.id)
        ).\
        order_by(ChatMessage.created_at.desc()).\
        all()
    
    # Group chats by product
    chat_dict = {}
    for product, message in chats:
        if product.id not in chat_dict:
            chat_dict[product.id] = {
                'product': product,
                'last_message': message,
                'buyer': message.sender if product.seller_id == current_user.id else current_user
            }
    
    return render_template('chat.html', 
                         title='Messages',
                         chats=chat_dict.values(),
                         current_product=None)

@bp.route('/chat/<int:product_id>')
@login_required
def chat(product_id):
    """View chat for a specific product"""
    product = Product.query.get_or_404(product_id)
    
    # Verify user is either buyer or seller
    if current_user.id != product.seller_id and not ChatMessage.query.filter_by(
        product_id=product_id,
        sender_id=current_user.id
    ).first():
        flash('You do not have access to this chat.', 'danger')
        return redirect(url_for('main.product', id=product_id))
    
    # Get all messages for this product
    messages = ChatMessage.query.filter_by(product_id=product_id).\
        order_by(ChatMessage.created_at.asc()).all()
    
    # Get all chats for the sidebar
    chats = db.session.query(Product, ChatMessage).\
        join(ChatMessage, Product.id == ChatMessage.product_id).\
        filter(
            (ChatMessage.sender_id == current_user.id) |
            (Product.seller_id == current_user.id)
        ).\
        order_by(ChatMessage.created_at.desc()).\
        all()
    
    # Group chats by product
    chat_dict = {}
    for p, message in chats:
        if p.id not in chat_dict:
            chat_dict[p.id] = {
                'product': p,
                'last_message': message,
                'buyer': message.sender if p.seller_id == current_user.id else current_user
            }
    
    return render_template('chat.html',
                         title=f'Chat - {product.title}',
                         chats=chat_dict.values(),
                         current_product=product,
                         messages=messages)

@bp.route('/chat/<int:product_id>/send', methods=['POST'])
@login_required
def send_message(product_id):
    """Send a message in a chat"""
    product = Product.query.get_or_404(product_id)
    
    # Verify user is either buyer or seller
    if current_user.id != product.seller_id and not ChatMessage.query.filter_by(
        product_id=product_id,
        sender_id=current_user.id
    ).first():
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    message = ChatMessage(
        sender_id=current_user.id,
        receiver_id=product.seller_id if current_user.id != product.seller_id else None,
        product_id=product_id,
        message=data['message']
    )
    
    db.session.add(message)
    
    # Create notification for receiver
    if message.receiver_id:
        receiver = User.query.get(message.receiver_id)
        receiver.create_notification(
            type='message',
            title='New Message',
            message=f'You have a new message from {current_user.username} about {product.title}',
            link=url_for('main.chat', product_id=product_id)
        )
    
    db.session.commit()
    
    return jsonify({
        'message': message.message,
        'created_at': message.created_at.isoformat()
    })

@bp.route('/chat/<int:product_id>/messages')
@login_required
def get_messages(product_id):
    """Get all messages for a chat"""
    product = Product.query.get_or_404(product_id)
    
    # Verify user is either buyer or seller
    if current_user.id != product.seller_id and not ChatMessage.query.filter_by(
        product_id=product_id,
        sender_id=current_user.id
    ).first():
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = ChatMessage.query.filter_by(product_id=product_id).\
        order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'messages': [{
            'id': msg.id,
            'message': msg.message,
            'sender_id': msg.sender_id,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
    })

@bp.route('/orders')
@login_required
def orders():
    """List all orders for the current user"""
    status = request.args.get('status')
    query = Order.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('orders.html', title='My Orders', orders=orders)

@bp.route('/order/<int:id>')
@login_required
def view_order(id):
    """View a single order"""
    order = Order.query.get_or_404(id)
    if order.user_id != current_user.id and order.product.seller_id != current_user.id:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('main.orders'))
    return render_template('order.html', title='Order Details', order=order)

@bp.route('/order/<int:id>/rate', methods=['GET', 'POST'])
@login_required
def rate_order(id):
    """Rate an order"""
    order = Order.query.get_or_404(id)
    
    if order.user_id != current_user.id and order.product.seller_id != current_user.id:
        flash('You are not authorized to rate this order.', 'danger')
        return redirect(url_for('main.orders'))
    
    if order.is_rated:
        flash('This order has already been rated.', 'warning')
        return redirect(url_for('main.orders'))
    
    if request.method == 'POST':
        rating_value = request.form.get('rating', type=int)
        comment = request.form.get('comment', '')
        
        if not rating_value or rating_value < 1 or rating_value > 5:
            flash('Invalid rating value', 'danger')
            return redirect(url_for('main.rate_order', id=id))
        
        # Determine who is being rated
        rated_id = order.product.seller_id if order.user_id == current_user.id else order.user_id
        
        new_rating = Rating(
            rater_id=current_user.id,
            rated_id=rated_id,
            order_id=order.id,
            rating=rating_value,
            comment=comment
        )
        
        db.session.add(new_rating)
        order.is_rated = True
        db.session.commit()
        
        flash('Thank you for your rating!', 'success')
        return redirect(url_for('main.orders'))
    
    return render_template('rate_order.html', title='Rate Order', order=order)

@bp.route('/product/<int:id>/ratings')
def product_ratings(id):
    """View all ratings for a product"""
    product = Product.query.get_or_404(id)
    ratings = ProductRating.query.filter_by(product_id=id).order_by(ProductRating.created_at.desc()).all()
    
    return render_template('product_ratings.html',
                         title=f'Ratings - {product.title}',
                         product=product,
                         ratings=ratings)

@bp.route('/rating/<int:id>/helpful', methods=['POST'])
@login_required
def mark_rating_helpful(id):
    """Mark a rating as helpful"""
    rating = ProductRating.query.get_or_404(id)
    
    # Check if user has already marked this rating as helpful
    if current_user in rating.helpful_voters:
        return jsonify({'error': 'You have already marked this rating as helpful'}), 400
    
    rating.helpful_votes += 1
    rating.helpful_voters.append(current_user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'helpful_votes': rating.helpful_votes
    })

@bp.route('/product/<int:id>/complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint(id):
    """Submit a complaint about a product or transaction"""
    product = Product.query.get_or_404(id)
    order = Order.query.filter_by(
        product_id=id,
        user_id=current_user.id
    ).first()
    
    if not order and product.seller_id != current_user.id:
        flash('You can only submit complaints for products you have purchased or sold.', 'danger')
        return redirect(url_for('main.product', id=id))
    
    if request.method == 'POST':
        try:
            complaint_type = request.form.get('complaint_type')
            description = request.form.get('description')
            resolution_request = request.form.get('resolution_request')
            additional_notes = request.form.get('additional_notes')
            
            # Handle photo uploads
            photos = []
            if 'photos' in request.files:
                for photo in request.files.getlist('photos'):
                    if photo.filename:
                        filename = secure_filename(photo.filename)
                        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        photo.save(photo_path)
                        photos.append(url_for('static', filename=f'uploads/{filename}'))
            
            # Create complaint
            complaint = Complaint(
                user_id=current_user.id,
                product_id=id,
                complaint_type=complaint_type,
                description=description,
                photos=photos
            )
            
            # Create dispute if resolution is requested
            if resolution_request:
                dispute = Dispute(
                    complaint=complaint,
                    status='open',
                    resolution_type=resolution_request
                )
                if additional_notes:
                    dispute.admin_notes = additional_notes
            
            db.session.add(complaint)
            db.session.commit()
            
            flash('Your complaint has been submitted successfully.', 'success')
            return redirect(url_for('main.view_complaint', id=complaint.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your complaint.', 'danger')
            return redirect(url_for('main.submit_complaint', id=id))
    
    return render_template('complaint_form.html',
                         title='Submit Complaint',
                         product=product,
                         order=order)

@bp.route('/complaint/<int:id>')
@login_required
def view_complaint(id):
    """View a complaint and its status"""
    complaint = Complaint.query.get_or_404(id)
    
    # Verify user has access to this complaint
    if current_user.id != complaint.user_id and current_user.id != complaint.product.seller_id:
        flash('You do not have access to this complaint.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('complaint_details.html',
                         title='Complaint Details',
                         complaint=complaint)

@bp.route('/complaints')
@login_required
def list_complaints():
    """List all complaints for the current user"""
    complaints = Complaint.query.filter(
        (Complaint.user_id == current_user.id) |
        (Complaint.product.has(seller_id=current_user.id))
    ).order_by(Complaint.created_at.desc()).all()
    
    return render_template('complaints.html',
                         title='My Complaints',
                         complaints=complaints)

@bp.route('/complaint/<int:id>/update', methods=['POST'])
@login_required
def update_complaint(id):
    """Update a complaint (admin only)"""
    complaint = Complaint.query.get_or_404(id)
    
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'status' in data:
            complaint.status = data['status']
            # Create notification for user
            complaint.user.create_notification(
                type='complaint',
                title='Complaint Status Updated',
                message=f'Your complaint about {complaint.product.title} has been {data["status"]}',
                link=url_for('main.view_complaint', id=complaint.id)
            )
        if 'resolution_notes' in data:
            complaint.resolution_notes = data['resolution_notes']
        
        if complaint.dispute and 'dispute' in data:
            dispute = complaint.dispute
            if 'status' in data['dispute']:
                dispute.status = data['dispute']['status']
                # Create notification for user
                complaint.user.create_notification(
                    type='dispute',
                    title='Dispute Status Updated',
                    message=f'Your dispute about {complaint.product.title} has been {data["dispute"]["status"]}',
                    link=url_for('main.view_complaint', id=complaint.id)
                )
            if 'mediator_id' in data['dispute']:
                dispute.mediator_id = data['dispute']['mediator_id']
                # Create notification for mediator
                mediator = User.query.get(data['dispute']['mediator_id'])
                mediator.create_notification(
                    type='mediation',
                    title='New Mediation Assignment',
                    message=f'You have been assigned to mediate a dispute about {complaint.product.title}',
                    link=url_for('main.view_complaint', id=complaint.id)
                )
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Complaint updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/admin/complaints')
@login_required
def admin_complaints():
    """Admin view of all complaints"""
    if not current_user.is_admin:
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('main.index'))
    
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Complaint.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    complaints = query.order_by(Complaint.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/complaints.html',
                         title='Manage Complaints',
                         complaints=complaints,
                         current_status=status)

@bp.route('/notifications')
@login_required
def notifications():
    """View all notifications for the current user"""
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html',
                         title='Notifications',
                         notifications=notifications)

@bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    """Mark a specific notification as read"""
    if current_user.mark_notification_read(id):
        return jsonify({'success': True})
    return jsonify({'error': 'Notification not found'}), 404

@bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    current_user.mark_all_notifications_read()
    return jsonify({'success': True})

@bp.route('/cart')
def cart():
    """Display the user's cart."""
    if not current_user.is_authenticated:
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('auth.login'))
    cart_items = current_user.get_cart_items()
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', title='My Cart', cart_items=cart_items, cart_total=cart_total)

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add a product to the user's cart."""
    product = Product.query.get_or_404(product_id)
    if product.is_sold:
        flash('This product is no longer available.', 'warning')
        return redirect(url_for('main.product', id=product_id))
    # Add the product to the user's cart
    current_user.add_to_cart(product)
    flash('Product added to cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in current_app.config['LANGUAGES']:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/update_cart_quantity/<int:cart_item_id>', methods=['POST'])
@login_required
def update_cart_quantity(cart_item_id):
    """Update the quantity of a product in the cart"""
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if cart_item.user_id != current_user.id:
        flash(_('You do not have permission to update this cart item'), 'danger')
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

@bp.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    """Remove a product from the cart"""
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if cart_item.user_id != current_user.id:
        flash(_('You do not have permission to remove this cart item'), 'danger')
        return redirect(url_for('main.cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash(_('Item removed from cart'), 'success')
    return redirect(url_for('main.cart'))

@bp.route('/purchase_cart', methods=['POST'])
@login_required
def purchase_cart():
    """Purchase all items in the cart"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('main.cart'))
    
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    eco_points = request.form.get('eco_points', type=int) or 0
    
    if eco_points > current_user.eco_points:
        flash('You do not have enough ECO points', 'danger')
        return redirect(url_for('main.cart'))
    
    # Calculate discount from ECO points (1 point = $0.01)
    discount = eco_points * 0.01
    final_amount = max(0, total_amount - discount)
    
    # Create purchase records
    for item in cart_items:
        order = Order(
            user_id=current_user.id,
            product_id=item.product.id,
            price=item.product.price * item.quantity,
            quantity=item.quantity,
            status='purchased'
        )
        db.session.add(order)
    
    # Update user's ECO points
    current_user.eco_points -= eco_points
    
    # Award new ECO points (10% of final amount)
    points_earned = int(final_amount / 10)  # 10 points per dollar
    current_user.eco_points += points_earned
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    
    flash(f'Purchase completed successfully! You earned {points_earned} ECO points.', 'success')
    return redirect(url_for('main.orders'))

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard view"""
    if not current_user.is_admin:
        flash(_('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('main.index'))
    
    # Get statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    active_complaints = Complaint.query.filter(Complaint.status.in_(['pending', 'in_progress'])).count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get recent complaints
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         active_complaints=active_complaints,
                         recent_orders=recent_orders,
                         recent_complaints=recent_complaints) 