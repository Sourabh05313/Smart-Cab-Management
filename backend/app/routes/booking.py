from flask import Blueprint, request, jsonify
from app.utils.database import get_db
from app.routes.auth import token_required
from bson import ObjectId
import datetime

bp = Blueprint('booking', __name__)

@bp.route('/', methods=['POST'])
@token_required
def create_booking(current_user):
    try:
        data = request.get_json()
        db = get_db()
        
        # Validate required fields
        required_fields = ['cab_id', 'pickup_location', 'drop_location', 'distance', 'travel_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Check if cab is available
        try:
            cab = db.cabs.find_one({'_id': ObjectId(data['cab_id'])})
        except:
            return jsonify({'message': 'Invalid cab ID format'}), 400
            
        if not cab:
            return jsonify({'message': 'Cab not found!'}), 404
            
        if cab['status'] != 'available':
            return jsonify({'message': 'Cab is not available!'}), 400
        
        # Parse travel date
        try:
            travel_date = datetime.datetime.strptime(data['travel_date'], '%Y-%m-%d %H:%M')
        except ValueError:
            return jsonify({'message': 'Invalid travel date format. Use YYYY-MM-DD HH:MM'}), 400
        
        booking = {
            'user_id': str(current_user['_id']),
            'cab_id': data['cab_id'],
            'pickup_location': data['pickup_location'],
            'drop_location': data['drop_location'],
            'distance': float(data['distance']),
            'fare': float(data['distance']) * float(cab['rate_per_km']),
            'status': 'pending',
            'booking_date': datetime.datetime.utcnow(),
            'travel_date': travel_date
        }
        
        result = db.bookings.insert_one(booking)
        booking['_id'] = str(result.inserted_id)
        
        # Update cab status
        db.cabs.update_one(
            {'_id': ObjectId(data['cab_id'])},
            {'$set': {'status': 'booked'}}
        )
        
        return jsonify({
            'message': 'Booking created successfully!',
            'booking': booking
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error creating booking: {str(e)}'}), 500

@bp.route('/user', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    try:
        db = get_db()
        bookings = list(db.bookings.find({'user_id': str(current_user['_id'])}))
        
        # Convert ObjectId to string and add cab details
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            cab = db.cabs.find_one({'_id': ObjectId(booking['cab_id'])})
            if cab:
                booking['cab_details'] = {
                    'brand': cab['brand'],
                    'model': cab['model'],
                    'registration_number': cab['registration_number']
                }
                
        return jsonify(bookings), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching bookings: {str(e)}'}), 500 