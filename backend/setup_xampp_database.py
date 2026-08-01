import mysql.connector
from mysql.connector import errorcode
import bcrypt

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

def create_database(cursor, db_name):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database {db_name} created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def create_tables(cursor):
    # Admin registration table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_registration (
                admin_id INT AUTO_INCREMENT PRIMARY KEY,
                admin_name VARCHAR(100) NOT NULL,
                admin_email VARCHAR(100) NOT NULL UNIQUE,
                admin_password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Admin registration table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating admin_registration table: {err}")

    # User registration table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_registration (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(100) NOT NULL,
                user_email VARCHAR(100) NOT NULL UNIQUE,
                user_password VARCHAR(255) NOT NULL,
                user_phone VARCHAR(20),
                user_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("User registration table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating user_registration table: {err}")

    # Driver registration table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_registration (
                driver_id INT AUTO_INCREMENT PRIMARY KEY,
                driver_name VARCHAR(100) NOT NULL,
                driver_email VARCHAR(100) NOT NULL UNIQUE,
                driver_password VARCHAR(255) NOT NULL,
                driver_phone VARCHAR(20),
                license_number VARCHAR(50) UNIQUE,
                vehicle_number VARCHAR(20),
                vehicle_type_id INT,
                status ENUM('active', 'inactive') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Driver registration table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating driver_registration table: {err}")

    # Vehicle types table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_types (
                vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
                type_name VARCHAR(50) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Vehicle types table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating vehicle_types table: {err}")

    # Bookings table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                driver_id INT,
                pickup_location VARCHAR(255) NOT NULL,
                dropoff_location VARCHAR(255) NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TIME NOT NULL,
                status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
                fare DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id)
            )
        """)
        print("Bookings table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating bookings table: {err}")

    # Payments table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
            )
        """)
        print("Payments table created successfully")
    except mysql.connector.Error as err:
        print(f"Failed creating payments table: {err}")

def main():
    try:
        # First connect without database
        config = db_config.copy()
        del config['database']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Create database
        create_database(cursor, db_config['database'])
        
        # Use the database
        cursor.execute(f"USE {db_config['database']}")
        
        # Create tables
        create_tables(cursor)
        
        # Insert default vehicle types if not exists
        try:
            cursor.execute("""
                INSERT IGNORE INTO vehicle_types (type_name) VALUES 
                ('Sedan'),
                ('SUV'),
                ('Hatchback'),
                ('Luxury')
            """)
            print("Default vehicle types inserted successfully")
        except mysql.connector.Error as err:
            print(f"Failed inserting vehicle types: {err}")

        conn.commit()
        print("Database setup completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 