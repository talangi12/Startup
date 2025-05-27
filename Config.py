import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here') # IMPORTANT: Change this!
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/market_match_db')
    SESSION_TYPE = 'filesystem' # Or 'mongodb' for persistent sessions
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session_data')
    
    # SMS Service Configuration (e.g., Twilio)
    SMS_ACCOUNT_SID = os.getenv('SMS_ACCOUNT_SID')
    SMS_AUTH_TOKEN = os.getenv('SMS_AUTH_TOKEN')
    SMS_FROM_NUMBER = os.getenv('SMS_FROM_NUMBER') # Your Twilio phone number

