from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    # Configure app
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['SESSION_COOKIE_SECURE'] = False  # For development only
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    
    # Import and register blueprints
    from .routes.admin_routes import bp as admin_bp
    from .routes.user_routes import bp as user_bp
    from .routes.driver_routes import bp as driver_bp
    from .routes.booking_routes import bp as booking_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(booking_bp)
    
    # Add test route
    @app.route('/api/test', methods=['GET'])
    def test_route():
        return {'message': 'Server is running!'}
    
    return app

# Create and export the app instance
app = create_app() 