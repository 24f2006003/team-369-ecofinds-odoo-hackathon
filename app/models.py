from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(20), unique=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    eco_points = db.Column(db.Integer, default=0)
    profile_img = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_verification_token = db.Column(db.String(100), unique=True)
    
    # Relationships
    products = db.relationship('Product', back_populates='seller')
    purchases = db.relationship('Purchase', back_populates='user')
    ratings = db.relationship('ProductRating', back_populates='user')
    complaints = db.relationship('Complaint', back_populates='user')
    assigned_complaints = db.relationship('Complaint', back_populates='assigned_to', foreign_keys='Complaint.assigned_to_id')
    complaint_actions = db.relationship('ComplaintHistory', back_populates='created_by')
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    sent_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.receiver_id', backref='receiver', lazy=True)
    given_ratings = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater', lazy=True)
    received_ratings = db.relationship('Rating', foreign_keys='Rating.rated_id', backref='rated', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_email_verification_token(self):
        token = secrets.token_urlsafe(32)
        self.email_verification_token = token
        return token

    def __repr__(self):
        return f'<User {self.username}>'

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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    purchases = db.relationship('Purchase', backref='product', lazy=True)
    product_ratings = db.relationship('ProductRating', backref='rated_product', lazy=True)
    seller = db.relationship('User', back_populates='products')

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

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem {self.id}>'

class Purchase(db.Model):
    __tablename__ = 'purchase'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_rated = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='purchases')
    product = db.relationship('Product', back_populates='purchases')
    
    def __repr__(self):
        return f'<Purchase {self.id}>'

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
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    def __repr__(self):
        return f'<Rating {self.id}>'

class Complaint(db.Model):
    __tablename__ = 'complaint'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    category = db.Column(db.String(50), nullable=False)  # product_issue, seller_issue, technical, other
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='complaints')
    product = db.relationship('Product', back_populates='complaints')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], back_populates='assigned_complaints')
    history = db.relationship('ComplaintHistory', back_populates='complaint_record', lazy=True, cascade='all, delete-orphan')
    
    @property
    def status_color(self):
        status_colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'resolved': 'success',
            'closed': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['resolved', 'closed']:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        if self.due_date and self.status not in ['resolved', 'closed']:
            delta = self.due_date - datetime.utcnow()
            return max(0, delta.days)
        return None

class ComplaintHistory(db.Model):
    __tablename__ = 'complaint_history'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # status_change, reply, assignment
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    created_by = db.relationship('User', backref=db.backref('complaint_actions', lazy=True))

    def __repr__(self):
        return f'<ComplaintHistory {self.id}>'

class ProductRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
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
    user = db.relationship('User', backref=db.backref('product_ratings', lazy=True))
    product = db.relationship('Product', backref=db.backref('ratings', lazy=True))
    helpful_voters = db.relationship('User', 
                                   secondary='rating_helpful_votes',
                                   backref=db.backref('helpful_votes_given', lazy=True))
    
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
        return Purchase.query.filter_by(
            user_id=self.user_id,
            product_id=self.product_id,
            status='completed'
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