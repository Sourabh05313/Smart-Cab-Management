import mysql.connector

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

def check_tables(cursor):
    # List of required tables
    required_tables = [
        'admin_registration',
        'user_registration',
        'driver_registration',
        'vehicle_types',
        'bookings',
        'payments'
    ]
    
    # Get all tables in the database
    cursor.execute("SHOW TABLES")
    existing_tables = [table[0] for table in cursor.fetchall()]
    
    # Check if all required tables exist
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"Missing tables: {', '.join(missing_tables)}")
        return False
    
    print("All required tables exist!")
    return True

def check_table_structure(cursor, table_name):
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        print(f"\nStructure of {table_name} table:")
        for column in columns:
            print(f"  {column[0]}: {column[1]} {column[2]}")
        return True
    except mysql.connector.Error as err:
        print(f"Error checking {table_name} table: {err}")
        return False

def main():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Checking database structure...")
        
        # Check if all required tables exist
        if not check_tables(cursor):
            print("Some tables are missing. Please run setup_xampp_database.py to create them.")
            return
        
        # Check structure of each table
        tables = [
            'admin_registration',
            'user_registration',
            'driver_registration',
            'vehicle_types',
            'bookings',
            'payments'
        ]
        
        for table in tables:
            check_table_structure(cursor, table)
        
        print("\nDatabase check completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 