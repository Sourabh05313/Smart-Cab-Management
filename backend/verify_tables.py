import mysql.connector
from mysql.connector import errorcode

# Database configuration
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

def create_tables(cursor):
    # Create user_registration table
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
    print("Created user_registration table")

    # Create driver_registration table
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
    print("Created driver_registration table")

    # Create vehicle_types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_types (
            vehicle_type_id INT AUTO_INCREMENT PRIMARY KEY,
            type_name VARCHAR(50) NOT NULL UNIQUE,
            base_fare DECIMAL(10,2) NOT NULL,
            per_km_rate DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created vehicle_types table")

    # Create bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            driver_id INT,
            pickup_location VARCHAR(255) NOT NULL,
            dropoff_location VARCHAR(255) NOT NULL,
            booking_date DATE NOT NULL,
            booking_time TIME NOT NULL,
            vehicle_type_id INT NOT NULL,
            status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
            fare DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
            FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id),
            FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(vehicle_type_id)
        )
    """)
    print("Created bookings table")

    # Create payments table
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
    print("Created payments table")

def update_vehicle_types(cursor):
    try:
        # Check if base_fare and per_km_rate columns exist in vehicle_types
        cursor.execute("SHOW COLUMNS FROM vehicle_types LIKE 'base_fare'")
        base_fare_exists = cursor.fetchone() is not None
        
        cursor.execute("SHOW COLUMNS FROM vehicle_types LIKE 'per_km_rate'")
        per_km_rate_exists = cursor.fetchone() is not None
        
        if not base_fare_exists:
            print("Adding base_fare column to vehicle_types")
            cursor.execute("ALTER TABLE vehicle_types ADD COLUMN base_fare DECIMAL(10,2) NOT NULL DEFAULT 50.00")
            
        if not per_km_rate_exists:
            print("Adding per_km_rate column to vehicle_types")
            cursor.execute("ALTER TABLE vehicle_types ADD COLUMN per_km_rate DECIMAL(10,2) NOT NULL DEFAULT 10.00")
        
        # Insert or update default vehicle types
        cursor.execute("""
            INSERT INTO vehicle_types (type_name, base_fare, per_km_rate) VALUES 
            ('Sedan', 50.00, 10.00),
            ('SUV', 70.00, 15.00),
            ('Hatchback', 40.00, 8.00),
            ('Luxury', 100.00, 20.00)
            ON DUPLICATE KEY UPDATE 
            base_fare = VALUES(base_fare),
            per_km_rate = VALUES(per_km_rate)
        """)
        print("Updated vehicle types and rates")
        
    except mysql.connector.Error as err:
        print(f"Error updating vehicle_types table: {err}")

def main():
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Connected to MySQL server")
        
        # Create tables
        create_tables(cursor)
        
        # Update vehicle types
        update_vehicle_types(cursor)
        
        conn.commit()
        print("All tables created and vehicle types updated successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 