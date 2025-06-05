from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_phone_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    profile_img = db.Column(db.String(200))
    eco_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    products = db.relationship('Product', backref='owner', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    purchases = db.relationship('Purchase', backref='user', lazy=True)
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

    def __repr__(self):
        return f'<Product {self.title}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem {self.id}>'

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchased_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_rated = db.Column(db.Boolean, default=False)

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