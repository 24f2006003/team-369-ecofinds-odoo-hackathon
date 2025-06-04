from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, OTP
from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime, timedelta
import re
from app.utils import send_verification_email, send_otp_sms

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
            username = request.form.get('username')
            email = request.form.get('email')
            phone_number = request.form.get('phone_number')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
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
                    phone_number=phone_number
                )
                user.set_password(password)
                
                # Generate email verification token
                verification_token = user.generate_email_verification_token()
                
                # Create OTP for phone verification
                otp = OTP(user.id)
                
                db.session.add(user)
                db.session.add(otp)
                db.session.commit()
                
                # Send verification email
                try:
                    send_verification_email(user)
                except Exception as e:
                    current_app.logger.error(f'Failed to send verification email: {str(e)}')
                    # Continue with registration even if email fails
                    pass
                
                # Send OTP via SMS
                try:
                    send_otp_sms(user.phone_number, otp.otp_code)
                except Exception as e:
                    current_app.logger.error(f'Failed to send OTP SMS: {str(e)}')
                    # Continue with registration even if SMS fails
                    pass
                
                flash('Registration successful! Please check your email and phone for verification.', 'success')
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
    if request.method == 'POST':
        data = request.get_json()
        
        if not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
            
        if not user.is_email_verified:
            return jsonify({'error': 'Please verify your email first'}), 401
            
        if not user.is_phone_verified:
            return jsonify({'error': 'Please verify your phone number first'}), 401
            
        login_user(user)
        return jsonify({'message': 'Login successful'}), 200
        
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

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