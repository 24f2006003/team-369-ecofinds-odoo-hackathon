from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, OTP
import re
from datetime import datetime, timedelta
from app.utils import send_verification_email, send_otp_sms, secure_filename
from flask_babel import _
from app.auth.google_auth import verify_google_token
import secrets
import os
from werkzeug.urls import url_parse
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset_email

from app.auth import bp

def is_valid_phone(phone):
    # Basic phone number validation (can be enhanced based on requirements)
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def is_valid_email(email):
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone_number = request.form.get('phone_number')
        
        # Validate form data
        if not all([email, username, password, confirm_password, phone_number]):
            flash(_('Please fill in all fields.'), 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash(_('Passwords do not match.'), 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered.'), 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash(_('Username already taken.'), 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            email=email,
            username=username,
            phone_number=phone_number
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Generate and send verification email
            token = user.generate_email_verification_token()
            send_verification_email(user.email, token)
            
            flash(_('Registration successful! Please check your email to verify your account.'), 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(_('An error occurred during registration. Please try again.'), 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html')

@bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if user is None:
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('main.index'))
    user.is_email_verified = True
    user.email_verification_token = None
    db.session.commit()
    flash('Your email has been verified!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/verify-phone', methods=['GET', 'POST'])
def verify_phone():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        otp = OTP.query.filter_by(
            user_id=current_user.id,
            otp_code=otp_code,
            is_used=False
        ).first()
        
        if otp and otp.is_valid():
            current_user.is_phone_verified = True
            otp.is_used = True
            db.session.commit()
            flash('Your phone number has been verified!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid or expired OTP code.', 'danger')
    
    # Generate new OTP
    otp = OTP(current_user.id)
    db.session.add(otp)
    db.session.commit()
    
    # TODO: Send OTP via SMS
    flash(f'OTP sent to your phone number: {otp.otp_code}', 'info')
    
    return render_template('auth/verify_phone.html', title='Verify Phone Number')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/resend-otp', methods=['POST'])
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

@bp.route('/google-signin', methods=['POST'])
def google_signin():
    try:
        data = request.get_json()
        if not data or 'credential' not in data:
            current_app.logger.error("No credential provided in Google sign-in request")
            return jsonify({'success': False, 'error': 'No credential provided'}), 400

        # Verify the Google token
        user_info = verify_google_token(data['credential'])
        if not user_info:
            current_app.logger.error("Invalid Google token in sign-in request")
            return jsonify({'success': False, 'error': 'Invalid Google token'}), 401

        # Check if user exists
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            try:
                # Create new user
                user = User(
                    email=user_info['email'],
                    username=user_info.get('name', user_info['email'].split('@')[0]),
                    is_email_verified=True,  # Google emails are verified
                    is_phone_verified=False  # Phone verification still required
                )
                db.session.add(user)
                db.session.commit()
                current_app.logger.info(f"Created new user from Google sign-in: {user.email}")
            except Exception as e:
                current_app.logger.error(f"Error creating user from Google sign-in: {str(e)}")
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Error creating user account'}), 500

        # Log in the user
        login_user(user)
        current_app.logger.info(f"User logged in via Google: {user.email}")
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('main.index')
        })

    except Exception as e:
        current_app.logger.error(f'Google sign-in error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile update
        current_user.username = request.form.get('username')
        current_user.phone_number = request.form.get('phone_number')
        
        # Handle profile picture upload
        profile_pic = request.files.get('profile_pic')
        if profile_pic:
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(profile_pic_path)
            current_user.profile_pic_url = url_for('static', filename=f'uploads/{filename}')
        
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', title='Profile') 