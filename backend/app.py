from flask import Flask, request, jsonify, session, send_from_directory, redirect, url_for
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime
import json
from mysql.connector import Error
import bcrypt
import jwt
from functools import wraps
import time
from mysql.connector import errorcode
import re
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure CORS with credentials
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost", "http://127.0.0.1"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "X-Auth"],
        "max_age": 3600
    }
})

# Configure session
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow all domains in development

# Database configuration for XAMPP
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # XAMPP default has no password
    'database': 'smart_cab_system',  # Updated to match the correct database name
    'raise_on_warnings': True,
    'autocommit': True,
    'auth_plugin': 'mysql_native_password',
    'connect_timeout': 10
}

# Add this near the top of the file, after the imports
API_BASE_URL = 'http://localhost:5000'

def get_db_connection():
    """Get a database connection with retry logic"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the database
            print(f"Attempt {attempt + 1}: Connecting to database '{db_config['database']}'...")
            conn = mysql.connector.connect(**db_config)
            if conn.is_connected():
                print(f"Successfully connected to database '{db_config['database']}'")
                return conn
                
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                # Database doesn't exist, try to create it
                print(f"Database {db_config['database']} does not exist. Attempting to create it...")
                try:
                    # Connect without database
                    config = db_config.copy()
                    del config['database']
                    temp_conn = mysql.connector.connect(**config)
                    cursor = temp_conn.cursor()
                    
                    # Create database
                    print(f"Creating database {db_config['database']}...")
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
                    cursor.execute(f"USE {db_config['database']}")
                    
                    # Create tables
                    print("Creating admin_registration table...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS admin_registration (
                            admin_id INT AUTO_INCREMENT PRIMARY KEY,
                            admin_name VARCHAR(100) NOT NULL,
                            admin_email VARCHAR(100) NOT NULL UNIQUE,
                            admin_password VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Insert default admin if not exists
                    print("Checking for default admin...")
                    cursor.execute("SELECT COUNT(*) FROM admin_registration WHERE admin_email = 'admin@smartcab.com'")
                    if cursor.fetchone()[0] == 0:
                        print("Creating default admin user")
                        try:
                            # Hash the default password
                            default_password = 'admin123'
                            salt = bcrypt.gensalt()
                            hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), salt)
                            print("Salt:", salt)
                            print("Hashed password:", hashed_password)
                            
                            cursor.execute("""
                                INSERT INTO admin_registration 
                                (admin_name, admin_email, admin_password)
                                VALUES ('Admin', 'admin@smartcab.com', %s)
                            """, (hashed_password.decode('utf-8'),))
                            conn.commit()
                            print("Created default admin user with hashed password")
                        except Exception as e:
                            print(f"Error creating default admin: {str(e)}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
                            return jsonify({
                                'status': 'error',
                                'message': 'Error creating default admin user',
                                'details': str(e)
                            }), 500
                    
                    temp_conn.commit()
                    cursor.close()
                    temp_conn.close()
                    print(f"Database {db_config['database']} and tables created successfully")
                    
                    # Try connecting again
                    print("Attempting to connect to newly created database...")
                    conn = mysql.connector.connect(**db_config)
                    if conn.is_connected():
                        print(f"Successfully connected to newly created database '{db_config['database']}'")
                        return conn
                        
                except Exception as e:
                    print(f"Error creating database: {e}")
                    raise
            
            print(f"Connection attempt {attempt + 1} failed: {err}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Giving up.")
                raise
                
    raise Exception("Failed to establish database connection after multiple attempts")

def test_db_connection():
    """Test database connection and create database if it doesn't exist"""
    try:
        connection = get_db_connection()
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            connection.close()
            return True, "Database connection successful"
    except mysql.connector.Error as err:
        error_msg = f"Failed to connect to database: {err}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return False, error_msg
    return False, "Unknown error occurred"

def verify_bookings_table():
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
            
        cursor = conn.cursor()
        
        # Check if bookings table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                pickup_location VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TIME NOT NULL,
                vehicle_type_id INT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
            )
        """)
        
        # Check if vehicle_types table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_types (
                vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
                type_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default vehicle types if they don't exist
        cursor.execute("""
            INSERT IGNORE INTO vehicle_types (type_name) 
            VALUES ('Sedan'), ('SUV'), ('Luxury')
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Tables verified successfully"
        
    except Exception as e:
        print(f"Error verifying tables: {str(e)}")
        return False, f"Error verifying tables: {str(e)}"

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Test endpoint
@app.route('/api/test', methods=['GET'])
def test_connection():
    return jsonify({
        'status': 'success',
        'message': 'Server is running!'
    })

@app.route('/api/base-url', methods=['GET'])
def get_base_url():
    return jsonify({
        'status': 'success',
        'base_url': API_BASE_URL
    })

