from flask import Flask, request, jsonify
from utils.aibrain_client import generate_itinerary, clear_cache, TravelAssistantError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from typing import Dict, Any
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('travel_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def format_error_response(error: str, status_code: int) -> tuple[Dict[str, Any], int]:
    """Format error responses consistently."""
    return jsonify({
        "status": "error",
        "message": error,
        "status_code": status_code
    }), status_code

def format_success_response(data: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    """Format success responses consistently."""
    return jsonify({
        "status": "success",
        "data": data,
        "status_code": 200
    }), 200

@app.route('/generate-itinerary', methods=['POST'])
@limiter.limit("10 per minute")
def itinerary():
    try:
        data = request.get_json()
        
        if not data:
            return format_error_response("No JSON data provided", 400)
            
        destination = data.get("destination")
        days = data.get("days")
        preferences = data.get("preferences", "sightseeing, food, public transportation")
        language = data.get("language", "en")

        if not destination or not days:
            return format_error_response("Missing required fields: destination and days", 400)

        try:
            days = int(days)
        except ValueError:
            return format_error_response("Days must be a valid integer", 400)

        result = generate_itinerary(destination, days, preferences, language)
        return format_success_response(result)
        
    except TravelAssistantError as te:
        logger.warning(f"Travel assistant error: {str(te)}")
        return format_error_response(str(te), 400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return format_error_response("An unexpected error occurred", 500)

@app.route('/clear-cache', methods=['POST'])
@limiter.limit("5 per hour")
def clear_itinerary_cache():
    """Clear the itinerary generation cache."""
    try:
        clear_cache()
        return format_success_response({"message": "Cache cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
        return format_error_response("Failed to clear cache", 500)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return format_success_response({
        "status": "healthy",
        "version": "1.1.0",
        "environment": os.getenv("FLASK_ENV", "development")
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    return format_error_response("Rate limit exceeded", 429)

if __name__ == '__main__':
    app.run(debug=True)
