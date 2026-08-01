from flask import Blueprint, request, jsonify
from app.utils.database import get_db
from app.routes.auth import token_required
from bson import ObjectId

bp = Blueprint('cab', __name__)

@bp.route('/', methods=['GET'])
def get_cabs():
    try:
        db = get_db()
        cabs = list(db.cabs.find())
        for cab in cabs:
            cab['_id'] = str(cab['_id'])
            # Add driver details if available
            if 'driver_id' in cab and cab['driver_id']:
                driver = db.users.find_one({'_id': ObjectId(cab['driver_id'])})
                if driver:
                    cab['driver'] = {
                        'name': driver['username'],
                        'phone': driver['phone']
                    }
        return jsonify(cabs), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching cabs: {str(e)}'}), 500

@bp.route('/<cab_id>', methods=['GET'])
def get_cab(cab_id):
    try:
        db = get_db()
        cab = db.cabs.find_one({'_id': ObjectId(cab_id)})
        if cab:
            cab['_id'] = str(cab['_id'])
            # Add driver details if available
            if 'driver_id' in cab and cab['driver_id']:
                driver = db.users.find_one({'_id': ObjectId(cab['driver_id'])})
                if driver:
                    cab['driver'] = {
                        'name': driver['username'],
                        'phone': driver['phone']
                    }
            return jsonify(cab), 200
        return jsonify({'message': 'Cab not found!'}), 404
    except:
        return jsonify({'message': 'Invalid cab ID format'}), 400

@bp.route('/', methods=['POST'])
@token_required
def add_cab(current_user):
    try:
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized access!'}), 403
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['brand', 'model', 'type', 'registration_number', 'driver_id', 'rate_per_km']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        db = get_db()
        
        # Check if driver exists
        try:
            driver = db.users.find_one({'_id': ObjectId(data['driver_id'])})
            if not driver or driver['role'] != 'driver':
                return jsonify({'message': 'Invalid driver ID or driver not found!'}), 400
        except:
            return jsonify({'message': 'Invalid driver ID format'}), 400
        
        cab = {
            'brand': data['brand'],
            'model': data['model'],
            'type': data['type'],
            'registration_number': data['registration_number'],
            'driver_id': data['driver_id'],
            'status': 'available',
            'rate_per_km': float(data['rate_per_km'])
        }
        
        result = db.cabs.insert_one(cab)
        cab['_id'] = str(result.inserted_id)
        
        return jsonify({
            'message': 'Cab added successfully!',
            'cab': cab
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error adding cab: {str(e)}'}), 500 