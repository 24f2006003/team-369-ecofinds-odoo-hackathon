import base64
from email.message import EmailMessage
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_token(path, scopes):
    PATH = path
    SCOPES = scopes
    token = None

    if not os.path.exists(PATH):
        raise FileNotFoundError(f"Client secrets file not found at {PATH}. Please download it from Google Cloud Console.")

    if os.path.exists('token_creds.json'):
        token = Credentials.from_authorized_user_file('token_creds.json',
                                                      SCOPES)

    if not token or not token.valid:
        if token and token.expired and token.refresh_token:
            token.refresh(Request())
        else:
            print("Opening OAuth flow to get Gmail credentials...")
            flow = InstalledAppFlow.from_client_secrets_file(
                PATH, SCOPES)
            token = flow.run_local_server(port=0)

        # Saves the credentials for later use.
        with open('token_creds.json', 'w') as token_file:
            token_file.write(token.to_json())

    return token


def get_service(token_creds):

    try:
        service = build('gmail', 'v1', credentials=token_creds)
        return service

    except HttpError as error:
        print(f'An error occurred: {error}')


def get_gmail_credentials():
    """Get Gmail credentials, only called when needed"""
    cred_file_path = "client_secrets.json"
    scopes = ['https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.compose']
    
    try:
        return get_token(cred_file_path, scopes)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please download client_secrets.json from Google Cloud Console and place it in the project root.")
        return None
    except Exception as e:
        print(f"Error getting Gmail credentials: {e}")
        return None


def initialize_gmail_credentials():
    """Initialize Gmail credentials at app startup"""
    print("Initializing Gmail credentials...")
    token_creds = get_gmail_credentials()
    if token_creds:
        print("Gmail credentials initialized successfully!")
        return token_creds
    else:
        print("Failed to initialize Gmail credentials. Email functionality may not work.")
        return None


token_creds = None


def send_gmail_message(subject, reciepent_id,
                       message, service, sender_id="mymailid@gmail.com"):
    """
    Creates and sends a basic email message
    Return: Prints message ID and returns message object.
    """

    msg = str(message)

    try:
        message = EmailMessage()
        message.set_content(msg)

        message['To'] = reciepent_id
        message['From'] = sender_id
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }

        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None

    return send_message


if __name__ == '__main__':
    token_creds = get_gmail_credentials()
    send_gmail_message("myfriend@gmail.com", "Succces mail",
                       "myemailId@gmail.com", get_service(token_creds))
