import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from functools import lru_cache
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('travel_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

class TravelAssistantError(Exception):
    """Custom exception for travel assistant errors."""
    pass

def validate_inputs(destination: str, days: int, preferences: str) -> None:
    """
    Validate input parameters with detailed error messages.
    
    Args:
        destination: The travel destination
        days: Number of days for the trip
        preferences: User preferences for the trip
        
    Raises:
        TravelAssistantError: If validation fails
    """
    if not isinstance(destination, str) or not destination.strip():
        raise TravelAssistantError("Destination must be a non-empty string")
    if not isinstance(days, int) or days < 1 or days > 30:
        raise TravelAssistantError("Days must be an integer between 1 and 30")
    if not isinstance(preferences, str):
        raise TravelAssistantError("Preferences must be a string")
    
    # Additional validation for destination
    if len(destination) > 100:
        raise TravelAssistantError("Destination name is too long (max 100 characters)")
    
    # Additional validation for preferences
    if len(preferences) > 500:
        raise TravelAssistantError("Preferences text is too long (max 500 characters)")

@lru_cache(maxsize=100)
def generate_itinerary(
    destination: str, 
    days: int, 
    preferences: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Generate a travel itinerary using Google's Gemini API with caching.
    
    Args:
        destination: The travel destination
        days: Number of days for the trip
        preferences: User preferences for the trip
        language: Language code for the response (default: "en")
        
    Returns:
        Dict containing the itinerary and metadata
        
    Raises:
        TravelAssistantError: If generation fails
    """
    try:
        validate_inputs(destination, days, preferences)
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = f"""You are an expert travel assistant that creates detailed and personalized travel itineraries.
        Focus on providing practical, well-structured information including:
        - Daily schedules with time estimates
        - Local transportation options and costs
        - Must-visit attractions and hidden gems
        - Local cuisine recommendations
        - Cultural tips and etiquette
        - Budget considerations
        - Safety tips and local emergency numbers
        - Weather considerations and best time to visit
        Format the response in a clear, organized manner with sections and bullet points.
        Provide the response in {language} language."""
        
        user_prompt = (
            f"Create a detailed {days}-day itinerary for {destination}. "
            f"Travel preferences: {preferences}. "
            "Include specific recommendations for attractions, restaurants, and activities. "
            "Add estimated costs and practical travel tips. "
            "Also include local customs and etiquette tips."
        )

        # Generate response using Gemini
        response = model.generate_content(
            contents=[
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [user_prompt]}
            ],
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2000,
                "top_p": 0.8,
                "top_k": 40
            }
        )

        # Log the generation
        logger.info(f"Generated itinerary for {destination} ({days} days)")

        return {
            "itinerary": response.text,
            "metadata": {
                "destination": destination,
                "days": days,
                "preferences": preferences,
                "language": language,
                "model": "gemini-pro",
                "prompt_tokens": len(system_prompt + user_prompt) // 4,  # Approximate token count
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.1.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        raise TravelAssistantError(f"Failed to generate itinerary: {str(e)}")

def clear_cache() -> None:
    """Clear the itinerary generation cache."""
    generate_itinerary.cache_clear()
    logger.info("Cache cleared successfully")
