from flask import current_app, url_for, render_template
from flask_mail import Message
from twilio.rest import Client
from app import mail
import logging
from threading import Thread
import os
import re
import unicodedata
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def secure_filename(filename):
    """
    Custom secure filename function to replace Werkzeug's secure_filename.
    Sanitizes a filename to be safe for use in a filesystem.
    """
    # Convert to ASCII and normalize
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Ensure the filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    # Split into name and extension
    name, ext = os.path.splitext(filename)
    
    # Ensure the extension is safe
    ext = ext.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']:
        ext = ''
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"

def send_verification_email(to_email, subject, message):
    """Send a verification email to the user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('MAIL_DEFAULT_SENDER')
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        with smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT'))) as server:
            if os.getenv('MAIL_USE_TLS'):
                server.starttls()
            if os.getenv('MAIL_USERNAME'):
                server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_otp_sms(phone_number, otp):
    """Send OTP via SMS (placeholder for actual SMS service integration)"""
    # TODO: Implement actual SMS service integration
    print(f"Sending OTP {otp} to {phone_number}")
    return True 