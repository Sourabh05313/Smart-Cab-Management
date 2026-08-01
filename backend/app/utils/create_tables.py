import mysql.connector

def create_database_and_tables():
    # First connect without specifying a database
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'auth_plugin': 'mysql_native_password'
    }

    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS smart_cab")
        cursor.execute("USE smart_cab")

        # Create user_registration table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_registration (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add address column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE user_registration ADD COLUMN address TEXT")
            print("Added address column to user_registration table")
        except mysql.connector.Error as err:
            if err.errno == 1060:  # Duplicate column error
                print("Address column already exists")
            else:
                raise

        # Create driver_registration table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_registration (
                driver_id INT AUTO_INCREMENT PRIMARY KEY,
                driver_name VARCHAR(100) NOT NULL,
                driver_phone VARCHAR(20) NOT NULL,
                vehicle_number VARCHAR(20) NOT NULL,
                vehicle_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create bookings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                pickup_location VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TIME NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                driver_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_registration(user_id),
                FOREIGN KEY (driver_id) REFERENCES driver_registration(driver_id)
            )
        """)

        print("Database and tables created successfully!")

    except Exception as e:
        print(f"Error creating database and tables: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    create_database_and_tables() 