from flask import Flask
from flask_session import Session # For session management
from config import Config
from routes import auth_bp, produce_bp, market_bp, buyer_bp
from database import db # Ensure database connection is initialized

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Session
Session(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(produce_bp)
app.register_blueprint(market_bp)
app.register_blueprint(buyer_bp)

@app.route('/')
def index():
    return "Agritech Market Match Backend is Running!"

if __name__ == '__main__':
    # Ensure MongoDB indexes are created/updated on startup
    # (This is handled in database.py when 'db' is accessed)
    print("Connecting to MongoDB and ensuring indexes...")
    # Accessing 'db' ensures the connection and index creation happens
    # You might want a more explicit check or migration system for production
    db.users.find_one({}) # A simple query to force connection

    app.run(debug=True, port=5000) # debug=True for development, set to False for production
