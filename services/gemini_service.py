import requests
import json
from config import CONFIG
import logging

logger = logging.getLogger(__name__)

import time

def send_to_gemini(updated_leads):
    batch_size = 50
    all_summaries = []
    
    for idx, lead in enumerate(updated_leads):
        lead['temp_id'] = f"lead_{idx}"
    
    url = f"{CONFIG['GEMINI_API_URL']}?key={CONFIG['GEMINI_API_KEY']}"
    headers = {'Content-Type': 'application/json'}
    
    for i in range(0, len(updated_leads), batch_size):
        batch = updated_leads[i:i + batch_size]
        logger.info(f"Sending batch {i//batch_size + 1} to Gemini (Leads {i} to {i+len(batch)})...")
        
        prompt = f"""
        You are an AI assistant. I will provide you with a list of leads that have been recently added or updated.
        
        Updated Leads:
        {json.dumps(batch, indent=2)}
        
        Your task:
        1. For each lead, determine the number of calls made by checking the presence of dates in fields like 'call_1_date', 'call_2_date', 'call_3_date', 'call_4_date', etc.
        2. Prioritize the leads based on the number of calls (higher number of calls = higher priority). If leads have the same number of calls, use your best judgment to sort them.
        3. Generate a highly detailed summary of the lead's history (1-2 sentences). You MUST include the total number of calls made, a summary of what was discussed based on ALL the remarks (remarks_1, remarks_2, etc.), and their current lead_status.
        
        Output ONLY valid JSON in the following format. Do not include any markdown tags like ```json.
        [
          {{
            "id": "Put the temp_id of the lead here (e.g., lead_0)",
            "call_count": 2,
            "priority": 1,
            "summary": "2 calls made. Parent mentioned looking for August or October batch in the remarks. Currently marked as a Future Prospect."
          }}
        ]
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        while True:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    res_json = response.json()
                    text_content = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    try:
                        clean_text = text_content.replace('```json', '').replace('```', '').strip()
                        summary_array = json.loads(clean_text)
                        if isinstance(summary_array, list):
                            all_summaries.extend(summary_array)
                        else:
                            logger.error(f"Gemini response is not a list: {type(summary_array)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Gemini response as JSON: {e}")
                    
                    break  # Success, move to the next batch
                    
                elif response.status_code in [429, 503]:
                    logger.warning(f"Gemini API Error {response.status_code}: {response.text}. Rate limit or high demand hit. Pausing for 60 seconds to let quotas reset before resuming...")
                    time.sleep(60) # Wait a full minute for per-minute quotas to clear
                else:
                    logger.warning(f"Gemini API Error: {response.status_code} - {response.text}")
                    break # Unrecoverable error (e.g., 400 Bad Request, 403 Forbidden), skip this batch
                    
            except Exception as e:
                logger.error(f"Exception calling Gemini API: {e}. Retrying in 10 seconds...")
                time.sleep(10) # Wait before retry on network error
            
        # Sleep between successful batches to avoid hitting the rate limit
        if i + batch_size < len(updated_leads):
            time.sleep(8)
            
    # Map summaries by temp_id to original leads
    summary_map = {str(item.get('id', '')).strip(): item for item in all_summaries if item.get('id')}
    
    enriched_leads = []
    for lead in updated_leads:
        temp_id = str(lead.get('temp_id', '')).strip()
        gemini_info = summary_map.get(temp_id, {})
        
        # Merge gemini info into the original lead dictionary
        lead['call_count'] = gemini_info.get('call_count', 0)
        lead['priority'] = gemini_info.get('priority', 999) # Default low priority
        lead['summary'] = gemini_info.get('summary', 'No summary generated.')
        
        # Clean up temp_id
        if 'temp_id' in lead:
            del lead['temp_id']
            
        enriched_leads.append(lead)
        
    # Sort the enriched leads by priority (lowest number first, assuming 1 is highest priority)
    enriched_leads.sort(key=lambda x: (x.get('priority', 999) if isinstance(x.get('priority'), (int, float)) else 999))
    
    return enriched_leads

def generate_professional_email(prioritized_leads):
    if not prioritized_leads:
        return "<p>No updates or new leads to report today.</p>"
        
    closed_count = 0
    dead_count = 0
    future_leads = []
    followup_leads = []
    
    for lead in prioritized_leads:
        status = str(lead.get('lead_status', '')).strip().lower()
        kid_name = lead.get('kid_name', 'Unknown')
        parent = lead.get('parents_name', 'Unknown')
        mobile = lead.get('mobile_number', 'No Number')
        call_count = lead.get('call_count', 0)
        summary = lead.get('summary', '')
        priority = lead.get('priority', '-')
        
        row = f"<tr><td>{priority}</td><td>{kid_name}</td><td>{parent}</td><td>{mobile}</td><td>{call_count}</td><td>{summary}</td></tr>"
        
        if status == 'closed':
            closed_count += 1
        elif status == 'dead':
            dead_count += 1
        elif 'future prospect' in status:
            future_leads.append(row)
        else:
            # Default to Follow Up for any other active status
            followup_leads.append(row)
            
    html_lines = [
        "<html><head><style>",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; font-family: Arial, sans-serif; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f2f2f2; }",
        "h3 { font-family: Arial, sans-serif; color: #333; }",
        "ul { font-family: Arial, sans-serif; font-size: 16px; }",
        "</style></head><body>",
        "<p style='font-family: Arial, sans-serif;'>Hello Team,</p>",
        "<p style='font-family: Arial, sans-serif;'>Here is the prioritized list of updated leads:</p>",
        "<ul>",
        f"<li><b>Closed Leads:</b> {closed_count}</li>",
        f"<li><b>Dead Leads:</b> {dead_count}</li>",
        "</ul>"
    ]
    
    table_header = "<tr><th>Priority</th><th>Kid Name</th><th>Parent Name</th><th>Mobile Number</th><th>Calls</th><th>Summary of Update</th></tr>"
    
    if future_leads:
        html_lines.append(f"<h3>Future Prospect Leads ({len(future_leads)})</h3>")
        html_lines.append("<table>" + table_header)
        html_lines.extend(future_leads)
        html_lines.append("</table>")
        
    if followup_leads:
        html_lines.append(f"<h3>Follow Up Leads ({len(followup_leads)})</h3>")
        html_lines.append("<table>" + table_header)
        html_lines.extend(followup_leads)
        html_lines.append("</table>")
        
    html_lines.append("<p style='font-family: Arial, sans-serif;'><br>Best Regards,<br>Lead Automation Bot</p>")
    html_lines.append("</body></html>")
    
    return "\n".join(html_lines)