@app.route('/api/admin/session', methods=['GET'])
def check_admin_session():
    try:
        logger.debug("\n=== Checking Admin Session ===")
        logger.debug("Session contents: %s", dict(session))
        logger.debug("Admin ID in session: %s", session.get('admin_id'))
        
        if 'admin_id' in session:
            logger.debug("Admin ID found in session: %s", session['admin_id'])
            conn = get_db_connection()
            if not conn:
                logger.error("Database connection failed")
                return jsonify({"success": False, "error": "Database connection failed"}), 500
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT admin_id, admin_name FROM admin_registration WHERE admin_id = %s",
                (session['admin_id'],)
            )
            admin = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if admin:
                logger.debug("Admin found in database: %s", admin)
                return jsonify({
                    "success": True,
                    "admin_id": admin['admin_id'],
                    "admin_name": admin['admin_name']
                })
            else:
                logger.warning("Admin not found in database")
                return jsonify({"success": False, "error": "Admin not found"}), 401
        
        logger.warning("No admin_id in session")
        return jsonify({"success": False, "error": "Not logged in"}), 401
        
    except Exception as e:
        logger.error("Session check error: %s", str(e))
        logger.error("Traceback: %s", traceback.format_exc())
        return jsonify({"success": False, "error": "Session check failed"}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        print("\n=== Admin Login Attempt ===")
        
        # Ensure we're getting JSON data
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 400
            
        data = request.get_json()
        print("Request data:", data)
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data received'
            }), 400
            
        admin_email = data.get('admin_email')
        admin_password = data.get('admin_password')
        
        print(f"Login attempt for email: {admin_email}")
        
        if not admin_email or not admin_password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
            
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # First, check if admin_registration table exists
            cursor.execute("SHOW TABLES LIKE 'admin_registration'")
            table_exists = cursor.fetchone()
            print("Admin table exists:", table_exists is not None)
            
            if not table_exists:
                print("Creating admin_registration table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_registration (
                        admin_id INT AUTO_INCREMENT PRIMARY KEY,
                        admin_name VARCHAR(100) NOT NULL,
                        admin_email VARCHAR(100) NOT NULL UNIQUE,
                        admin_password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("Created admin_registration table")
            
            # Check if default admin exists
            cursor.execute("SELECT COUNT(*) as count FROM admin_registration WHERE admin_email = 'admin@smartcab.com'")
            admin_count = cursor.fetchone()['count']
            print("Number of admin users found:", admin_count)
            
            if admin_count == 0:
                print("Creating default admin user")
                try:
                    # Hash the default password
                    default_password = 'admin123'
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), salt)
                    
                    cursor.execute("""
                        INSERT INTO admin_registration 
                        (admin_name, admin_email, admin_password)
                        VALUES ('Admin', 'admin@smartcab.com', %s)
                    """, (hashed_password.decode('utf-8'),))
                    conn.commit()
                    print("Created default admin user with hashed password")
                except Exception as e:
                    print(f"Error creating default admin: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Error creating default admin user',
                        'details': str(e)
                    }), 500
            
            # Check if admin exists and get their details
            print("\n=== Fetching Admin Details ===")
            cursor.execute('SELECT * FROM admin_registration WHERE admin_email = %s', (admin_email,))
            admin = cursor.fetchone()
            print("Admin found:", admin)
            
            if not admin:
                print("No admin found with email:", admin_email)
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid email or password'
                }), 401
                
            # Verify password
            try:
                print("\n=== Password Verification ===")
                print("Stored password type:", type(admin['admin_password']))
                print("Stored password value:", admin['admin_password'])
                print("Input password:", admin_password)
                
                # Ensure stored password is bytes
                stored_password = admin['admin_password']
                if isinstance(stored_password, str):
                    print("Converting stored password from string to bytes")
                    stored_password = stored_password.encode('utf-8')
                
                # Hash the input password for comparison
                print("Encoding input password")
                input_password = admin_password.encode('utf-8')
                
                print("Comparing passwords...")
                print("Stored password (bytes):", stored_password)
                print("Input password (bytes):", input_password)
                
                # Try to verify the password
                try:
                    # First, check if the stored password is a valid bcrypt hash
                    if not stored_password.startswith(b'$2b$'):
                        print("Stored password is not a valid bcrypt hash, rehashing...")
                        salt = bcrypt.gensalt()
                        hashed_password = bcrypt.hashpw(input_password, salt)
                        
                        # Update the stored password with the new hash
                        cursor.execute("""
                            UPDATE admin_registration 
                            SET admin_password = %s 
                            WHERE admin_email = %s
                        """, (hashed_password.decode('utf-8'), admin_email))
                        conn.commit()
                        
                        stored_password = hashed_password
                    
                    if bcrypt.checkpw(input_password, stored_password):
                        print("Password verified successfully")
                        
                        # Set session data
                        session.permanent = True
                        session['admin_id'] = admin['admin_id']
                        session['admin_email'] = admin['admin_email']
                        session['admin_name'] = admin['admin_name']
                        
                        print("Session data set:", session)
                        
                        response = jsonify({
                            'status': 'success',
                            'message': 'Login successful',
                            'admin': {
                                'id': admin['admin_id'],
                                'name': admin['admin_name'],
                                'email': admin['admin_email']
                            }
                        })
                        
                        # Set secure cookie
                        response.set_cookie(
                            'session',
                            value=str(session.get('admin_id', '')),
                            httponly=True,
                            secure=False,  # Set to True in production
                            samesite='Lax',
                            max_age=86400  # 24 hours
                        )
                        
                        return response
                    else:
                        print("Password verification failed")
                        return jsonify({
                            'status': 'error',
                            'message': 'Invalid email or password'
                        }), 401
                except Exception as e:
                    print(f"Error during password verification: {str(e)}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Error verifying password',
                        'details': str(e),
                        'debug_info': {
                            'stored_password_type': str(type(stored_password)),
                            'stored_password_length': len(stored_password) if stored_password else 0,
                            'input_password_type': str(type(input_password)),
                            'input_password_length': len(input_password) if input_password else 0
                        }
                    }), 500
                    
            except Exception as e:
                print(f"Password verification error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error verifying password',
                    'details': str(e)
                }), 500
                
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error occurred',
                'details': str(err)
            }), 500
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    try:
        data = request.get_json()
        admin_name = data.get('admin_name')
        admin_email = data.get('admin_email')
        admin_password = data.get('admin_password')

        if not all([admin_name, admin_email, admin_password]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Check if email already exists
            cursor.execute(
                "SELECT * FROM admin_registration WHERE admin_email = %s",
                (admin_email,)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Email already registered'
                }), 400

            # Hash the password
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

            # Insert new admin
            cursor.execute(
                "INSERT INTO admin_registration (admin_name, admin_email, admin_password) VALUES (%s, %s, %s)",
                (admin_name, admin_email, hashed_password)
            )
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Admin registered successfully'
            })

        except mysql.connector.Error as err:
            print(f"Database error during admin registration: {err}")
            return jsonify({
                'success': False,
                'message': 'Database error occurred'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error in admin registration: {e}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/user/register', methods=['POST'])
def user_register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract and validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()

        # Validate required fields
        if not all([name, email, password, phone, address]):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate email format
        if not '@' in email or not '.' in email:
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate phone number (basic check)
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return jsonify({'error': 'Invalid phone number format'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT COUNT(*) FROM user_registration WHERE user_email = %s", (email,))
            if cursor.fetchone()[0] > 0:
                return jsonify({'error': 'Email already registered'}), 409

            # Insert new user
            query = """
                INSERT INTO user_registration 
                (user_name, user_email, user_password, user_phone, user_address) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, email, password, phone, address))
            conn.commit()
            
            # Get the newly created user's ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            user_id = cursor.fetchone()[0]
            
            return jsonify({
                'message': 'Registration successful',
                'user_id': user_id,
                'redirect': 'userLogin.html'
            })

        except mysql.connector.Error as err:
            print(f"Database error during registration: {err}")
            if err.errno == 1062:  # Duplicate entry error
                return jsonify({'error': 'Email already registered'}), 409
            return jsonify({'error': 'Database operation failed'}), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error in user registration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/session', methods=['GET'])
def check_user_session():
    try:
        print("\n=== Checking User Session ===")
        print("Session contents:", dict(session))
        print("User ID in session:", session.get('user_id'))
        
        if 'user_id' in session:
            print(f"User ID found in session: {session['user_id']}")
            conn = get_db_connection()
            if not conn:
                print("Database connection failed")
                return jsonify({"error": "Database connection failed"}), 500
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_id, user_name FROM user_registration WHERE user_id = %s",
                (session['user_id'],)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                print(f"User found in database: {user}")
                return jsonify({
                    "success": True,
                    "user_id": user['user_id'],
                    "name": user['user_name']
                })
            else:
                print("User not found in database")
                return jsonify({"error": "User not found"}), 401
        
        print("No user_id in session")
        return jsonify({"error": "Not logged in"}), 401
        
    except Exception as e:
        print(f"Session check error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Session check failed"}), 500

@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute(
                "SELECT user_name, user_email, user_phone FROM user_registration WHERE user_id = %s",
                (session['user_id'],)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return jsonify(user)

        elif request.method == 'PUT':
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            password = data.get('password')

            if not all([name, email, phone]):
                return jsonify({"error": "Name, email, and phone are required"}), 400

            # Check if email is already taken by another user
            cursor.execute(
                "SELECT user_id FROM user_registration WHERE user_email = %s AND user_id != %s",
                (email, session['user_id'])
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": "Email already in use"}), 409

            # Update user profile
            if password:
                cursor.execute(
                    """UPDATE user_registration 
                       SET user_name = %s, user_email = %s, user_phone = %s, user_password = %s
                       WHERE user_id = %s""",
                    (name, email, phone, password, session['user_id'])
                )
            else:
                cursor.execute(
                    """UPDATE user_registration 
                       SET user_name = %s, user_email = %s, user_phone = %s
                       WHERE user_id = %s""",
                    (name, email, phone, session['user_id'])
                )

            conn.commit()
            cursor.close()
            conn.close()

            # Update session
            session['user_name'] = name
            session['user_email'] = email
            session['user_phone'] = phone

            return jsonify({"message": "Profile updated successfully"})

    except Exception as e:
        print(f"Profile error: {str(e)}")
        return jsonify({"error": "Profile operation failed"}), 500

@app.route('/api/user/bookings', methods=['GET', 'POST'])
def user_bookings():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Verify and create tables if they don't exist
        try:
            # Check if vehicle_types table exists
            cursor.execute("SHOW TABLES LIKE 'vehicle_types'")
            if not cursor.fetchone():
                # Create vehicle_types table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE vehicle_types (
                        vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
                        type_name VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Insert default vehicle types
                cursor.execute("""
                    INSERT INTO vehicle_types (type_name) 
                    VALUES ('Sedan'), ('SUV'), ('Luxury')
                """)

            # Check if bookings table exists
            cursor.execute("SHOW TABLES LIKE 'bookings'")
            if not cursor.fetchone():
                # Create bookings table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE bookings (
                        booking_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        driver_id INT,
                        vehicle_type_id INT NOT NULL,
                        pickup_location VARCHAR(255) NOT NULL,
                        dropoff_location VARCHAR(255) NOT NULL,
                        booking_date DATE NOT NULL,
                        booking_time TIME NOT NULL,
                        status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
                        fare DECIMAL(10,2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                        FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id),
                        FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
                    )
                """)
            else:
                # Table exists, check its structure
                cursor.execute("DESCRIBE bookings")
                columns = {row['Field']: row for row in cursor.fetchall()}
                print("Existing columns:", columns)  # Debug log
                
                # Check for old column names and rename them
                if 'pickup' in columns and 'pickup_location' not in columns:
                    print("Renaming pickup to pickup_location")  # Debug log
                    cursor.execute("ALTER TABLE bookings CHANGE pickup pickup_location VARCHAR(255) NOT NULL")
                if 'destination' in columns and 'dropoff_location' not in columns:
                    print("Renaming destination to dropoff_location")  # Debug log
                    cursor.execute("ALTER TABLE bookings CHANGE destination dropoff_location VARCHAR(255) NOT NULL")
                
                # Add missing columns if needed
                if 'pickup_location' not in columns:
                    print("Adding pickup_location column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN pickup_location VARCHAR(255) NOT NULL AFTER user_id")
                if 'dropoff_location' not in columns:
                    print("Adding dropoff_location column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN dropoff_location VARCHAR(255) NOT NULL AFTER pickup_location")
                if 'booking_date' not in columns:
                    print("Adding booking_date column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN booking_date DATE NOT NULL AFTER dropoff_location")
                if 'booking_time' not in columns:
                    print("Adding booking_time column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN booking_time TIME NOT NULL AFTER booking_date")
                if 'vehicle_type_id' not in columns:
                    print("Adding vehicle_type_id column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN vehicle_type_id INT NOT NULL AFTER booking_time")
                if 'status' not in columns:
                    print("Adding status column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending' AFTER vehicle_type_id")
                if 'fare' not in columns:
                    print("Adding fare column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN fare DECIMAL(10,2) AFTER status")
                if 'created_at' not in columns:
                    print("Adding created_at column")  # Debug log
                    cursor.execute("ALTER TABLE bookings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER fare")
            
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error creating/verifying tables: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                "error": "Database setup error",
                "details": str(err)
            }), 500

        if request.method == 'GET':
            try:
                print("Fetching bookings for user_id:", session['user_id'])  # Debug log
                
                cursor.execute("""
                    SELECT b.booking_id as id, 
                           b.pickup_location, 
                           b.dropoff_location, 
                           DATE_FORMAT(b.booking_date, '%Y-%m-%d') as booking_date,
                           DATE_FORMAT(b.booking_time, '%h:%i %p') as booking_time,
                           b.status, 
                           vt.type_name as vehicle_type,
                           b.fare
                    FROM bookings b
                    LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
                    WHERE b.user_id = %s 
                    ORDER BY b.booking_date DESC, b.booking_time DESC
                """, (session['user_id'],))
                
                bookings = cursor.fetchall()
                print("Fetched bookings:", bookings)  # Debug log
                
                if not bookings:
                    print("No bookings found for user")  # Debug log
                    return jsonify({"bookings": []})
                    
                return jsonify({"bookings": bookings})
                
            except mysql.connector.Error as err:
                print(f"Database error in GET bookings: {err}")  # Debug log
                print(f"Error code: {err.errno}")  # Debug log
                print(f"SQL state: {err.sqlstate}")  # Debug log
                return jsonify({
                    "error": "Failed to fetch bookings",
                    "details": str(err)
                }), 500
            except Exception as e:
                print(f"Unexpected error in GET bookings: {str(e)}")  # Debug log
                import traceback
                print(f"Traceback: {traceback.format_exc()}")  # Debug log
                return jsonify({
                    "error": "An unexpected error occurred while fetching bookings",
                    "details": str(e),
                    "traceback": traceback.format_exc()
                }), 500
            finally:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass

        elif request.method == 'POST':
            try:
                data = request.get_json()
                print("Received booking data:", data)  # Debug log
                
                if not data:
                    return jsonify({"error": "No data provided"}), 400

                # Map old field names to new ones for backward compatibility
                field_mapping = {
                    'pickup': 'pickup_location',
                    'destination': 'dropoff_location',
                    'date': 'booking_date',
                    'time': 'booking_time',
                    'vehicle_type_id': 'vehicle_type'
                }

                print("Original data:", data)  # Debug log
                
                # Create normalized data with correct field names
                normalized_data = {}
                for old_field, new_field in field_mapping.items():
                    if old_field in data:
                        normalized_data[new_field] = data[old_field]
                        print(f"Mapped {old_field} to {new_field}: {data[old_field]}")  # Debug log

                # Ensure pickup_location is set correctly
                if 'pickup' in data:
                    normalized_data['pickup_location'] = data['pickup']
                    print(f"Explicitly mapped pickup to pickup_location: {data['pickup']}")  # Debug log

                print("Normalized data:", normalized_data)  # Debug log

                # Extract and validate required fields
                required_fields = {
                    'pickup_location': str,
                    'dropoff_location': str,
                    'booking_date': str,
                    'booking_time': str,
                    'vehicle_type': str
                }

                # Check for missing fields
                missing_fields = [field for field in required_fields if field not in normalized_data or not normalized_data[field]]
                if missing_fields:
                    return jsonify({
                        "error": "Missing required fields",
                        "fields": missing_fields,
                        "expected_fields": list(required_fields.keys()),
                        "received_fields": list(data.keys()),
                        "normalized_fields": list(normalized_data.keys())
                    }), 400

                # Validate date format
                try:
                    # Ensure date is in YYYY-MM-DD format
                    date_str = normalized_data['booking_date'].strip()
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                        return jsonify({
                            "error": "Invalid date format",
                            "expected_format": "YYYY-MM-DD (e.g., 2024-04-20)"
                        }), 400
                        
                    booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if booking_date < datetime.now().date():
                        return jsonify({"error": "Booking date must be today or later"}), 400
                except ValueError as e:
                    return jsonify({
                        "error": "Invalid date format",
                        "expected_format": "YYYY-MM-DD (e.g., 2024-04-20)",
                        "details": str(e)
                    }), 400

                # Validate and format time
                try:
                    # Normalize time format (remove extra spaces, ensure uppercase AM/PM)
                    time_str = normalized_data['booking_time'].strip().upper()
                    time_str = re.sub(r'\s+', ' ', time_str)  # Normalize spaces
                    
                    # Parse time
                    time_obj = datetime.strptime(time_str, '%I:%M %p').time()
                    booking_time = time_obj.strftime('%H:%M')
                except ValueError:
                    return jsonify({
                        "error": "Invalid time format",
                        "expected_format": "HH:MM AM/PM (e.g., 02:30 PM)"
                    }), 400

                # Validate vehicle type
                try:
                    cursor.execute(
                        "SELECT vehicle_type_id FROM vehicle_types WHERE type_name = %s",
                        (normalized_data['vehicle_type'],)
                    )
                    result = cursor.fetchone()
                    print("Vehicle type query result:", result)  # Debug log
                    
                    if not result:
                        return jsonify({
                            "error": "Invalid vehicle type",
                            "valid_types": ["Sedan", "SUV", "Luxury"]
                        }), 400
                except Exception as e:
                    print(f"Error validating vehicle type: {str(e)}")  # Debug log
                    return jsonify({
                        "error": "Error validating vehicle type",
                        "details": str(e)
                    }), 500

                # Prepare booking data
                try:
                    booking_data = (
                        session['user_id'],
                        normalized_data['pickup_location'],
                        normalized_data['dropoff_location'],
                        booking_date,
                        booking_time,
                        result['vehicle_type_id']
                    )
                    print("Prepared booking data:", booking_data)  # Debug log
                except Exception as e:
                    print(f"Error preparing booking data: {str(e)}")  # Debug log
                    return jsonify({
                        "error": "Error preparing booking data",
                        "details": str(e),
                        "normalized_data": normalized_data
                    }), 500

                # Insert booking
                try:
                    # First, verify the table structure
                    cursor.execute("DESCRIBE bookings")
                    columns = cursor.fetchall()
                    print("Bookings table structure:", columns)  # Debug log
                    
                    # Convert to dictionary format for easier access
                    column_names = [row['Field'] for row in columns]
                    print("Column names:", column_names)  # Debug log

                    # Check if we have duplicate columns and drop the old ones
                    if 'pickup' in column_names and 'pickup_location' in column_names:
                        print("Dropping old pickup column")  # Debug log
                        cursor.execute("ALTER TABLE bookings DROP COLUMN pickup")
                        conn.commit()

                    if 'destination' in column_names and 'dropoff_location' in column_names:
                        print("Dropping old destination column")  # Debug log
                        cursor.execute("ALTER TABLE bookings DROP COLUMN destination")
                        conn.commit()

                    # Insert booking
                    cursor.execute("""
                        INSERT INTO bookings 
                        (user_id, pickup_location, dropoff_location, booking_date, booking_time, vehicle_type_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                    """, booking_data)
                    
                    conn.commit()
                    print("Booking inserted successfully")  # Debug log
                    
                    return jsonify({
                        "message": "Booking created successfully",
                        "booking_id": cursor.lastrowid
                    })
                except mysql.connector.Error as err:
                    print(f"Database error during booking insertion: {err}")  # Debug log
                    print(f"Error code: {err.errno}")  # Debug log
                    print(f"SQL state: {err.sqlstate}")  # Debug log
                    print(f"SQL query: INSERT INTO bookings (user_id, pickup_location, dropoff_location, booking_date, booking_time, vehicle_type_id, status) VALUES ({booking_data}, 'pending')")  # Debug log
                    
                    # Get more details about the error
                    cursor.execute("SHOW CREATE TABLE bookings")
                    table_structure = cursor.fetchone()
                    print("Table structure:", table_structure)  # Debug log
                    
                    return jsonify({
                        "error": "Failed to create booking",
                        "details": str(err),
                        "normalized_data": normalized_data,
                        "booking_data": booking_data,
                        "column_names": column_names,
                        "table_structure": table_structure['Create Table'] if table_structure else None
                    }), 500
                except Exception as e:
                    print(f"Unexpected error during booking insertion: {str(e)}")  # Debug log
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")  # Debug log
                    return jsonify({
                        "error": "Unexpected error during booking creation",
                        "details": str(e),
                        "traceback": traceback.format_exc()
                    }), 500

            except Exception as e:
                print(f"Unexpected error in POST bookings: {str(e)}")  # Debug log
                import traceback
                print(f"Traceback: {traceback.format_exc()}")  # Debug log
                return jsonify({
                    "error": "An unexpected error occurred",
                    "details": str(e),
                    "traceback": traceback.format_exc()
                }), 500
            finally:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass

    except Exception as e:
        print(f"Bookings error: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/user/login', methods=['POST'])
def user_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                "SELECT * FROM user_registration WHERE user_email = %s AND user_password = %s",
                (email, password)
            )
            user = cursor.fetchone()

            if user:
                session['user_id'] = user['user_id']
                session['user_name'] = user['user_name']
                return jsonify({
                    "message": "Login successful",
                    "name": user['user_name']
                })
            else:
                return jsonify({"error": "Invalid credentials"}), 401

        except mysql.connector.Error as err:
            print(f"Database error during login: {err}")
            return jsonify({"error": "Database operation failed"}), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "An error occurred during login"}), 500

