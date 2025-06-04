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
            data = request.get_json()
            current_app.logger.info(f'Registration attempt with data: {data}')
            
            # Validate input data
            if not all(k in data for k in ['email', 'password', 'phone_number', 'username']):
                current_app.logger.error('Missing required fields in registration data')
                return jsonify({'error': 'Missing required fields'}), 400
                
            if not is_valid_email(data['email']):
                current_app.logger.error(f'Invalid email format: {data["email"]}')
                return jsonify({'error': 'Invalid email format'}), 400
                
            if not is_valid_phone(data['phone_number']):
                current_app.logger.error(f'Invalid phone number format: {data["phone_number"]}')
                return jsonify({'error': 'Invalid phone number format. Please include country code (e.g., +1)'}), 400

            # Check if user already exists
            if User.query.filter_by(email=data['email']).first():
                current_app.logger.error(f'Email already registered: {data["email"]}')
                return jsonify({'error': 'Email already registered'}), 400
                
            if User.query.filter_by(phone_number=data['phone_number']).first():
                current_app.logger.error(f'Phone number already registered: {data["phone_number"]}')
                return jsonify({'error': 'Phone number already registered'}), 400

            # Create new user
            try:
                user = User(
                    email=data['email'],
                    username=data['username'],
                    phone_number=data['phone_number']
                )
                user.set_password(data['password'])
                
                # Generate email verification token
                verification_token = user.generate_email_verification_token()
                
                # Create OTP for phone verification
                otp = OTP(user.id)
                
                db.session.add(user)
                db.session.add(otp)
                db.session.commit()
                current_app.logger.info(f'User created successfully: {user.username}')

                # Send verification email
                try:
                    send_verification_email(user)
                    current_app.logger.info(f'Verification email sent to: {user.email}')
                except Exception as e:
                    current_app.logger.error(f'Failed to send verification email: {str(e)}')
                    # Continue with registration even if email fails
                    pass

                # Send OTP via SMS
                try:
                    send_otp_sms(user.phone_number, otp.otp_code)
                    current_app.logger.info(f'OTP sent to: {user.phone_number}')
                except Exception as e:
                    current_app.logger.error(f'Failed to send OTP SMS: {str(e)}')
                    # Continue with registration even if SMS fails
                    pass
                
                return jsonify({
                    'message': 'Registration successful. Please verify your email and phone number.',
                    'otp': otp.otp_code  # Remove this in production, only for testing
                }), 201

            except Exception as e:
                current_app.logger.error(f'Error creating user: {str(e)}')
                db.session.rollback()
                return jsonify({'error': 'Error creating user account'}), 500

        except Exception as e:
            current_app.logger.error(f'Registration error: {str(e)}')
            db.session.rollback()
            return jsonify({'error': 'An error occurred during registration. Please try again.'}), 500

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