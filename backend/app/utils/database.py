import mysql.connector
import os
from dotenv import load_dotenv
import time
import bcrypt
from mysql.connector import errorcode

# Load environment variables
load_dotenv()

# Database configuration for XAMPP
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # XAMPP default has no password
    'database': 'smart_cab_system',
    'raise_on_warnings': True,
    'autocommit': True,
    'auth_plugin': 'mysql_native_password',
    'connect_timeout': 10
}

def create_database_if_not_exists():
    try:
        # Connect without database
        config = db_config.copy()
        del config['database']
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        try:
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
            print(f"Database '{db_config['database']}' created or already exists")
            
            # Select the database
            cursor.execute(f"USE {db_config['database']}")
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_registration (
                    admin_id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_name VARCHAR(100) NOT NULL,
                    admin_email VARCHAR(100) NOT NULL UNIQUE,
                    admin_password VARCHAR(255) NOT NULL,
                    admin_phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_registration (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(100) NOT NULL,
                    user_email VARCHAR(100) NOT NULL UNIQUE,
                    user_password VARCHAR(255) NOT NULL,
                    user_phone VARCHAR(20),
                    user_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_types (
                    vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
                    type_name VARCHAR(50) NOT NULL UNIQUE,
                    base_fare DECIMAL(10,2) NOT NULL,
                    per_km_rate DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_id INT AUTO_INCREMENT PRIMARY KEY,
                    driver_name VARCHAR(100) NOT NULL,
                    driver_email VARCHAR(100) NOT NULL UNIQUE,
                    driver_password VARCHAR(255) NOT NULL,
                    driver_phone VARCHAR(20) NOT NULL,
                    driver_address TEXT,
                    license_number VARCHAR(50) NOT NULL UNIQUE,
                    vehicle_type_id INT,
                    vehicle_number VARCHAR(20) NOT NULL,
                    is_available BOOLEAN DEFAULT TRUE,
                    current_location VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    driver_id INT,
                    pickup_location VARCHAR(255) NOT NULL,
                    destination VARCHAR(255) NOT NULL,
                    booking_date DATE NOT NULL,
                    booking_time TIME NOT NULL,
                    vehicle_type_id INT NOT NULL,
                    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
                    fare DECIMAL(10,2),
                    distance DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
                    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    user_id INT NOT NULL,
                    driver_id INT NOT NULL,
                    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
                    FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
                )
            """)
            
            # Check if admin exists
            cursor.execute("SELECT COUNT(*) FROM admin_registration")
            if cursor.fetchone()[0] == 0:
                # Insert default admin
                cursor.execute("""
                    INSERT INTO admin_registration 
                    (admin_name, admin_email, admin_password, admin_phone)
                    VALUES ('Admin', 'admin@smartcab.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKy7PJN9JNqZ0qK', '1234567890')
                """)
            
            # Check if vehicle types exist
            cursor.execute("SELECT COUNT(*) FROM vehicle_types")
            if cursor.fetchone()[0] == 0:
                # Insert vehicle types
                cursor.execute("""
                    INSERT INTO vehicle_types (type_name, base_fare, per_km_rate)
                    VALUES 
                    ('sedan', 50.00, 10.00),
                    ('suv', 70.00, 15.00),
                    ('luxury', 100.00, 20.00)
                """)
            
            connection.commit()
            print("Database tables created or already exist")
            return True
            
        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")
            connection.rollback()
            return False
            
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def get_db_connection():
    """Get a database connection with retry logic"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the database
            conn = mysql.connector.connect(**db_config)
            if conn.is_connected():
                return conn
                
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                # Database doesn't exist, try to create it
                print(f"Database {db_config['database']} does not exist. Attempting to create it...")
                if create_database_if_not_exists():
                    continue
            print(f"Connection attempt {attempt + 1} failed: {err}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
                
    raise Exception("Failed to establish database connection after multiple attempts")

def test_db_connection():
    """Test database connection and create database if it doesn't exist"""
    try:
        # Try to connect to the database
        connection = get_db_connection()
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            connection.close()
            return True
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    return False 