from flask import Blueprint, jsonify, request, session
from ..utils.database import get_db_connection
import bcrypt
from functools import wraps

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'No data provided'
            }), 400
            
        admin_email = data.get('admin_email')
        admin_password = data.get('admin_password')
        
        if not admin_email or not admin_password:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Email and password are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get admin details
            cursor.execute("""
                SELECT admin_id, admin_name, admin_email, admin_password 
                FROM admin_registration 
                WHERE admin_email = %s
            """, (admin_email,))
            
            admin = cursor.fetchone()
            
            if not admin:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Invalid email or password'
                }), 401
            
            # Verify password
            if admin_password == 'admin123':  # Default admin password
                # Set session
                session['admin_id'] = admin['admin_id']
                session['admin_name'] = admin['admin_name']
                session['is_admin'] = True
                
                return jsonify({
                    'message': 'Login successful',
                    'admin': {
                        'id': admin['admin_id'],
                        'name': admin['admin_name'],
                        'email': admin['admin_email']
                    }
                })
            else:
                # For non-default password, verify with bcrypt
                stored_password = admin['admin_password']
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')
                    
                if bcrypt.checkpw(admin_password.encode('utf-8'), stored_password):
                    # Set session
                    session['admin_id'] = admin['admin_id']
                    session['admin_name'] = admin['admin_name']
                    session['is_admin'] = True
                    
                    return jsonify({
                        'message': 'Login successful',
                        'admin': {
                            'id': admin['admin_id'],
                            'name': admin['admin_name'],
                            'email': admin['admin_email']
                        }
                    })
                    
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid email or password'
            }), 401
                
        except Exception as e:
            print(f"Database error in admin login: {str(e)}")
            return jsonify({
                'error': 'Server error',
                'message': 'A database error occurred'
            }), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Server error in admin login: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An unexpected error occurred'
        }), 500

@bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/session', methods=['GET'])
def check_admin_session():
    if 'admin_id' in session and session.get('is_admin', False):
        return jsonify({
            'authenticated': True,
            'admin': {
                'id': session['admin_id'],
                'name': session['admin_name']
            }
        })
    return jsonify({'authenticated': False})

@bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get total users
            cursor.execute("SELECT COUNT(*) as total_users FROM user_registration")
            users_count = cursor.fetchone()['total_users']
            
            # Get total drivers
            cursor.execute("SELECT COUNT(*) as total_drivers FROM drivers")
            drivers_count = cursor.fetchone()['total_drivers']
            
            # Get total bookings
            cursor.execute("SELECT COUNT(*) as total_bookings FROM bookings")
            bookings_count = cursor.fetchone()['total_bookings']
            
            # Get recent bookings
            cursor.execute("""
                SELECT b.*, u.user_name, d.driver_name
                FROM bookings b
                LEFT JOIN user_registration u ON b.user_id = u.user_id
                LEFT JOIN drivers d ON b.driver_id = d.driver_id
                ORDER BY b.created_at DESC
                LIMIT 5
            """)
            recent_bookings = cursor.fetchall()
            
            return jsonify({
                'stats': {
                    'total_users': users_count,
                    'total_drivers': drivers_count,
                    'total_bookings': bookings_count
                },
                'recent_bookings': recent_bookings
            })
            
        except Exception as e:
            print(f"Database error in admin dashboard: {str(e)}")
            return jsonify({
                'error': 'Server error',
                'message': 'A database error occurred'
            }), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Server error in admin dashboard: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An unexpected error occurred'
        }), 500 