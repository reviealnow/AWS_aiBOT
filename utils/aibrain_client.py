from google import generativeai as genai
import os
from dotenv import load_dotenv
import logging
from functools import lru_cache
import json
from typing import Dict, Any, Optional
from datetime import datetime
import re

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

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# List available models and verify access
try:
    for m in genai.list_models():
        logger.info(f"Available model: {m.name}")
except Exception as e:
    logger.error(f"Error listing models: {str(e)}")
    raise ValueError("Unable to access Gemini API. Please verify your API key and permissions.")

# Select the most appropriate model
GEMINI_MODEL = "gemini-1.5-pro"  # Using a stable version
for model in genai.list_models():
    if model.name == "models/gemini-1.5-pro":
        GEMINI_MODEL = "gemini-1.5-pro"
        break

logger.info(f"Selected model: {GEMINI_MODEL}")

class TravelAssistantError(Exception):
    """Custom exception for travel assistant errors."""
    pass

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amounts consistently."""
    return f"{currency} {amount:,.2f}"

def format_time_range(start_time: str, end_time: str) -> str:
    """Format time ranges consistently."""
    return f"{start_time} - {end_time}"

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

def format_itinerary_response(raw_response: str) -> str:
    """
    Format the raw AI response into a well-structured itinerary.
    
    Args:
        raw_response: The raw response from the AI model
        
    Returns:
        Formatted itinerary text
    """
    # Split into sections
    sections = re.split(r'\n(?=Day \d+:|Overview:|Essential Tips:|Budget Considerations:|Safety Tips:|Local Customs:)', raw_response)
    
    formatted_sections = []
    
    for section in sections:
        section = section.strip()
        if section:
            # Add proper markdown formatting
            if section.startswith(('Day ', 'Overview:', 'Essential Tips:', 'Budget Considerations:', 'Safety Tips:', 'Local Customs:')):
                section = f"## {section}"
            formatted_sections.append(section)
    
    # Join sections with proper spacing
    formatted_text = "\n\n".join(formatted_sections)
    
    # Add horizontal rules between days
    formatted_text = re.sub(r'(\n## Day \d+:)', r'\n---\1', formatted_text)
    
    return formatted_text

@lru_cache(maxsize=100)
def generate_itinerary(
    destination: str, 
    days: int, 
    preferences: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Generate a travel itinerary using Google's Gemini AI with caching.
    
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
        
        system_prompt = f"""You are an expert travel assistant that creates detailed and personalized travel itineraries.
        Focus on providing practical, well-structured information in the following format:

        Overview:
        [Brief overview of the destination and trip]

        Essential Tips:
        - Best time to visit and current weather considerations
        - Local transportation options and how to get around
        - Important local phrases and communication tips
        - Recommended areas to stay

        [For each day, provide:]
        Day X:
        - Morning (time): [Activities with specific locations, estimated durations, and costs]
        - Afternoon (time): [Activities]
        - Evening (time): [Activities]
        - Recommended restaurants for each meal
        - Local tips and tricks for the day's activities

        Budget Considerations:
        - Estimated daily costs (accommodation, food, activities, transport)
        - Money-saving tips
        - Price ranges for different activities

        Safety Tips:
        - Emergency numbers and locations of hospitals
        - Areas to avoid or be cautious about
        - Common scams to watch out for
        - COVID-19 or other health considerations

        Local Customs:
        - Cultural etiquette and taboos
        - Tipping customs
        - Dress code recommendations
        - Important local laws to be aware of

        Format all costs in {format_currency(0, "USD")} format.
        Format all time ranges as {format_time_range("HH:MM", "HH:MM")}.
        Provide the response in {language} language."""
        
        user_prompt = (
            f"Create a detailed {days}-day itinerary for {destination}. "
            f"Travel preferences: {preferences}. "
            "Include specific recommendations for attractions, restaurants, and activities. "
            "Add estimated costs and practical travel tips. "
            "Also include local customs and etiquette tips."
        )

        try:
            # Configure the model
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Generate content with proper parameters
            response = model.generate_content(
                contents=[
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )

            # Format the response
            formatted_itinerary = format_itinerary_response(response.text)

            # Log the generation
            logger.info(f"Generated itinerary for {destination} ({days} days)")

            return {
                "itinerary": formatted_itinerary,
                "metadata": {
                    "destination": destination,
                    "days": days,
                    "preferences": preferences,
                    "language": language,
                    "model": GEMINI_MODEL,
                    "prompt_tokens": len(system_prompt + user_prompt) // 4,  # Approximate token count
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.1.0"
                }
            }
        except Exception as model_error:
            logger.error(f"Model error: {str(model_error)}")
            # Try fallback with simpler prompt
            response = model.generate_content(
                contents=[{"text": user_prompt}],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            return {
                "itinerary": response.text,
                "metadata": {
                    "destination": destination,
                    "days": days,
                    "preferences": preferences,
                    "language": language,
                    "model": GEMINI_MODEL,
                    "prompt_tokens": len(user_prompt) // 4,
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.1.0",
                    "fallback": True
                }
            }
        
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        raise TravelAssistantError(f"Failed to generate itinerary: {str(e)}")

def clear_cache() -> None:
    """Clear the itinerary generation cache."""
    generate_itinerary.cache_clear()
    logger.info("Cache cleared successfully")
