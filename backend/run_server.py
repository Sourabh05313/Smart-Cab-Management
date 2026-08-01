from app import app
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Print all registered routes for debugging
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info("%s: %s %s", rule.endpoint, rule.methods, rule)
            
        # Run the app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        logger.error("Error starting server: %s", str(e))
        logger.error("Traceback: %s", traceback.format_exc())
        raise 