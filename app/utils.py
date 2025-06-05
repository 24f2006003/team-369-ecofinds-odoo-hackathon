from flask import current_app, url_for, render_template
from flask_mail import Message
from twilio.rest import Client
from app import mail
import logging
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    """
    Send an email asynchronously.
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        text_body (str): Plain text version of the email
        html_body (str): HTML version of the email
    """
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Send email asynchronously
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

def send_complaint_notification(complaint, recipient_email, is_admin=False):
    """
    Send a notification email for complaint updates.
    
    Args:
        complaint (Complaint): The complaint object
        recipient_email (str): Email address of the recipient
        is_admin (bool): Whether the recipient is an admin
    """
    subject = f"Complaint Update - {complaint.reference_number}"
    
    # Render both HTML and text versions of the email
    html_body = render_template('email/complaint_notification.html',
                              complaint=complaint,
                              is_admin=is_admin)
    text_body = render_template('email/complaint_notification.txt',
                              complaint=complaint,
                              is_admin=is_admin)
    
    send_email(subject, [recipient_email], text_body, html_body)

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