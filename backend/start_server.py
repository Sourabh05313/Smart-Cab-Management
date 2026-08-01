import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

try:
    from app import app
    from app.utils.database import test_db_connection
    
    if __name__ == '__main__':
        print("Starting Smart Cab System Backend Server...")
        print("Server will be available at http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        
        # Test database connection
        if test_db_connection():
            print("Starting Flask server...")
            app.run(debug=True, port=5000, host='0.0.0.0')
        else:
            print("Failed to start server due to database connection issues")
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Please ensure:")
    print("1. All required Python packages are installed")
    print("2. The app directory structure is correct")
    print("3. All necessary files are present")
    print(f"Current Python path: {sys.path}")
except Exception as e:
    print(f"Unexpected error: {e}") 