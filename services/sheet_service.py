import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CONFIG
import logging

logger = logging.getLogger(__name__)

def get_sheet_data():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CONFIG['GOOGLE_SHEET_CREDENTIALS_FILE'], scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(CONFIG['SPREADSHEET_ID']).worksheet(CONFIG['SHEET_NAME'])
        
        records = sheet.get_all_records() # Automatically parses headers to keys
        # Normalize keys similar to JS version
        normalized_records = []
        for row in records:
            normalized_row = {str(k).strip().lower().replace(" ", "_"): v for k, v in row.items()}
            normalized_records.append(normalized_row)
            
        return normalized_records
    except Exception as e:
        logger.error(f"Error accessing Google Sheet: {e}")
        # In a real app with no credentials file yet, return empty list for safety during dev.
        return []