@app.route('/api/user/logout', methods=['POST'])
def user_logout():
    try:
        session.clear()
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        stats = {
            'total_users': 0,
            'total_drivers': 0,
            'total_bookings': 0,
            'total_revenue': 0
        }
        
        try:
            # Get total users
            cursor.execute("SELECT COUNT(*) as count FROM user_registration")
            result = cursor.fetchone()
            stats['total_users'] = result['count'] if result else 0
            
            # Get total drivers
            cursor.execute("SELECT COUNT(*) as count FROM driver_registration")
            result = cursor.fetchone()
            stats['total_drivers'] = result['count'] if result else 0
            
            # Get total bookings
            cursor.execute("SELECT COUNT(*) as count FROM bookings")
            result = cursor.fetchone()
            stats['total_bookings'] = result['count'] if result else 0
            
            # Get total revenue
            cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE payment_status = 'completed'")
            result = cursor.fetchone()
            stats['total_revenue'] = float(result['total']) if result and result['total'] else 0.0
            
            return jsonify({'success': True, 'stats': stats})
            
        except mysql.connector.Error as err:
            logger.error("Database error in stats: %s", err)
            return jsonify({'success': False, 'error': 'Database operation failed'}), 500
            
    except Exception as e:
        logger.error("Error in get_admin_stats: %s", str(e))
        return jsonify({'success': False, 'error': 'An error occurred'}), 500
        
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/api/admin/recent-bookings', methods=['GET'])
def get_recent_bookings():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get recent bookings with user and driver details
            cursor.execute("""
                SELECT b.booking_id, 
                       u.user_name,
                       d.driver_name,
                       b.pickup_location,
                       b.dropoff_location,
                       DATE_FORMAT(b.booking_date, '%Y-%m-%d') as booking_date,
                       DATE_FORMAT(b.booking_time, '%h:%i %p') as booking_time,
                       b.status,
                       vt.type_name as vehicle_type,
                       b.fare
                FROM bookings b
                JOIN user_registration u ON b.user_id = u.user_id
                LEFT JOIN driver_registration d ON b.driver_id = d.driver_id
                LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
                ORDER BY b.booking_date DESC, b.booking_time DESC
                LIMIT 5
            """)
            bookings = cursor.fetchall()
            
            return jsonify({'success': True, 'bookings': bookings})
            
        except mysql.connector.Error as err:
            print(f"Database error in recent bookings: {err}")
            return jsonify({'success': False, 'error': 'Database operation failed'}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Error getting recent bookings: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get recent bookings'}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    try:
        session.clear()
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500

@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT user_id, user_name, user_email, user_phone, user_address,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM user_registration
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            return jsonify({'success': True, 'users': users})
            
        except mysql.connector.Error as err:
            print(f"Database error in get_admin_users: {err}")
            return jsonify({'success': False, 'error': 'Database operation failed'}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Error in get_admin_users: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/api/admin/drivers', methods=['GET'])
def get_admin_drivers():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT d.driver_id, d.driver_name, d.driver_email, d.driver_phone, 
                       d.license_number, d.vehicle_number, vt.type_name as vehicle_type,
                       DATE_FORMAT(d.created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM driver_registration d
                LEFT JOIN vehicle_types vt ON d.vehicle_type_id = vt.vehicle_type_id
                ORDER BY d.created_at DESC
            """)
            drivers = cursor.fetchall()
            
            return jsonify({'success': True, 'drivers': drivers})
            
        except mysql.connector.Error as err:
            print(f"Database error in get_admin_drivers: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch drivers',
                'details': str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Error in get_admin_drivers: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'details': str(e)
        }), 500

@app.route('/api/admin/bookings', methods=['GET'])
def get_admin_bookings():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get all bookings with user and driver details
            cursor.execute("""
                SELECT b.booking_id, 
                       u.user_name,
                       d.driver_name,
                       b.pickup_location,
                       b.dropoff_location,
                       DATE_FORMAT(b.booking_date, '%Y-%m-%d') as booking_date,
                       DATE_FORMAT(b.booking_time, '%h:%i %p') as booking_time,
                       b.status,
                       vt.type_name as vehicle_type,
                       b.fare
                FROM bookings b
                JOIN user_registration u ON b.user_id = u.user_id
                LEFT JOIN driver_registration d ON b.driver_id = d.driver_id
                LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
                ORDER BY b.booking_date DESC, b.booking_time DESC
            """)
            bookings = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'bookings': bookings
            })
            
        except mysql.connector.Error as err:
            print(f"Database error in admin bookings: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch bookings',
                'details': str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Error getting admin bookings: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching bookings',
            'details': str(e)
        }), 500

@app.route('/api/admin/bookings/<int:booking_id>', methods=['PUT'])
def update_booking_status(booking_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        status = request.json.get('status')
        if not status:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookings 
            SET status = %s 
            WHERE booking_id = %s
        """, (status, booking_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Booking status updated successfully'})
        
    except Exception as e:
        print(f"Error updating booking status: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update booking status'}), 500

@app.route('/api/driver/login', methods=['POST'])
def driver_login():
    try:
        print("\n=== Driver Login Attempt ===")
        data = request.get_json()
        driver_email = data.get('driver_email')
        driver_password = data.get('driver_password')

        if not driver_email or not driver_password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Get driver by email
            cursor.execute(
                "SELECT * FROM driver_registration WHERE driver_email = %s",
                (driver_email,)
            )
            driver = cursor.fetchone()

            if not driver:
                return jsonify({
                    'success': False,
                    'message': 'Invalid email or password'
                }), 401

            # Verify password using bcrypt
            try:
                print("\n=== Password Verification ===")
                print("Stored password type:", type(driver['driver_password']))
                print("Stored password value:", driver['driver_password'])
                
                # Get the stored password
                stored_password = driver['driver_password']
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')
                
                # Check if the stored password is a valid bcrypt hash
                if not stored_password.startswith(b'$2b$'):
                    print("Invalid hash format - rehashing password")
                    # Generate new salt and hash
                    salt = bcrypt.gensalt()
                    new_hash = bcrypt.hashpw(driver_password.encode('utf-8'), salt)
                    
                    # Update the stored hash
                    cursor.execute(
                        "UPDATE driver_registration SET driver_password = %s WHERE driver_id = %s",
                        (new_hash.decode('utf-8'), driver['driver_id'])
                    )
                    conn.commit()
                    print("Password rehashed successfully")
                    
                    # Use the new hash for verification
                    stored_password = new_hash
                
                # Verify the password
                if bcrypt.checkpw(driver_password.encode('utf-8'), stored_password):
                    print("Password verified successfully")
                    # Set session data
                    session['driver_id'] = driver['driver_id']
                    session['driver_email'] = driver['driver_email']
                    session['driver_name'] = driver['driver_name']

                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'driver': {
                            'driver_id': driver['driver_id'],
                            'driver_name': driver['driver_name'],
                            'driver_email': driver['driver_email']
                        }
                    })
                else:
                    print("Password verification failed")
                    return jsonify({
                        'success': False,
                        'message': 'Invalid email or password'
                    }), 401
                    
            except ValueError as e:
                print(f"Password verification error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Error verifying password. Please try again.'
                }), 500

        except mysql.connector.Error as err:
            print(f"Database error in driver login: {err}")
            return jsonify({
                'success': False,
                'message': f'Database error: {str(err)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error in driver login: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/driver/session', methods=['GET'])
def check_driver_session():
    try:
        if 'driver_id' in session:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Database connection failed"}), 500
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT driver_id, driver_name FROM driver_registration WHERE driver_id = %s",
                (session['driver_id'],)
            )
            driver = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if driver:
                # Refresh session
                session.permanent = True
                return jsonify({
                    "driver_id": driver['driver_id'],
                    "driver_name": driver['driver_name'],
                    "status": "active"  # Default status for now
                })
        
        return jsonify({"error": "Not logged in"}), 401
    except Exception as e:
        print(f"Session check error: {str(e)}")
        return jsonify({"error": "Session check failed"}), 500

@app.route('/api/driver/stats', methods=['GET'])
def get_driver_stats():
    try:
        if 'driver_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get total bookings
            cursor.execute(
                "SELECT COUNT(*) as total FROM bookings WHERE driver_id = %s",
                (session['driver_id'],)
            )
            result = cursor.fetchone()
            total_bookings = result['total'] if result else 0

            # Get completed bookings
            cursor.execute(
                "SELECT COUNT(*) as completed FROM bookings WHERE driver_id = %s AND status = 'completed'",
                (session['driver_id'],)
            )
            result = cursor.fetchone()
            completed_bookings = result['completed'] if result else 0

            # Get total earnings from completed bookings
            cursor.execute(
                "SELECT COALESCE(SUM(fare), 0) as earnings FROM bookings WHERE driver_id = %s AND status = 'completed'",
                (session['driver_id'],)
            )
            result = cursor.fetchone()
            total_earnings = float(result['earnings']) if result else 0.0

            return jsonify({
                "total_bookings": total_bookings,
                "completed_bookings": completed_bookings,
                "total_earnings": total_earnings
            })

        except mysql.connector.Error as err:
            print(f"Database error getting driver stats: {err}")
            return jsonify({
                "error": "Database operation failed",
                "details": str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error getting driver stats: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/driver/current-booking', methods=['GET'])
def get_current_booking():
    try:
        if 'driver_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT b.*, u.user_name as user_name 
                FROM bookings b 
                JOIN user_registration u ON b.user_id = u.user_id 
                WHERE b.driver_id = %s AND b.status IN ('pending', 'confirmed', 'started') 
                ORDER BY b.booking_date DESC LIMIT 1
            """, (session['driver_id'],))
            booking = cursor.fetchone()

            if booking:
                # Format the response
                formatted_booking = {
                    'id': booking['booking_id'],
                    'pickup_location': booking['pickup_location'],
                    'dropoff_location': booking['dropoff_location'],
                    'booking_date': booking['booking_date'].strftime('%Y-%m-%d'),
                    'booking_time': booking['booking_time'].strftime('%H:%M'),
                    'status': booking['status'],
                    'user_name': booking['user_name'],
                    'fare': booking['fare']
                }
                return jsonify({"booking": formatted_booking})
            else:
                return jsonify({"booking": None})

        except mysql.connector.Error as err:
            print(f"Database error getting current booking: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                "error": "Database operation failed",
                "details": str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error getting current booking: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500

@app.route('/api/driver/bookings', methods=['GET'])
def get_driver_bookings():
    try:
        if 'driver_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT b.booking_id as id,
                       b.pickup_location,
                       b.dropoff_location as destination,
                       DATE_FORMAT(b.booking_date, '%Y-%m-%d') as booking_date,
                       DATE_FORMAT(b.booking_time, '%h:%i %p') as booking_time,
                       b.status,
                       u.user_name,
                       vt.type_name as vehicle_type,
                       b.fare
                FROM bookings b
                JOIN user_registration u ON b.user_id = u.user_id
                LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
                WHERE b.driver_id = %s
                ORDER BY b.booking_date DESC, b.booking_time DESC
                LIMIT 10
            """, (session['driver_id'],))
            bookings = cursor.fetchall()

            return jsonify({"bookings": bookings})

        except mysql.connector.Error as err:
            print(f"Database error getting driver bookings: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                "error": "Database operation failed",
                "details": str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error getting driver bookings: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/driver/update-booking-status', methods=['PUT'])
def update_driver_booking_status():
    try:
        if 'driver_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE bookings SET status = %s WHERE driver_id = %s AND status = 'assigned'",
                (data['status'], session['driver_id'])
            )
            conn.commit()
            return jsonify({"message": "Booking status updated successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({"error": "Failed to update booking status"}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error updating booking status: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/driver/profile', methods=['GET'])
def get_driver_profile():
    conn = None
    cursor = None
    try:
        # Log the session state
        print(f"Current session: {session}")
        
        if 'driver_id' not in session:
            print("No driver_id in session")
            return jsonify({"error": "Not logged in"}), 401

        driver_id = session.get('driver_id')
        print(f"Fetching profile for driver_id: {driver_id}")

        conn = get_db_connection()
        if not conn:
            print("Failed to establish database connection")
            return jsonify({"error": "Database connection failed"}), 500

        try:
            cursor = conn.cursor(dictionary=True)
        except Exception as e:
            print(f"Error creating dictionary cursor: {str(e)}")
            # Fallback to regular cursor if dictionary cursor fails
            cursor = conn.cursor()
        
        try:
            # First verify the driver exists
            print(f"Verifying driver existence for ID: {driver_id}")
            cursor.execute(
                "SELECT driver_id FROM driver_registration WHERE driver_id = %s",
                (driver_id,)
            )
            result = cursor.fetchone()
            if not result:
                print(f"No driver found with ID: {driver_id}")
                return jsonify({"error": "Driver not found"}), 404

            # Get full profile data with vehicle type name
            print("Fetching full profile data")
            cursor.execute("""
                SELECT 
                    dr.driver_id,
                    dr.driver_name,
                    dr.driver_email,
                    dr.driver_phone,
                    dr.license_number,
                    dr.vehicle_number,
                    dr.vehicle_type_id,
                    vt.type_name as vehicle_type
                FROM driver_registration dr
                LEFT JOIN vehicle_types vt ON dr.vehicle_type_id = vt.vehicle_type_id
                WHERE dr.driver_id = %s
            """, (driver_id,))
            
            driver = cursor.fetchone()
            
            if not driver:
                print(f"No profile data found for driver ID: {driver_id}")
                return jsonify({"error": "Driver profile not found"}), 404

            # Handle both dictionary and tuple cursor results
            if isinstance(driver, dict):
                profile_data = {
                    "driver_id": driver['driver_id'],
                    "driver_name": driver['driver_name'] or "",
                    "driver_email": driver['driver_email'] or "",
                    "driver_phone": driver['driver_phone'] or "",
                    "license_number": driver['license_number'] or "",
                    "vehicle_number": driver['vehicle_number'] or "",
                    "vehicle_type_id": driver['vehicle_type_id'] or "",
                    "vehicle_type": driver['vehicle_type'] or ""
                }
            else:
                # If using regular cursor, data comes as tuple
                profile_data = {
                    "driver_id": driver[0] or "",
                    "driver_name": driver[1] or "",
                    "driver_email": driver[2] or "",
                    "driver_phone": driver[3] or "",
                    "license_number": driver[4] or "",
                    "vehicle_number": driver[5] or "",
                    "vehicle_type_id": driver[6] or "",
                    "vehicle_type": driver[7] or ""
                }

            print(f"Successfully fetched profile data: {profile_data}")
            return jsonify(profile_data)

        except mysql.connector.Error as err:
            print(f"Database error getting driver profile: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                "error": "Database operation failed",
                "details": str(err)
            }), 500
            
    except Exception as e:
        print(f"Error getting driver profile: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500
    
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/api/driver/profile', methods=['PUT'])
def update_driver_profile():
    conn = None
    cursor = None
    try:
        if 'driver_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        
        try:
            # Build update query based on provided fields
            update_fields = []
            update_values = []
            
            if 'driver_name' in data:
                update_fields.append("driver_name = %s")
                update_values.append(data['driver_name'])
            
            if 'driver_phone' in data:
                update_fields.append("driver_phone = %s")
                update_values.append(data['driver_phone'])
            
            if 'license_number' in data:
                update_fields.append("license_number = %s")
                update_values.append(data['license_number'])
            
            if 'vehicle_number' in data:
                update_fields.append("vehicle_number = %s")
                update_values.append(data['vehicle_number'])
            
            if 'vehicle_type' in data:
                update_fields.append("vehicle_type = %s")
                update_values.append(data['vehicle_type'])
            
            # Handle password change if provided
            if 'current_password' in data and 'new_password' in data:
                # Verify current password
                cursor.execute(
                    "SELECT driver_password FROM driver_registration WHERE driver_id = %s",
                    (session['driver_id'],)
                )
                result = cursor.fetchone()
                
                if not result or not bcrypt.checkpw(
                    data['current_password'].encode('utf-8'),
                    result['driver_password'].encode('utf-8')
                ):
                    return jsonify({"error": "Current password is incorrect"}), 400
                
                # Hash new password
                hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
                update_fields.append("driver_password = %s")
                update_values.append(hashed_password.decode('utf-8'))
            
            if not update_fields:
                return jsonify({"error": "No valid fields to update"}), 400
            
            # Add driver_id to update_values
            update_values.append(session['driver_id'])
            
            # Build and execute update query
            update_query = f"""
                UPDATE driver_registration 
                SET {', '.join(update_fields)}
                WHERE driver_id = %s
            """
            
            cursor.execute(update_query, update_values)
            conn.commit()
            
            return jsonify({"message": "Profile updated successfully"})

        except mysql.connector.Error as err:
            print(f"Database error updating driver profile: {err}")
            return jsonify({"error": "Database operation failed"}), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error updating driver profile: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

@app.route('/api/driver/logout', methods=['POST'])
def driver_logout():
    try:
        session.clear()
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500

@app.route('/api/driver/register', methods=['POST'])
def driver_register():
    try:
        data = request.get_json()
        driver_name = data.get('driver_name')
        driver_email = data.get('driver_email')
        driver_password = data.get('driver_password')
        driver_phone = data.get('driver_phone')
        driver_address = data.get('driver_address')
        license_number = data.get('license_number')
        vehicle_type_id = data.get('vehicle_type_id')
        vehicle_number = data.get('vehicle_number')

        # Validate required fields
        if not all([driver_name, driver_email, driver_password, driver_phone, license_number, vehicle_number]):
            return jsonify({
                'success': False,
                'message': 'All required fields must be provided'
            }), 400

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Check if email or license number already exists
            cursor.execute(
                "SELECT * FROM driver_registration WHERE driver_email = %s OR license_number = %s",
                (driver_email, license_number)
            )
            existing_driver = cursor.fetchone()
            if existing_driver:
                field = 'email' if existing_driver['driver_email'] == driver_email else 'license number'
                return jsonify({
                    'success': False,
                    'message': f'Driver with this {field} already exists'
                }), 400

            # Hash the password using bcrypt
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(driver_password.encode('utf-8'), salt).decode('utf-8')

            # Insert new driver
            cursor.execute(
                """INSERT INTO driver_registration 
                   (driver_name, driver_email, driver_password, driver_phone, driver_address, 
                    license_number, vehicle_type_id, vehicle_number)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (driver_name, driver_email, hashed_password, driver_phone, driver_address,
                 license_number, vehicle_type_id, vehicle_number)
            )
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Driver registered successfully'
            })

        except mysql.connector.Error as err:
            return jsonify({
                'success': False,
                'message': f'Database error: {str(err)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/admin/verify', methods=['GET'])
def verify_admin_setup():
    try:
        print("\n=== Verifying Admin Setup ===")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check database
            cursor.execute("SELECT DATABASE()")
            db_info = cursor.fetchone()
            print(f"Current database: {db_info['DATABASE()']}")
            
            # Check if admin_registration table exists
            cursor.execute("SHOW TABLES LIKE 'admin_registration'")
            table_exists = cursor.fetchone() is not None
            print(f"Admin table exists: {table_exists}")
            
            if table_exists:
                # Get table structure
                cursor.execute("DESCRIBE admin_registration")
                columns = cursor.fetchall()
                print("Table columns:", columns)
                
                # Check for default admin
                cursor.execute("SELECT * FROM admin_registration WHERE admin_email = 'admin@smartcab.com'")
                admin = cursor.fetchone()
                print("Default admin exists:", admin is not None)
                
                if admin:
                    print("Admin details:", admin)
            
            return jsonify({
                'status': 'success',
                'database': db_info['DATABASE()'],
                'table_exists': table_exists,
                'columns': columns if table_exists else [],
                'default_admin_exists': admin is not None if table_exists else False,
                'admin_details': admin if admin else None
            })
            
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error occurred',
                'details': str(err)
            }), 500
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/admin/reset-password', methods=['POST'])
def reset_admin_password():
    try:
        print("\n=== Resetting Admin Password ===")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Hash the new password
            new_password = 'admin123'
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            
            # Update the admin password
            cursor.execute("""
                UPDATE admin_registration 
                SET admin_password = %s 
                WHERE admin_email = 'admin@smartcab.com'
            """, (hashed_password.decode('utf-8'),))
            
            conn.commit()
            print("Admin password reset successfully")
            
            return jsonify({
                'status': 'success',
                'message': 'Admin password reset successfully',
                'new_password': new_password
            })
            
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({
                'status': 'error',
                'message': 'Database error occurred',
                'details': str(err)
            }), 500
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@app.route('/api/user/bookings/<int:booking_id>', methods=['GET'])
def get_booking_details(booking_id):
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT b.booking_id as id,
                       b.pickup_location,
                       b.dropoff_location,
                       DATE_FORMAT(b.booking_date, '%Y-%m-%d') as booking_date,
                       DATE_FORMAT(b.booking_time, '%h:%i %p') as booking_time,
                       b.status,
                       vt.type_name as vehicle_type,
                       b.fare,
                       d.driver_name
                FROM bookings b
                LEFT JOIN vehicle_types vt ON b.vehicle_type_id = vt.vehicle_type_id
                LEFT JOIN driver_registration d ON b.driver_id = d.driver_id
                WHERE b.booking_id = %s AND b.user_id = %s
            """, (booking_id, session['user_id']))
            
            booking = cursor.fetchone()
            
            if not booking:
                return jsonify({"error": "Booking not found"}), 404
                
            return jsonify(booking)
            
        except mysql.connector.Error as err:
            print(f"Database error getting booking details: {err}")
            print(f"Error code: {err.errno}")
            print(f"SQL state: {err.sqlstate}")
            return jsonify({
                "error": "Failed to fetch booking details",
                "details": str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error getting booking details: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = ["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost", "http://127.0.0.1"]
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Type, X-Auth')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            return response
            
    return response

@app.before_request
def before_request():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check and create admin_registration table
        cursor.execute("SHOW TABLES LIKE 'admin_registration'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE admin_registration (
                    admin_id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_name VARCHAR(100) NOT NULL,
                    admin_email VARCHAR(100) NOT NULL UNIQUE,
                    admin_password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Hash the default password
            default_password = 'admin123'
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), salt)
            
            # Insert default admin if not exists
            cursor.execute("""
                INSERT INTO admin_registration 
                (admin_name, admin_email, admin_password)
                VALUES ('Admin', 'admin@smartcab.com', %s)
            """, (hashed_password.decode('utf-8'),))
            conn.commit()
            print("Created admin_registration table and default admin user with hashed password")
            
        # Check and create user_registration table
        cursor.execute("SHOW TABLES LIKE 'user_registration'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE user_registration (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(100) NOT NULL,
                    user_email VARCHAR(100) NOT NULL UNIQUE,
                    user_password VARCHAR(255) NOT NULL,
                    user_phone VARCHAR(20),
                    user_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Created user_registration table")
            
        # Check and create driver_registration table
        cursor.execute("SHOW TABLES LIKE 'driver_registration'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE driver_registration (
                    driver_id INT AUTO_INCREMENT PRIMARY KEY,
                    driver_name VARCHAR(100) NOT NULL,
                    driver_email VARCHAR(100) NOT NULL UNIQUE,
                    driver_password VARCHAR(255) NOT NULL,
                    driver_phone VARCHAR(20),
                    license_number VARCHAR(50) UNIQUE,
                    vehicle_number VARCHAR(50),
                    vehicle_type_id INT,
                    is_available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Created driver_registration table")
            
        # Check and create vehicle_types table
        cursor.execute("SHOW TABLES LIKE 'vehicle_types'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE vehicle_types (
                    vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
                    type_name VARCHAR(50) NOT NULL UNIQUE,
                    base_fare DECIMAL(10,2) NOT NULL,
                    per_km_rate DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default vehicle types
            cursor.execute("""
                INSERT INTO vehicle_types (type_name, base_fare, per_km_rate)
                VALUES 
                    ('Economy', 50.00, 12.00),
                    ('Premium', 80.00, 15.00),
                    ('Luxury', 120.00, 20.00)
            """)
            conn.commit()
            print("Created vehicle_types table with default types")
            
        # Check and create bookings table
        cursor.execute("SHOW TABLES LIKE 'bookings'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE bookings (
                    booking_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    driver_id INT,
                    vehicle_type_id INT NOT NULL,
                    pickup_location VARCHAR(255) NOT NULL,
                    dropoff_location VARCHAR(255) NOT NULL,
                    booking_date DATE NOT NULL,
                    booking_time TIME NOT NULL,
                    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
                    fare DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                    FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id),
                    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
                )
            """)
            conn.commit()
            print("Created bookings table")
            
        # Check and create payments table
        cursor.execute("SHOW TABLES LIKE 'payments'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_method VARCHAR(50),
                    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
                    transaction_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
                )
            """)
            conn.commit()
            print("Created payments table")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error in before_request: {str(e)}")
        # Don't return error response here as it's a middleware

@app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT'])
def get_user_details(user_id):
    if not check_admin_session():
        return jsonify({'error': 'Admin not logged in'}), 401
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM user_registration WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            
            if user:
                return jsonify({'success': True, 'user': user})
            else:
                return jsonify({'error': 'User not found'}), 404
                
        elif request.method == 'PUT':
            data = request.get_json()
            required_fields = ['user_name', 'user_email', 'user_phone', 'user_address']
            
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Check if email is unique (excluding current user)
            cursor.execute('SELECT user_id FROM user_registration WHERE user_email = %s AND user_id != %s', 
                         (data['user_email'], user_id))
            if cursor.fetchone():
                return jsonify({'error': 'Email already exists'}), 400
                
            update_query = '''
                UPDATE user_registration 
                SET user_name = %s, user_email = %s, user_phone = %s, user_address = %s 
                WHERE user_id = %s
            '''
            cursor.execute(update_query, 
                         (data['user_name'], data['user_email'], data['user_phone'], 
                          data['user_address'], user_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'User updated successfully'})
            
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/api/admin/drivers/<int:driver_id>', methods=['GET', 'PUT'])
def get_driver_details(driver_id):
    if not check_admin_session():
        return jsonify({'error': 'Admin not logged in'}), 401
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM driver_registration WHERE driver_id = %s', (driver_id,))
            driver = cursor.fetchone()
            
            if driver:
                return jsonify({'success': True, 'driver': driver})
            else:
                return jsonify({'error': 'Driver not found'}), 404
                
        elif request.method == 'PUT':
            data = request.get_json()
            required_fields = ['driver_name', 'driver_email', 'driver_phone', 'driver_address', 
                             'driver_license', 'vehicle_type']
            
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Check if email is unique (excluding current driver)
            cursor.execute('SELECT driver_id FROM driver_registration WHERE driver_email = %s AND driver_id != %s', 
                         (data['driver_email'], driver_id))
            if cursor.fetchone():
                return jsonify({'error': 'Email already exists'}), 400
                
            # Check if license is unique (excluding current driver)
            cursor.execute('SELECT driver_id FROM driver_registration WHERE driver_license = %s AND driver_id != %s', 
                         (data['driver_license'], driver_id))
            if cursor.fetchone():
                return jsonify({'error': 'License number already exists'}), 400
                
            update_query = '''
                UPDATE driver_registration 
                SET driver_name = %s, driver_email = %s, driver_phone = %s, 
                    driver_address = %s, driver_license = %s, vehicle_type = %s 
                WHERE driver_id = %s
            '''
            cursor.execute(update_query, 
                         (data['driver_name'], data['driver_email'], data['driver_phone'], 
                          data['driver_address'], data['driver_license'], data['vehicle_type'], 
                          driver_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Driver updated successfully'})
            
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/api/vehicle-types', methods=['GET'])
def get_vehicle_types():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT vehicle_type_id, type_name, base_fare, per_km_rate
                FROM vehicle_types
                ORDER BY base_fare ASC
            """)
            vehicle_types = cursor.fetchall()
            
            if not vehicle_types:
                # If no vehicle types exist, insert default ones
                cursor.execute("""
                    INSERT INTO vehicle_types (type_name, base_fare, per_km_rate)
                    VALUES 
                        ('Economy', 50.00, 12.00),
                        ('Premium', 80.00, 15.00),
                        ('Luxury', 120.00, 20.00)
                """)
                conn.commit()
                
                # Fetch the newly inserted vehicle types
                cursor.execute("""
                    SELECT vehicle_type_id, type_name, base_fare, per_km_rate
                    FROM vehicle_types
                    ORDER BY base_fare ASC
                """)
                vehicle_types = cursor.fetchall()
            
            return jsonify({
                "success": True,
                "vehicle_types": vehicle_types
            })
            
        except mysql.connector.Error as err:
            print(f"Database error getting vehicle types: {err}")
            return jsonify({
                "error": "Failed to fetch vehicle types",
                "details": str(err)
            }), 500
            
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"Error getting vehicle types: {str(e)}")
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500

# Register all routes before the application starts
app.route('/api/admin/stats', methods=['GET'])(get_admin_stats)
app.route('/api/admin/recent-bookings', methods=['GET'])(get_recent_bookings)
app.route('/api/admin/users', methods=['GET'])(get_admin_users)
app.route('/api/admin/drivers', methods=['GET'])(get_admin_drivers)
app.route('/api/admin/bookings', methods=['GET'])(get_admin_bookings)
app.route('/api/admin/bookings/<int:booking_id>', methods=['PUT'])(update_booking_status)
app.route('/api/admin/verify', methods=['GET'])(verify_admin_setup)
app.route('/api/admin/reset-password', methods=['POST'])(reset_admin_password)
app.route('/api/admin/session', methods=['GET'])(check_admin_session)
app.route('/api/admin/login', methods=['POST'])(admin_login)
app.route('/api/admin/logout', methods=['POST'])(admin_logout)
app.route('/api/admin/register', methods=['POST'])(admin_register)

# User routes
app.route('/api/user/register', methods=['POST'])(user_register)
app.route('/api/user/login', methods=['POST'])(user_login)
app.route('/api/user/logout', methods=['POST'])(user_logout)
app.route('/api/user/session', methods=['GET'])(check_user_session)
app.route('/api/user/profile', methods=['GET', 'PUT'])(user_profile)
app.route('/api/user/bookings', methods=['GET', 'POST'])(user_bookings)
app.route('/api/user/bookings/<int:booking_id>', methods=['GET'])(get_booking_details)

# Driver routes
app.route('/api/driver/register', methods=['POST'])(driver_register)
app.route('/api/driver/login', methods=['POST'])(driver_login)
app.route('/api/driver/logout', methods=['POST'])(driver_logout)
app.route('/api/driver/session', methods=['GET'])(check_driver_session)
app.route('/api/driver/stats', methods=['GET'])(get_driver_stats)
app.route('/api/driver/current-booking', methods=['GET'])(get_current_booking)
app.route('/api/driver/bookings', methods=['GET'])(get_driver_bookings)
app.route('/api/driver/update-booking-status', methods=['PUT'])(update_driver_booking_status)
app.route('/api/driver/profile', methods=['GET', 'PUT'])(get_driver_profile)

# Other routes
app.route('/api/vehicle-types', methods=['GET'])(get_vehicle_types)
app.route('/api/test', methods=['GET'])(test_connection)
app.route('/api/base-url', methods=['GET'])(get_base_url)
app.route('/')(serve_index)
app.route('/<path:path>')(serve_static)

# Remove the register_routes() function and its call since we're registering routes directly

if __name__ == '__main__':
    print("\nStarting Smart Cab System Backend Server...")
    print("Checking database connection...")
    db_status = test_db_connection()
    if db_status:
        print("\nDatabase connection successful")
        print("Starting Flask server...")
        app.run(debug=True, port=5000, host='0.0.0.0')
    else:
        print("\nFailed to connect to database. Please check:")
        print("1. XAMPP MySQL service is running")
        print("2. Database credentials in .env file are correct")
        print("3. Database 'SMART_CAB_SYSTEM' exists")
        print("\nTry running setup_database.py first if database doesn't exist.") 

# Print all registered routes
logger.info("Registered routes:")
for rule in app.url_map.iter_rules():
    logger.info("%s: %s %s", rule.endpoint, rule.methods, rule) 