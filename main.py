import logging
from datetime import datetime, timedelta
from config import CONFIG
from services.sheet_service import get_sheet_data
from services.mongo_service import upsert_lead, get_all_leads
from services.gemini_service import send_to_gemini, generate_professional_email
from services.email_service import send_email

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_recent_lead(lead, days=15):
    date_fields = ['date', 'call_1_date', 'call_2_date', 'call_3_date', 'call_4_date']
    cutoff = datetime.now() - timedelta(days=days)
    current_year = datetime.now().year
    
    for field in date_fields:
        val = str(lead.get(field, '')).strip()
        if val:
            try:
                # Attempt to parse date like '30-Jun' or '8-Jul'
                dt = datetime.strptime(f"{val}-{current_year}", "%d-%b-%Y")
                
                # If date is in the future (e.g. next year's date parsed in current year), 
                # or date is recent, consider it valid.
                if dt >= cutoff:
                    return True
            except ValueError:
                pass # Ignore unparseable dates
                
    return False

def main():
    logger.info("Starting Lead Automation Flow (Python)...")
    
    try:
        # Fetch current leads from Google Sheet
        current_leads_raw = get_sheet_data()
        
        # Filter out empty rows (where mobile_number and kid_name are both completely blank)
        current_leads = []
        for lead in current_leads_raw:
            if str(lead.get('mobile_number', '')).strip() or str(lead.get('kid_name', '')).strip():
                current_leads.append(lead)
        
        if not current_leads:
            logger.info("No records found in sheet. Exiting.")
            return

        # Fetch previous leads from MongoDB
        previous_leads = get_all_leads()
        
        # Compare current_leads and previous_leads
        # We identify a lead by mobile_number and kid_name
        prev_dict = {
            f"{lead.get('mobile_number', '')}_{lead.get('kid_name', '')}": lead
            for lead in previous_leads if lead.get('mobile_number') and lead.get('kid_name')
        }
        
        # Identify new or updated leads
        updated_leads = []
        days_to_filter = CONFIG.get('DAYS_TO_FILTER', 15)
        
        for lead in current_leads:
            key = f"{lead.get('mobile_number', '')}_{lead.get('kid_name', '')}"
            if key not in prev_dict:
                # New Lead
                if is_recent_lead(lead, days=days_to_filter):
                    updated_leads.append(lead)
            else:
                # Existing Lead - check for modifications
                prev_lead = prev_dict[key]
                # Compare relevant fields. Remove MongoDB ID for comparison
                current_for_compare = {k: v for k, v in lead.items() if k != '_id'}
                prev_for_compare = {k: v for k, v in prev_lead.items() if k != '_id'}
                
                if current_for_compare != prev_for_compare:
                    if is_recent_lead(lead, days=days_to_filter):
                        updated_leads.append(lead)
                        logger.info(f"Updated existing lead {lead.get('kid_name', '')} ({lead.get('mobile_number', '')})")
        
        if not updated_leads:
            logger.info("No updated or new leads found. Exiting.")
            return
            
        logger.info(f"Found {len(updated_leads)} total new or updated leads.")
        
        # Filter leads to only send Follow Up / Future Prospect to Gemini
        gemini_leads = []
        direct_leads = []
        
        for lead in updated_leads:
            status = str(lead.get('lead_status', '')).strip().lower()
            if status in ['closed', 'dead']:
                direct_leads.append(lead)
            else:
                gemini_leads.append(lead)
                
        logger.info(f"Sending {len(gemini_leads)} active leads to Gemini API. Bypassing API for {len(direct_leads)} Closed/Dead leads.")
        
        # Send only active leads to Gemini
        if gemini_leads:
            gemini_summary = send_to_gemini(gemini_leads)
        else:
            gemini_summary = []
            
        # Re-combine with the closed/dead leads so they get counted in the email
        final_leads_for_email = gemini_summary + direct_leads
        
        # Generate Email
        email_body = generate_professional_email(final_leads_for_email)
        
        if email_body:
            send_email("Lead Summary and Prioritization Report", email_body)
            logger.info("Email sent successfully.")
        else:
            logger.warning("Failed to generate email body.")
            
        # Upsert current leads to MongoDB for next time
        for lead in current_leads:
            upsert_lead(lead)
            
        logger.info("Automation completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in main flow: {e}")

if __name__ == "__main__":
    main()

