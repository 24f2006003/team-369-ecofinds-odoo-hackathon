from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets
import hashlib
import os
from flask import flash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    eco_points = db.Column(db.Integer, default=0)
    profile_img = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    email_verification_token = db.Column(db.String(100), unique=True)
    
    # Relationships
    products = db.relationship('Product', back_populates='seller', lazy=True)
    orders = db.relationship('Order', back_populates='user', lazy=True)
    ratings = db.relationship('ProductRating', back_populates='user', lazy=True)
    complaints = db.relationship('Complaint', foreign_keys='Complaint.user_id', back_populates='user', lazy=True)
    assigned_complaints = db.relationship('Complaint', foreign_keys='Complaint.assigned_to_id', back_populates='assigned_to', lazy=True)
    sent_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.receiver_id', backref='receiver', lazy=True)
    given_ratings = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater', lazy=True)
    received_ratings = db.relationship('Rating', foreign_keys='Rating.rated_id', backref='rated', lazy=True)
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    cart_items = db.relationship('Product', secondary='cart', lazy='dynamic',
                               backref=db.backref('cart_users', lazy='dynamic'))

    def get_unread_notifications(self):
        """Get all unread notifications for the user"""
        return self.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).all()
    
    def mark_notification_read(self, notification_id):
        """Mark a specific notification as read"""
        notification = self.notifications.filter_by(id=notification_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False
    
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        self.notifications.filter_by(is_read=False).update({'is_read': True})
        db.session.commit()

    def create_notification(self, type, title, message, link=None):
        """Create a new notification for the user"""
        notification = Notification(
            user_id=self.id,
            type=type,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    def set_password(self, password):
        """Hash and set the user's password"""
        salt = os.urandom(32)  # Generate a random salt
        key = hashlib.pbkdf2_hmac(
            'sha256',  # Hash algorithm
            password.encode('utf-8'),  # Convert password to bytes
            salt,  # Salt
            100000  # Number of iterations
        )
        # Store salt and key together
        self.password_hash = salt.hex() + ':' + key.hex()

    def check_password(self, password):
        """Verify the password against the stored hash"""
        if not self.password_hash:
            return False
        
        # Split the stored hash into salt and key
        salt_hex, key_hex = self.password_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        
        # Hash the provided password with the same salt
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return key == stored_key

    def generate_email_verification_token(self):
        token = secrets.token_urlsafe(32)
        self.email_verification_token = token
        return token

    def __repr__(self):
        return f'<User {self.username}>'

    def get_cart_items(self):
        """Get all items in the user's cart"""
        return CartItem.query.filter_by(user_id=self.id).all()

    def add_to_cart(self, product, quantity=1):
        """Add a product to the user's cart"""
        cart_item = CartItem.query.filter_by(user_id=self.id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=self.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()

    def update_cart_quantity(self, product_id, quantity):
        """Update the quantity of a product in the cart"""
        cart_item = CartItem.query.filter_by(user_id=self.id, product_id=product_id).first()
        if cart_item:
            if quantity <= 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
            db.session.commit()

    def remove_from_cart(self, product_id):
        """Remove a product from the cart"""
        cart_item = CartItem.query.filter_by(user_id=self.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()

    def get_purchases(self):
        """Get all purchased items"""
        return Order.query.filter_by(user_id=self.id, status='purchased').all()
    
    def get_delivered_items(self):
        """Get all delivered items"""
        return Order.query.filter_by(user_id=self.id, status='delivered').all()
    
    def get_cancelled_items(self):
        """Get all cancelled items"""
        return Order.query.filter_by(user_id=self.id, status='cancelled').all()
    
    def get_returned_items(self):
        """Get all returned items"""
        return Order.query.filter_by(user_id=self.id, status='returned').all()

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category_obj', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def __init__(self, user_id):
        self.user_id = user_id
        self.otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)

    def is_valid(self):
        return not self.is_used and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f'<OTP {self.id}>'

class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # new, like_new, good, fair
    image_url = db.Column(db.String(500))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_sold = db.Column(db.Boolean, default=False)
    
    # Auction-related fields
    is_auction = db.Column(db.Boolean, default=False)
    auction_start_price = db.Column(db.Float)
    auction_end_time = db.Column(db.DateTime)
    auction_min_bid_increment = db.Column(db.Float, default=1.0)
    auction_auto_extend = db.Column(db.Boolean, default=True)
    auction_extend_minutes = db.Column(db.Integer, default=5)
    auction_status = db.Column(db.String(20), default='pending')  # pending, active, ended, cancelled
    
    # Relationships
    seller = db.relationship('User', back_populates='products')
    orders = db.relationship('Order', back_populates='product', lazy=True)
    product_ratings = db.relationship('ProductRating', back_populates='rated_product')
    complaints = db.relationship('Complaint', back_populates='product')
    bids = db.relationship('Bid', back_populates='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.title}>'

    def get_average_rating(self):
        ratings = [r.rating for r in self.product_ratings]
        return sum(ratings) / len(ratings) if ratings else 0
    
    def get_rating_count(self):
        return len(self.product_ratings)
    
    def get_rating_distribution(self):
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in self.product_ratings:
            distribution[rating.rating] += 1
        return distribution
    
    def has_user_rated(self, user_id):
        return any(r.user_id == user_id for r in self.product_ratings)
    
    def get_user_rating(self, user_id):
        for rating in self.product_ratings:
            if rating.user_id == user_id:
                return rating
        return None

    def get_rating_analytics(self):
        """Get detailed rating analytics for the product"""
        ratings = self.product_ratings
        total_ratings = len(ratings)
        
        if not total_ratings:
            return {
                'average': 0,
                'total': 0,
                'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'verified_purchase_percentage': 0,
                'with_photos_percentage': 0,
                'with_reviews_percentage': 0,
                'helpful_votes_total': 0,
                'sentiment_distribution': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'category_distribution': {},
                'sentiment_trend': []
            }
        
        # Calculate distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        verified_count = 0
        photos_count = 0
        reviews_count = 0
        helpful_votes_total = 0
        sentiment_distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
        category_distribution = {}
        sentiment_trend = []
        
        for rating in ratings:
            distribution[rating.rating] += 1
            if rating.verified_purchase:
                verified_count += 1
            if rating.photos:
                photos_count += 1
            if rating.review:
                reviews_count += 1
                sentiment_distribution[rating.get_sentiment_label().lower()] += 1
                sentiment_trend.append({
                    'date': rating.created_at.strftime('%Y-%m-%d'),
                    'score': rating.sentiment_score
                })
            helpful_votes_total += rating.helpful_votes
            
            # Aggregate category ratings
            for category, score in rating.categories.items():
                if category not in category_distribution:
                    category_distribution[category] = {'total': 0, 'count': 0}
                category_distribution[category]['total'] += score
                category_distribution[category]['count'] += 1
        
        # Calculate category averages
        for category in category_distribution:
            category_distribution[category]['average'] = (
                category_distribution[category]['total'] / 
                category_distribution[category]['count']
            )
        
        return {
            'average': self.get_average_rating(),
            'total': total_ratings,
            'distribution': distribution,
            'verified_purchase_percentage': (verified_count / total_ratings) * 100,
            'with_photos_percentage': (photos_count / total_ratings) * 100,
            'with_reviews_percentage': (reviews_count / total_ratings) * 100,
            'helpful_votes_total': helpful_votes_total,
            'sentiment_distribution': sentiment_distribution,
            'category_distribution': category_distribution,
            'sentiment_trend': sentiment_trend
        }

    def get_current_highest_bid(self):
        """Get the current highest bid for this product"""
        highest_bid = Bid.query.filter_by(product_id=self.id).order_by(Bid.amount.desc()).first()
        return highest_bid.amount if highest_bid else self.auction_start_price

    def get_time_remaining(self):
        """Get the time remaining in the auction"""
        if not self.auction_end_time:
            return None
        remaining = self.auction_end_time - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def is_auction_active(self):
        """Check if the auction is currently active"""
        if not self.is_auction or self.is_sold:
            return False
        return self.auction_status == 'active' and self.get_time_remaining().total_seconds() > 0

    def extend_auction(self):
        """Extend the auction time if auto-extend is enabled"""
        if self.auction_auto_extend and self.is_auction_active():
            self.auction_end_time += timedelta(minutes=self.auction_extend_minutes)
            return True
        return False

    def get_purchase_count(self):
        """Get total number of purchases"""
        return Order.query.filter_by(product_id=self.id, status='purchased').count()
    
    def get_delivery_count(self):
        """Get total number of deliveries"""
        return Order.query.filter_by(product_id=self.id, status='delivered').count()

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase
    status = db.Column(db.String(20), default='added_to_cart')  # added_to_cart, purchased, cancelled, returned, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_rated = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')
    
    def __repr__(self):
        return f'<Order {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_rated': self.is_rated
        }

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    def __repr__(self):
        return f'<Rating {self.id}>'

class Complaint(db.Model):
    """Model for user complaints"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    complaint_type = db.Column(db.String(50), nullable=False)  # product_quality, seller_behavior, shipping_issue, etc.
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_review, resolved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = db.Column(db.Text)
    photos = db.Column(db.JSON)  # List of photo URLs
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='complaints', foreign_keys=[user_id])
    product = db.relationship('Product', back_populates='complaints')
    assigned_to = db.relationship('User', back_populates='assigned_complaints', foreign_keys=[assigned_to_id])
    dispute = db.relationship('Dispute', backref='complaint', uselist=False)
    history = db.relationship('ComplaintHistory', back_populates='complaint', lazy=True)
    
    def __repr__(self):
        return f'<Complaint {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'complaint_type': self.complaint_type,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolution_notes': self.resolution_notes,
            'photos': self.photos
        }

class Dispute(db.Model):
    """Model for dispute resolution"""
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_mediation, resolved, closed
    resolution_type = db.Column(db.String(50))  # refund, replacement, partial_refund, etc.
    resolution_amount = db.Column(db.Float)  # For monetary resolutions
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Mediation fields
    mediator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mediation_notes = db.Column(db.Text)
    mediation_status = db.Column(db.String(20))  # pending, in_progress, completed
    
    # Relationships
    mediator = db.relationship('User', backref=db.backref('mediated_disputes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Dispute {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'status': self.status,
            'resolution_type': self.resolution_type,
            'resolution_amount': self.resolution_amount,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'mediator_id': self.mediator_id,
            'mediation_notes': self.mediation_notes,
            'mediation_status': self.mediation_status
        }

class ComplaintHistory(db.Model):
    __tablename__ = 'complaint_history'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., 'status_change', 'reply', 'assignment'
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    complaint = db.relationship('Complaint', back_populates='history')
    
    def __repr__(self):
        return f'<ComplaintHistory {self.id}>'

class ProductRating(db.Model):
    __tablename__ = 'product_rating'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    helpful_votes = db.Column(db.Integer, default=0)
    verified_purchase = db.Column(db.Boolean, default=False)
    photos = db.Column(db.JSON)  # Store photo URLs as JSON array
    categories = db.Column(db.JSON)  # Store rating categories as JSON
    sentiment_score = db.Column(db.Float)  # -1 to 1, where -1 is negative and 1 is positive
    sentiment_magnitude = db.Column(db.Float)  # 0 to 1, indicating the strength of the sentiment
    
    # Relationships
    user = db.relationship('User', back_populates='ratings')
    rated_product = db.relationship('Product', back_populates='product_ratings')
    helpful_voters = db.relationship('User', 
                                   secondary='rating_helpful_votes',
                                   backref=db.backref('helpful_votes_given', lazy=True))
    
    def __repr__(self):
        return f'<ProductRating {self.id}>'

    def __init__(self, user_id, product_id, rating, review=None, photos=None, categories=None):
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.review = review
        self.photos = photos or []
        self.categories = categories or {}
        # Check if user has purchased the product
        self.verified_purchase = self._check_verified_purchase()
        # Analyze sentiment if review is provided
        if review:
            self._analyze_sentiment()
    
    def _analyze_sentiment(self):
        """Analyze the sentiment of the review text"""
        from textblob import TextBlob
        
        analysis = TextBlob(self.review)
        self.sentiment_score = analysis.sentiment.polarity  # -1 to 1
        self.sentiment_magnitude = analysis.sentiment.subjectivity  # 0 to 1
    
    def get_sentiment_label(self):
        """Get a human-readable sentiment label"""
        if not self.sentiment_score:
            return "Neutral"
        
        if self.sentiment_score > 0.3:
            return "Positive"
        elif self.sentiment_score < -0.3:
            return "Negative"
        else:
            return "Neutral"
    
    def _check_verified_purchase(self):
        return Order.query.filter_by(
            user_id=self.user_id,
            product_id=self.product_id,
            status='purchased'
        ).first() is not None
    
    def add_photo(self, photo_url):
        if not self.photos:
            self.photos = []
        self.photos.append(photo_url)
    
    def remove_photo(self, photo_url):
        if self.photos and photo_url in self.photos:
            self.photos.remove(photo_url)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_name': self.user.username,
            'helpful_votes': self.helpful_votes,
            'verified_purchase': self.verified_purchase,
            'photos': self.photos,
            'categories': self.categories,
            'sentiment': {
                'score': self.sentiment_score,
                'magnitude': self.sentiment_magnitude,
                'label': self.get_sentiment_label()
            }
        }

# Association table for helpful votes
rating_helpful_votes = db.Table('rating_helpful_votes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('rating_id', db.Integer, db.ForeignKey('product_rating.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Bid(db.Model):
    __tablename__ = 'bid'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_winning = db.Column(db.Boolean, default=False)
    
    # Relationships
    product = db.relationship('Product', back_populates='bids')
    user = db.relationship('User', backref='bids')
    
    def __repr__(self):
        return f'<Bid {self.id}>'

    def is_valid(self):
        """Check if the bid is valid"""
        if not self.product.is_auction_active():
            return False
        
        current_highest = self.product.get_current_highest_bid()
        min_increment = self.product.auction_min_bid_increment
        
        return self.amount >= current_highest + min_increment

class Notification(db.Model):
    """Model for user notifications"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # message, complaint, bid, order, rating
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200))  # URL to related content
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

# Cart association table
cart = db.Table('cart',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('cart_users', lazy='dynamic'))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy='dynamic'))