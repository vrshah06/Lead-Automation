import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'GOOGLE_SHEET_CREDENTIALS_FILE': os.environ.get('GOOGLE_SHEET_CREDENTIALS_FILE', 'credentials.json'),
    'SPREADSHEET_ID': os.environ.get('SPREADSHEET_ID', '17ou0ovQHhcEJXYRKb_SvszhXgP00_rXFqyyyofC7lA8'),
    'SHEET_NAME': os.environ.get('SHEET_NAME', 'Leads'),
    'DAYS_TO_FILTER': int(os.environ.get('DAYS_TO_FILTER', 15)),
    
    'MONGO_URI': os.environ.get('MONGO_URI'),
    'MONGO_DATABASE': os.environ.get('MONGO_DATABASE', 'LeadDB'),
    'MONGO_COLLECTION': os.environ.get('MONGO_COLLECTION', 'Leads'),
    
    'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
    'GEMINI_API_URL': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
    
    'SMTP_SERVER': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.environ.get('SMTP_PORT', 587)),
    'SENDER_EMAIL': os.environ.get('SENDER_EMAIL', 'vrshah0603@gmail.com'),
    'SENDER_PASSWORD': os.environ.get('SENDER_PASSWORD'),
    'RECEIVER_EMAIL': os.environ.get('RECEIVER_EMAIL', 'vrshah0603@gmail.com')
}
