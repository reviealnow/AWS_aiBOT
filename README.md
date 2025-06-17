# AI Travel Assistant

An intelligent travel assistant powered by Google's Gemini AI that generates personalized travel itineraries based on your preferences.

## Features

- 🌍 Generate detailed travel itineraries for any destination
- 🗣️ Support for multiple languages (English, Spanish, French, German, Italian, Japanese, Chinese)
- 💰 Detailed cost estimates and budget considerations
- 🏃‍♂️ Day-by-day activity planning with time estimates
- 🍴 Restaurant recommendations
- 🚗 Transportation guidance
- 🔒 Rate limiting to prevent abuse
- 📝 Caching for improved performance
- 🎨 Modern web interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-travel-assistant.git
cd ai-travel-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Fill in the form with your travel details:
   - Destination
   - Number of days (1-30)
   - Travel preferences (optional)
   - Preferred language

4. Click "Generate Itinerary" to get your personalized travel plan

## API Documentation

The service also provides a REST API for integration with other applications.

### Endpoints

- `GET /` - Web interface
- `GET /api/docs` - API documentation
- `GET /health` - Health check
- `POST /generate-itinerary` - Generate travel itinerary
- `POST /clear-cache` - Clear cache

### Generate Itinerary

```http
POST /generate-itinerary
Content-Type: application/json

{
    "destination": "Paris",
    "days": 3,
    "preferences": "museums, cafes, walking",
    "language": "en"
}
```

#### Response Format

```json
{
    "status": "success",
    "data": {
        "itinerary": "...",
        "metadata": {
            "destination": "Paris",
            "days": 3,
            "preferences": "museums, cafes, walking",
            "language": "en",
            "model": "gemini-2.0-flash",
            "prompt_tokens": 500,
            "generated_at": "2024-03-17T12:00:00Z",
            "version": "1.1.0"
        }
    },
    "status_code": 200
}
```

## Rate Limits

- Default: 200 requests per day, 50 per hour
- Generate Itinerary: 10 requests per minute
- Clear Cache: 5 requests per hour

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
    "status": "error",
    "message": "Error description",
    "status_code": 400
}
```

## Development

- Built with Flask and Google's Gemini AI
- Uses Tailwind CSS for the frontend
- Implements caching using Python's lru_cache
- Includes comprehensive logging
- Follows REST API best practices

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
