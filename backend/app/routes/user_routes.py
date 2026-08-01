from flask import Blueprint, jsonify, request, session
from ..utils.database import get_db_connection
import bcrypt
from functools import wraps
import mysql.connector

bp = Blueprint('user', __name__, url_prefix='/api/user')

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'User authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/register', methods=['POST'])
def user_register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        address = data.get('address')
        
        if not all([name, email, password]):
            return jsonify({'error': 'Name, email and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT user_id FROM user_registration WHERE user_email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'error': 'Email already registered'}), 400
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insert new user
            cursor.execute("""
                INSERT INTO user_registration (user_name, user_email, user_password, user_phone, user_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, hashed_password, phone, address))
            
            conn.commit()
            return jsonify({'message': 'User registered successfully'})
            
        except mysql.connector.Error as err:
            print(f"MySQL Error: {err}")
            return jsonify({'error': f'Database error: {err.msg}'}), 500
        except Exception as e:
            print(f"Error in user registration: {str(e)}")
            return jsonify({'error': 'Failed to register user'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error in registration: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/login', methods=['POST'])
def user_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email and password are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check if user exists
            cursor.execute("SELECT * FROM user_registration WHERE user_email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'No account found with this email address'
                }), 401
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['user_password'].encode('utf-8')):
                # Successful login
                session['user_id'] = user['user_id']
                session['user_name'] = user['user_name']
                return jsonify({
                    'message': 'Login successful',
                    'user': {
                        'id': user['user_id'],
                        'name': user['user_name'],
                        'email': user['user_email']
                    }
                })
            else:
                # Failed login attempt
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Incorrect password'
                }), 401
                
        except Exception as e:
            print(f"Error in user login: {str(e)}")
            return jsonify({
                'error': 'Login failed',
                'message': 'An error occurred while trying to log in'
            }), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error in login: {str(e)}")
        return jsonify({
            'error': 'Login failed',
            'message': 'An unexpected error occurred'
        }), 500

@bp.route('/logout', methods=['POST'])
def user_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/session', methods=['GET'])
def check_user_session():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name']
            }
        })
    return jsonify({'authenticated': False})

@bp.route('/profile', methods=['GET'])
@user_required
def get_profile():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT user_name, user_email, user_phone, user_address 
                FROM user_registration 
                WHERE user_id = %s
            """, (session['user_id'],))
            
            user = cursor.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            return jsonify(user)
            
        except Exception as e:
            print(f"Error getting profile: {str(e)}")
            return jsonify({'error': 'Failed to get profile'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error in get profile: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/profile', methods=['PUT'])
@user_required
def update_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get current user data
            cursor.execute("""
                SELECT user_password 
                FROM user_registration 
                WHERE user_id = %s
            """, (session['user_id'],))
            
            current_user = cursor.fetchone()
            if not current_user:
                return jsonify({'error': 'User not found'}), 404
            
            # Build update query
            update_fields = []
            update_values = []
            
            if 'user_name' in data:
                update_fields.append("user_name = %s")
                update_values.append(data['user_name'])
            
            if 'user_phone' in data:
                update_fields.append("user_phone = %s")
                update_values.append(data['user_phone'])
            
            if 'user_address' in data:
                update_fields.append("user_address = %s")
                update_values.append(data['user_address'])
            
            # Handle password change if provided
            if 'current_password' in data and 'new_password' in data:
                # Verify current password
                if not bcrypt.checkpw(data['current_password'].encode('utf-8'), current_user['user_password'].encode('utf-8')):
                    return jsonify({'error': 'Current password is incorrect'}), 400
                
                # Hash new password
                hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
                update_fields.append("user_password = %s")
                update_values.append(hashed_password)
            
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            # Add user_id to values
            update_values.append(session['user_id'])
            
            # Build and execute update query
            update_query = f"""
                UPDATE user_registration 
                SET {', '.join(update_fields)}
                WHERE user_id = %s
            """
            
            cursor.execute(update_query, update_values)
            conn.commit()
            
            return jsonify({'message': 'Profile updated successfully'})
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            conn.rollback()
            return jsonify({'error': 'Failed to update profile'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error in update profile: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500 