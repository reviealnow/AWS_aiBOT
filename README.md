# Travel Assistant AI Bot

A smart travel assistant powered by Google's Gemini AI that generates personalized travel itineraries.

## Features

- Generate detailed travel itineraries with daily schedules
- Multi-language support
- Caching for frequently requested destinations
- Rate limiting to prevent abuse
- Comprehensive error handling
- Detailed logging
- Health check endpoint
- Cache management

## Prerequisites

- Python 3.8+
- Google API key for Gemini AI
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/travel-assistant-ai.git
cd travel-assistant-ai
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

4. Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
FLASK_ENV=development
```

## Usage

1. Start the server:
```bash
python app.py
```

2. The API will be available at `http://localhost:5000`

### API Endpoints

#### Generate Itinerary
```http
POST /generate-itinerary
Content-Type: application/json

{
    "destination": "Kyoto, Japan",
    "days": 3,
    "preferences": "cherry blossom viewing, local cuisine, historical temples",
    "language": "en"
}
```

#### Clear Cache
```http
POST /clear-cache
```

#### Health Check
```http
GET /health
```

## Rate Limits

- 200 requests per day
- 50 requests per hour
- 10 requests per minute for itinerary generation
- 5 requests per hour for cache clearing

## Error Handling

The API returns consistent error responses in the following format:
```json
{
    "status": "error",
    "message": "Error description",
    "status_code": 400
}
```

## Logging

Logs are written to both:
- Console output
- `travel_assistant.log` file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version

Current version: 1.1.0
