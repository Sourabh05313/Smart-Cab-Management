from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from app.utils.database import get_db
from bson import ObjectId
import os

bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
            current_user = get_db().users.find_one({'_id': ObjectId(data['user_id'])})
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    db = get_db()
    
    if db.users.find_one({'email': data['email']}):
        return jsonify({'message': 'Email already exists!'}), 400
        
    hashed_password = generate_password_hash(data['password'])
    user = {
        'username': data['username'],
        'email': data['email'],
        'password': hashed_password,
        'role': data['role'],
        'phone': data['phone'],
        'address': data['address'],
        'created_at': datetime.datetime.utcnow()
    }
    
    result = db.users.insert_one(user)
    user['_id'] = str(result.inserted_id)
    del user['password']
    
    return jsonify({
        'message': 'User registered successfully!',
        'user': user
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    db = get_db()
    
    user = db.users.find_one({'email': data['email']})
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401
        
    token = jwt.encode({
        'user_id': str(user['_id']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, os.getenv('SECRET_KEY'))
    
    user['_id'] = str(user['_id'])
    del user['password']
    
    return jsonify({
        'token': token,
        'user': user
    }), 200 