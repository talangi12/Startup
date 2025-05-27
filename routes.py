from flask import Blueprint, request, jsonify, session, redirect, url_for
from models import (
    create_user, find_user_by_email, verify_password, find_user_by_id,
    create_produce_listing, get_all_produce_listings, get_produce_listing_by_id,
    update_produce_listing, delete_produce_listing,
    add_market_price, get_market_prices,
    create_buyer_request, get_all_buyer_requests, get_buyer_request_by_id,
    update_buyer_request, delete_buyer_request
)
from services.sms_service import send_sms
from bson.objectid import ObjectId
from functools import wraps

# Create blueprints for modularity
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
produce_bp = Blueprint('produce', __name__, url_prefix='/api/produce')
market_bp = Blueprint('market', __name__, url_prefix='/api/market')
buyer_bp = Blueprint('buyer', __name__, url_prefix='/api/buyer')

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized"}), 401
        user = find_user_by_id(session['user_id'])
        if not user or user.get('user_type') != 'farmer':
            return jsonify({"message": "Forbidden: Farmer access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized"}), 401
        user = find_user_by_id(session['user_id'])
        if not user or user.get('user_type') != 'buyer':
            return jsonify({"message": "Forbidden: Buyer access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Auth Routes ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    required_fields = ['email', 'password', 'user_type', 'contact_number', 'location', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    if find_user_by_email(data['email']):
        return jsonify({"message": "User with this email already exists"}), 409

    try:
        result = create_user(data)
        user_id = str(result.inserted_id)
        # Automatically log in after registration
        session['user_id'] = user_id
        session['user_type'] = data['user_type']
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = find_user_by_email(email)
    if not user or not verify_password(user['password'], password):
        return jsonify({"message": "Invalid credentials"}), 401

    session['user_id'] = str(user['_id'])
    session['user_type'] = user.get('user_type')
    return jsonify({"message": "Logged in successfully", "user_type": user.get('user_type')}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    user = find_user_by_id(session['user_id'])
    if user:
        # Remove sensitive data like password hash before sending
        user.pop('password', None)
        user['_id'] = str(user['_id']) # Convert ObjectId to string
        return jsonify(user), 200
    return jsonify({"message": "User not found"}), 404

# --- Produce Routes (Farmers) ---
@produce_bp.route('/', methods=['POST'])
@farmer_required
def add_produce():
    data = request.json
    required_fields = ['produce_type', 'quantity', 'unit', 'price_per_unit', 'available_from', 'available_until']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    data['farmer_id'] = session['user_id'] # Link listing to farmer
    
    try:
        result = create_produce_listing(data)
        return jsonify({"message": "Produce listing added successfully", "listing_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to add listing: {str(e)}"}), 500

@produce_bp.route('/', methods=['GET'])
@login_required # Anyone logged in can view all produce
def get_produce():
    listings = get_all_produce_listings()
    for listing in listings:
        listing['_id'] = str(listing['_id'])
        # Optionally, fetch farmer details if needed
    return jsonify(listings), 200

@produce_bp.route('/<id>', methods=['GET'])
@login_required
def get_single_produce(id):
    listing = get_produce_listing_by_id(id)
    if listing:
        listing['_id'] = str(listing['_id'])
        return jsonify(listing), 200
    return jsonify({"message": "Listing not found"}), 404

@produce_bp.route('/<id>', methods=['PUT'])
@farmer_required
def update_produce(id):
    data = request.json
    listing = get_produce_listing_by_id(id)
    if not listing:
        return jsonify({"message": "Listing not found"}), 404
    
    # Ensure farmer can only update their own listings
    if listing['farmer_id'] != session['user_id']:
        return jsonify({"message": "Forbidden: You can only update your own listings"}), 403

    try:
        update_produce_listing(id, data)
        return jsonify({"message": "Listing updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to update listing: {str(e)}"}), 500

@produce_bp.route('/<id>', methods=['DELETE'])
@farmer_required
def delete_produce(id):
    listing = get_produce_listing_by_id(id)
    if not listing:
        return jsonify({"message": "Listing not found"}), 404
    
    if listing['farmer_id'] != session['user_id']:
        return jsonify({"message": "Forbidden: You can only delete your own listings"}), 403

    try:
        delete_produce_listing(id)
        return jsonify({"message": "Listing deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to delete listing: {str(e)}"}), 500

# --- Market Price Routes (Admin/Data Entry - simplified for now) ---
@market_bp.route('/', methods=['POST'])
@login_required # Assume only admins can add prices for now, or specific roles
def add_price():
    data = request.json
    required_fields = ['produce_type', 'region', 'price', 'unit']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    # You might want to check for admin/data entry role here
    # if session.get('user_type') != 'admin':
    #     return jsonify({"message": "Forbidden: Admin access required"}), 403

    try:
        result = add_market_price(data)
        return jsonify({"message": "Market price added successfully", "price_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to add price: {str(e)}"}), 500

@market_bp.route('/', methods=['GET'])
@login_required
def get_prices():
    produce_type = request.args.get('produce_type')
    region = request.args.get('region')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    prices = get_market_prices(produce_type, region, date_from, date_to)
    for price in prices:
        price['_id'] = str(price['_id'])
    return jsonify(prices), 200

# --- Buyer Request Routes ---
@buyer_bp.route('/', methods=['POST'])
@buyer_required
def add_buyer_request():
    data = request.json
    required_fields = ['produce_type', 'quantity_needed', 'unit', 'delivery_location']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    data['buyer_id'] = session['user_id'] # Link request to buyer
    
    try:
        result = create_buyer_request(data)
        return jsonify({"message": "Buyer request added successfully", "request_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to add request: {str(e)}"}), 500

@buyer_bp.route('/', methods=['GET'])
@login_required # Anyone logged in can view requests
def get_requests():
    requests = get_all_buyer_requests()
    for req in requests:
        req['_id'] = str(req['_id'])
    return jsonify(requests), 200

@buyer_bp.route('/<id>', methods=['GET'])
@login_required
def get_single_request(id):
    req = get_buyer_request_by_id(id)
    if req:
        req['_id'] = str(req['_id'])
        return jsonify(req), 200
    return jsonify({"message": "Request not found"}), 404

@buyer_bp.route('/<id>', methods=['PUT'])
@buyer_required
def update_request(id):
    data = request.json
    req = get_buyer_request_by_id(id)
    if not req:
        return jsonify({"message": "Request not found"}), 404
    
    if req['buyer_id'] != session['user_id']:
        return jsonify({"message": "Forbidden: You can only update your own requests"}), 403

    try:
        update_buyer_request(id, data)
        return jsonify({"message": "Request updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to update request: {str(e)}"}), 500

@buyer_bp.route('/<id>', methods=['DELETE'])
@buyer_required
def delete_request(id):
    req = get_buyer_request_by_id(id)
    if not req:
        return jsonify({"message": "Request not found"}), 404
    
    if req['buyer_id'] != session['user_id']:
        return jsonify({"message": "Forbidden: You can only delete your own requests"}), 403

    try:
        delete_buyer_request(id)
        return jsonify({"message": "Request deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to delete request: {str(e)}"}), 500

# --- Matching and Alert Logic (Conceptual - requires more sophisticated algorithm) ---
# This would typically be a background task or a more complex endpoint
@produce_bp.route('/<listing_id>/match', methods=['GET'])
@farmer_required
def find_matches_for_listing(listing_id):
    listing = get_produce_listing_by_id(listing_id)
    if not listing:
        return jsonify({"message": "Listing not found"}), 404
    
    if listing['farmer_id'] != session['user_id']:
        return jsonify({"message": "Forbidden"}), 403

    # Basic matching logic: Find buyer requests for the same produce type
    potential_matches = []
    buyer_requests = get_all_buyer_requests()
    for req in buyer_requests:
        if req['produce_type'] == listing['produce_type'] and req['is_active']:
            # More complex logic here: proximity, quantity match, price range
            # For now, just matching by type
            potential_matches.append({
                "request_id": str(req['_id']),
                "buyer_id": req['buyer_id'],
                "quantity_needed": req['quantity_needed'],
                "delivery_location": req['delivery_location'],
                "target_price": req.get('target_price_per_unit')
            })
    
    # In a real scenario, you'd trigger SMS alerts here or via a background job
    # For demonstration, let's say a buyer expresses interest
    # For now, just return potential matches
    return jsonify({"message": "Potential matches found", "matches": potential_matches}), 200


@market_bp.route('/send_price_alert', methods=['POST'])
@login_required # Restricted to admin or a background task
def send_price_alert_to_farmers():
    data = request.json
    produce_type = data.get('produce_type')
    region = data.get('region')
    price = data.get('price')
    unit = data.get('unit')

    if not all([produce_type, region, price, unit]):
        return jsonify({"message": "Missing required fields for alert"}), 400

    # Find farmers who list this produce or are in this region
    # This is highly simplified; a real system would have more complex filtering
    farmers_to_alert = find_user_by_email('farmer@example.com') # Placeholder: find all farmers, or farmers interested in this produce
    
    # In a real app, you'd iterate through relevant farmers
    # For now, let's simulate sending to a single user (e.g., the current user if they are a farmer)
    user_to_alert = find_user_by_id(session['user_id'])
    if user_to_alert and user_to_alert.get('user_type') == 'farmer':
        message = f"Agritech Alert: Latest market price for {produce_type} in {region} is {price} {unit}."
        if send_sms(user_to_alert['contact_number'], message):
            return jsonify({"message": f"Price alert sent to {user_to_alert['email']}"}), 200
        else:
            return jsonify({"message": "Failed to send SMS alert"}), 500
    
    return jsonify({"message": "No relevant farmers found to send alert or not a farmer"}), 404

