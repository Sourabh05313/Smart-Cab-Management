from flask import Blueprint, request, jsonify
from app.utils.database import get_db
from app.routes.auth import token_required
from bson import ObjectId

bp = Blueprint('admin', __name__)

@bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized access!'}), 403
            
        db = get_db()
        users = list(db.users.find())
        for user in users:
            user['_id'] = str(user['_id'])
            del user['password']
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching users: {str(e)}'}), 500

@bp.route('/bookings', methods=['GET'])
@token_required
def get_all_bookings(current_user):
    try:
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized access!'}), 403
            
        db = get_db()
        bookings = list(db.bookings.find())
        
        # Convert ObjectId to string and add user and cab details
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            
            # Add user details
            user = db.users.find_one({'_id': ObjectId(booking['user_id'])})
            if user:
                booking['user'] = {
                    'name': user['username'],
                    'email': user['email'],
                    'phone': user['phone']
                }
            
            # Add cab details
            cab = db.cabs.find_one({'_id': ObjectId(booking['cab_id'])})
            if cab:
                booking['cab'] = {
                    'brand': cab['brand'],
                    'model': cab['model'],
                    'registration_number': cab['registration_number']
                }
                
        return jsonify(bookings), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching bookings: {str(e)}'}), 500

@bp.route('/cabs', methods=['GET'])
@token_required
def get_all_cabs(current_user):
    try:
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized access!'}), 403
            
        db = get_db()
        cabs = list(db.cabs.find())
        
        # Convert ObjectId to string and add driver details
        for cab in cabs:
            cab['_id'] = str(cab['_id'])
            
            # Add driver details
            if 'driver_id' in cab and cab['driver_id']:
                driver = db.users.find_one({'_id': ObjectId(cab['driver_id'])})
                if driver:
                    cab['driver'] = {
                        'name': driver['username'],
                        'email': driver['email'],
                        'phone': driver['phone']
                    }
                    
        return jsonify(cabs), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching cabs: {str(e)}'}), 500 