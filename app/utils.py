from flask import current_app, url_for
from flask_mail import Message
from twilio.rest import Client
from app import mail
import logging

def send_verification_email(user):
    """Send email verification link to user."""
    try:
        msg = Message(
            'Verify your email address',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        msg.body = f'''To verify your email address, visit the following link:
{current_app.config['BASE_URL']}/verify-email/{user.email_verification_token}

If you did not make this request then simply ignore this email.
'''
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send verification email: {str(e)}')
        return False

def send_otp_sms(phone_number, otp_code):
    """Send OTP via SMS."""
    try:
        # In development, just log the OTP
        current_app.logger.info(f'OTP for {phone_number}: {otp_code}')
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send OTP SMS: {str(e)}')
        return False 