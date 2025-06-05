import base64
from email.message import EmailMessage
from .gmail import get_service, get_gmail_credentials
from .validation import validate_email

def send_email(subject, recipients, text_body, html_body):
    """
    Send email using Gmail API
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        text_body (str): Plain text body (can be empty)
        html_body (str): HTML body content
    
    Returns:
        bool: True if all emails sent successfully, False otherwise
    """
    try:
        # Validate all email addresses first
        invalid_emails = [email for email in recipients if not validate_email(email)]
        if invalid_emails:
            print(f"Invalid email addresses found: {invalid_emails}")
            return False
        
        token_creds = get_gmail_credentials()
        if not token_creds:
            print("Gmail credentials not available. Cannot send email.")
            return False
            
        service = get_service(token_creds)
        if not service:
            print("Failed to get Gmail service")
            return False
        
        success_count = 0
        
        # Send email to each recipient
        for recipient in recipients:
            try:
                message = EmailMessage()
                
                if html_body:
                    message.set_content(text_body or "")  # Set plain text as fallback
                    message.add_alternative(html_body, subtype='html')
                else:
                    message.set_content(text_body or "")
                    
                message['To'] = recipient
                message['From'] = "arnavl3110@gmail.com"
                message['Subject'] = subject

                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                # Create message body for API
                create_message = {
                    'raw': encoded_message
                }
                
                # Send message
                result = service.users().messages().send(
                    userId="me", 
                    body=create_message
                ).execute()
                
                print(f'Email sent to {recipient}. Message ID: {result["id"]}')
                success_count += 1
                
            except Exception as e:
                print(f'Failed to send email to {recipient}: {e}')
        
        return success_count == len(recipients)
        
    except Exception as e:
        print(f'Error in send_email function: {e}')
        return False