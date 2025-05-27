from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database() # This will get the database specified in MONGO_URI

# Ensure indexes for faster querying
db.users.create_index("email", unique=True)
db.produce_listings.create_index([("location", "2dsphere")]) # For geospatial queries
db.market_prices.create_index([("produce_type", 1), ("region", 1), ("date_recorded", -1)])
