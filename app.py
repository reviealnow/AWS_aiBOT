from flask import Flask, request, jsonify, render_template
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

@app.route('/')
def index():
    """Serve the main HTML interface."""
    return render_template('index.html')

@app.route('/api/docs')
def api_docs():
    """API documentation endpoint."""
    return jsonify({
        "message": "Travel Assistant API",
        "version": "1.1.0",
        "status": "running",
        "endpoints": {
            "GET /": "Web interface",
            "GET /api/docs": "This documentation",
            "GET /health": "Health check",
            "POST /generate-itinerary": "Generate travel itinerary",
            "POST /clear-cache": "Clear cache"
        },
        "usage": {
            "generate_itinerary": {
                "method": "POST",
                "url": "/generate-itinerary",
                "required_fields": ["destination", "days"],
                "optional_fields": ["preferences", "language"],
                "example": {
                    "destination": "Paris",
                    "days": 3,
                    "preferences": "museums, cafes, walking",
                    "language": "en"
                }
            },
            "clear_cache": {
                "method": "POST",
                "url": "/clear-cache",
                "description": "Clear the itinerary generation cache"
            }
        },
        "rate_limits": {
            "default": "200 per day, 50 per hour",
            "generate_itinerary": "10 per minute",
            "clear_cache": "5 per hour"
        }
    })

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

        # Additional input validation
        if not isinstance(destination, str) or len(destination.strip()) == 0:
            return format_error_response("Destination must be a non-empty string", 400)
        
        if days < 1 or days > 30:
            return format_error_response("Days must be between 1 and 30", 400)

        if len(destination) > 100:
            return format_error_response("Destination name is too long (max 100 characters)", 400)

        if len(preferences) > 500:
            return format_error_response("Preferences text is too long (max 500 characters)", 400)

        supported_languages = {'en', 'es', 'fr', 'de', 'it', 'ja', 'zh'}
        if language not in supported_languages:
            return format_error_response(f"Unsupported language. Supported languages: {', '.join(supported_languages)}", 400)

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

@app.errorhandler(404)
def not_found_error(e):
    return format_error_response("Resource not found", 404)

@app.errorhandler(500)
def internal_error(e):
    return format_error_response("Internal server error", 500)

if __name__ == '__main__':
    app.run(debug=True)
