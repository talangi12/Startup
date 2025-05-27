import os
# from twilio.rest import Client # Uncomment if using Twilio
from config import Config

def send_sms(to_number, message):
    # This is a placeholder. You'd integrate with a real SMS API here (e.g., Twilio, Africa's Talking)
    # Ensure to handle country codes properly for international numbers.
    # For Kenya, numbers typically start with 07 or +2547
    
    # Example using Twilio (requires twilio-python library and credentials in .env)
    # try:
    #     client = Client(Config.SMS_ACCOUNT_SID, Config.SMS_AUTH_TOKEN)
    #     message = client.messages.create(
    #         to=to_number,
    #         from_=Config.SMS_FROM_NUMBER,
    #         body=message
    #     )
    #     print(f"SMS sent to {to_number}: {message.sid}")
    #     return True
    # except Exception as e:
    #     print(f"Error sending SMS to {to_number}: {e}")
    #     return False
    
    print(f"--- SIMULATING SMS SEND ---")
    print(f"To: {to_number}")
    print(f"Message: {message}")
    print(f"---------------------------")
    return True # Simulate success

# Example usage (for testing)
if __name__ == "__main__":
    # Ensure you have a valid phone number and Twilio credentials in .env for real testing
    # send_sms("+2547XXXXXXXX", "Test alert from Agritech Market Match!") 
    pass
from database import db
from datetime import datetime
from bson.objectid import ObjectId # For unique MongoDB IDs
import hashlib # For password hashing

# --- User Management ---
def create_user(user_data):
    user_data['password'] = hashlib.sha256(user_data['password'].encode()).hexdigest() # Hash password
    user_data['created_at'] = datetime.utcnow()
    user_data['user_type'] = user_data.get('user_type', 'farmer') # Default to farmer
    return db.users.insert_one(user_data)

def find_user_by_email(email):
    return db.users.find_one({"email": email})

def find_user_by_id(user_id):
    return db.users.find_one({"_id": ObjectId(user_id)})

def verify_password(hashed_password, provided_password):
    return hashed_password == hashlib.sha256(provided_password.encode()).hexdigest()

# --- Produce Listing Management ---
def create_produce_listing(listing_data):
    listing_data['created_at'] = datetime.utcnow()
    listing_data['updated_at'] = datetime.utcnow()
    listing_data['is_active'] = True
    return db.produce_listings.insert_one(listing_data)

def get_all_produce_listings():
    return list(db.produce_listings.find({"is_active": True}))

def get_produce_listing_by_id(listing_id):
    return db.produce_listings.find_one({"_id": ObjectId(listing_id)})

def update_produce_listing(listing_id, update_data):
    update_data['updated_at'] = datetime.utcnow()
    return db.produce_listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": update_data}
    )

def delete_produce_listing(listing_id):
    return db.produce_listings.delete_one({"_id": ObjectId(listing_id)})

# --- Market Price Data ---
def add_market_price(price_data):
    price_data['date_recorded'] = datetime.utcnow().date().isoformat() # Store as ISO date string
    return db.market_prices.insert_one(price_data)

def get_market_prices(produce_type=None, region=None, date_from=None, date_to=None):
    query = {}
    if produce_type:
        query['produce_type'] = produce_type
    if region:
        query['region'] = region
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query['$gte'] = date_from
        if date_to:
            date_query['$lte'] = date_to
        query['date_recorded'] = date_query
    return list(db.market_prices.find(query).sort("date_recorded", -1))

# --- Buyer Requests ---
def create_buyer_request(request_data):
    request_data['created_at'] = datetime.utcnow()
    request_data['is_active'] = True
    return db.buyer_requests.insert_one(request_data)

def get_all_buyer_requests():
    return list(db.buyer_requests.find({"is_active": True}))

def get_buyer_request_by_id(request_id):
    return db.buyer_requests.find_one({"_id": ObjectId(request_id)})

def update_buyer_request(request_id, update_data):
    return db.buyer_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )

def delete_buyer_request(request_id):
    return db.buyer_requests.delete_one({"_id": ObjectId(request_id)})

