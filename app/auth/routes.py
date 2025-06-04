from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, OTP
from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime, timedelta
import re
from app.utils import send_verification_email, send_otp_sms
from flask_babel import _

auth = Blueprint('auth', __name__)

def is_valid_phone(phone):
    # Basic phone number validation (can be enhanced based on requirements)
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def is_valid_email(email):
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Log form data for debugging
            current_app.logger.info(f'Registration attempt - Username: {username}, Email: {email}, Phone: {phone_number}')
            
            # Validate required fields
            if not all([username, email, phone_number, password, confirm_password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('auth.register'))
            
            # Validate password match
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('auth.register'))
            
            # Validate password length
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'danger')
                return redirect(url_for('auth.register'))
            
            # Validate email format
            if not is_valid_email(email):
                flash('Invalid email format', 'danger')
                return redirect(url_for('auth.register'))
            
            # Validate phone number format
            if not is_valid_phone(phone_number):
                flash('Invalid phone number format. Please include country code (e.g., +1)', 'danger')
                return redirect(url_for('auth.register'))
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('auth.register'))
            
            if User.query.filter_by(phone_number=phone_number).first():
                flash('Phone number already registered', 'danger')
                return redirect(url_for('auth.register'))
            
            # Create new user
            try:
                user = User(
                    email=email,
                    username=username,
                    phone_number=phone_number,
                    is_email_verified=True,  # Temporarily set to True for testing
                    is_phone_verified=True   # Temporarily set to True for testing
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                # Log successful registration
                current_app.logger.info(f'User registered successfully - ID: {user.id}, Email: {user.email}')
                
                flash('Registration successful! You can now login.', 'success')
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                current_app.logger.error(f'Error creating user: {str(e)}')
                db.session.rollback()
                flash('Error creating user account. Please try again.', 'danger')
                return redirect(url_for('auth.register'))
                
        except Exception as e:
            current_app.logger.error(f'Registration error: {str(e)}')
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link')
        return redirect(url_for('auth.login'))
        
    user.is_email_verified = True
    user.email_verification_token = None
    db.session.commit()
    
    flash('Email verified successfully!')
    return redirect(url_for('auth.login'))

@auth.route('/verify-phone', methods=['POST'])
def verify_phone():
    data = request.get_json()
    if not all(k in data for k in ['phone_number', 'otp']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    user = User.query.filter_by(phone_number=data['phone_number']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    otp = OTP.query.filter_by(user_id=user.id, is_used=False).order_by(OTP.created_at.desc()).first()
    if not otp or not otp.is_valid():
        return jsonify({'error': 'Invalid or expired OTP'}), 400
        
    if otp.otp_code != data['otp']:
        return jsonify({'error': 'Invalid OTP'}), 400
        
    user.is_phone_verified = True
    otp.is_used = True
    db.session.commit()
    
    return jsonify({'message': 'Phone number verified successfully'}), 200

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_landing'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash(_('Please provide both email and password'), 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash(_('No account found with this email. Please register first.'), 'warning')
            return redirect(url_for('auth.register'))
        
        if not user.check_password(password):
            flash(_('Invalid password. Please try again.'), 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        flash(_('Login successful!'), 'success')
        
        if user.is_admin:
            return redirect(url_for('admin_landing'))
        return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    if 'phone_number' not in data:
        return jsonify({'error': 'Phone number is required'}), 400
        
    user = User.query.filter_by(phone_number=data['phone_number']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Create new OTP
    otp = OTP(user.id)
    db.session.add(otp)
    db.session.commit()
    
    # TODO: Send OTP via SMS service
    
    return jsonify({
        'message': 'OTP sent successfully',
        'otp': otp.otp_code  # Remove this in production, only for testing
    }), 200 