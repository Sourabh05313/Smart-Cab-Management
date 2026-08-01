from flask import Blueprint, jsonify, request, session
from ..utils.database import get_db_connection
import bcrypt
from functools import wraps

bp = Blueprint('driver', __name__, url_prefix='/api/driver')

def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'driver_id' not in session:
            return jsonify({'error': 'Driver authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/register', methods=['POST'])
def driver_register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    license_number = data.get('license_number')
    
    if not all([name, email, password, license_number]):
        return jsonify({'error': 'Name, email, password and license number are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT driver_id FROM driver_registration WHERE driver_email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert new driver
        cursor.execute("""
            INSERT INTO driver_registration (driver_name, driver_email, driver_password, driver_phone, license_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, hashed_password, phone, license_number))
        
        conn.commit()
        return jsonify({'message': 'Driver registered successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/login', methods=['POST'])
def driver_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM driver_registration WHERE driver_email = %s", (email,))
        driver = cursor.fetchone()
        
        if driver and bcrypt.checkpw(password.encode('utf-8'), driver['driver_password'].encode('utf-8')):
            session['driver_id'] = driver['driver_id']
            session['driver_name'] = driver['driver_name']
            return jsonify({
                'message': 'Login successful',
                'driver': {
                    'id': driver['driver_id'],
                    'name': driver['driver_name'],
                    'email': driver['driver_email']
                }
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/logout', methods=['POST'])
def driver_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/session', methods=['GET'])
def check_driver_session():
    if 'driver_id' in session:
        return jsonify({
            'authenticated': True,
            'driver': {
                'id': session['driver_id'],
                'name': session['driver_name']
            }
        })
    return jsonify({'authenticated': False}) 