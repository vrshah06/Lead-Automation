import logging
from datetime import datetime
from pymongo import MongoClient
from config import CONFIG

logger = logging.getLogger(__name__)

# Initialize MongoClient once
client = None
db = None
collection = None

def get_collection():
    global client, db, collection
    if client is None:
        try:
            client = MongoClient(CONFIG['MONGO_URI'])
            db = client[CONFIG['MONGO_DATABASE']]
            collection = db[CONFIG['MONGO_COLLECTION']]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return collection

def upsert_lead(lead):
    try:
        col = get_collection()
        
        mobile = lead.get('mobile_number')
        kid = lead.get('kid_name')
        
        if not mobile or not kid:
            logger.warning(f"Lead missing mobile_number or kid_name. Skipping upsert: {lead}")
            return False
            
        # Try to find existing lead
        filter_query = {"mobile_number": mobile, "kid_name": kid}
        update_doc = {"$set": lead}
        
        result = col.update_one(filter_query, update_doc, upsert=True)
        if result.upserted_id:
            logger.info(f"Inserted new lead {kid} ({mobile}) with id: {result.upserted_id}")
        else:
            logger.info(f"Updated existing lead {kid} ({mobile})")
        return True
    except Exception as e:
        logger.error(f"Exception calling MongoDB update_one: {e}")
        return False

def get_all_leads():
    try:
        col = get_collection()
        cursor = col.find({})
        
        records = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            records.append(doc)
            
        return records
    except Exception as e:
        logger.error(f"Exception calling MongoDB find: {e}")
        return []
