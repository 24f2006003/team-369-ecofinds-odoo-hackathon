def get_otp_email_template(username, otp):
    """Generate HTML template for OTP verification email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .otp {{ font-size: 32px; font-weight: bold; text-align: center; 
                     background-color: #fff; padding: 20px; margin: 20px 0; 
                     border: 2px dashed #4CAF50; }}
            .footer {{ text-align: center; padding: 20px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Email Verification</h1>
            </div>
            <div class="content">
                <h2>Hello {username}!</h2>
                <p>Thank you for registering with us. Please use the following OTP to verify your email address:</p>
                <div class="otp">{otp}</div>
                <p><strong>Important:</strong></p>
                <ul>
                    <li>This OTP is valid for 10 minutes only</li>
                    <li>Do not share this OTP with anyone</li>
                    <li>If you didn't request this, please ignore this email</li>
                </ul>
            </div>
            <div class="footer">
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_password_reset_email_template(username, reset_link):
    """Generate HTML template for password reset email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 30px; background-color: #2196F3; 
                       color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; 
                        padding: 15px; border-radius: 5px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello {username}!</h2>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                <div class="warning">
                    <p><strong>Security Notice:</strong></p>
                    <ul>
                        <li>This link is valid for 1 hour only</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Your password will remain unchanged until you create a new one</li>
                    </ul>
                </div>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
            </div>
            <div class="footer">
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_email_template(username):
    """Generate HTML template for welcome email after successful registration"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ text-align: center; padding: 20px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Our Platform!</h1>
            </div>
            <div class="content">
                <h2>Hello {username}!</h2>
                <p>Congratulations! Your account has been successfully created and verified.</p>
                <p>You can now start using all the features of our platform:</p>
                <ul>
                    <li>Create and manage projects</li>
                    <li>Collaborate with team members</li>
                    <li>Track tasks and progress</li>
                    <li>Send and receive notifications</li>
                </ul>
                <p>Thank you for joining us!</p>
            </div>
            <div class="footer">
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """
