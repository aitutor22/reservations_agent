# Ramen Restaurant Voice Reservation Agent

A production-ready AI-powered voice agent for **Sakura Ramen House** reservations using OpenAI Realtime API with advanced security guardrails. This web-based application allows customers to inquire about restaurant information, ramen menu options, and create reservations through natural voice conversations with real-time API integration.

## Architecture Overview

### Agent System
The application uses a **3-agent architecture** with security guardrails:

1. **Main Agent** - Entry point with Sakura Ramen House personality that welcomes customers and routes conversations
2. **Information Agent** - Handles all restaurant information queries with dual response system:
   - **Quick responses** for basic info (hours, location, phone, policies)
   - **Vector search** for complex menu and dining queries
3. **Reservation Agent** - Creates and manages reservations with real API integration:
   - Singapore phone number validation (+65 format)
   - Real-time availability checking
   - Confirmation number generation

### Technology Stack
- **Frontend**: Vue.js 2.x with Vuex state management
- **Backend**: FastAPI with OpenAI Agents SDK (v0.2.5)
- **Voice Processing**: OpenAI Realtime API (speech-to-speech) with shimmer voice
- **Real-time Communication**: WebSocket with guardrail filtering
- **API Client**: httpx AsyncClient with connection pooling
- **Security**: Input/output guardrails for content filtering
- **Knowledge Base**: Vector store for complex queries

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- OpenAI API key with Realtime API access

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and add your OpenAI API key

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

// MAKE sure you are in right folder
```

## Key Features

### Voice Interactions
- **Real-time speech-to-speech** processing with PCM16 audio
- **Natural conversation flow** with server-side VAD
- **Multi-turn conversations** with context retention
- **<500ms audio latency** for responsive experience
- **Security guardrails** filtering malicious content
- **Singapore-optimized** voice personality

### Restaurant Information
- Operating hours and location
- Ramen menu varieties (tonkotsu, shoyu, miso, shio)
- Daily specials and limited-time offerings
- Dietary accommodations and customization options
- Wait times and seating policies

### Reservation System  
- **Real API integration** with POST /api/reservations
- **Singapore phone validation** with automatic +65 formatting
- **Confirmation numbers** for each booking
- **Async/sync bridge** for seamless tool execution
- **User-friendly error messages** optimized for voice
- **Reservation lookup** by phone number

## Testing

### Test Guardrails
```bash
cd backend
python test_guardrails.py
```

### Test Reservation API
```bash
cd backend
python test_reservation_api.py
```

### Test Voice Agent
Open browser to http://localhost:5173 after starting both frontend and backend.

## Project Structure

```
reservations_agent/
├── frontend/                 # Vue.js 2.x application
│   ├── src/
│   │   ├── components/      # VoiceInterface component
│   │   ├── store/          # Vuex state management
│   │   ├── router/         # Vue Router
│   │   └── views/          # Application views
│   └── public/
├── backend/                 # FastAPI application
│   ├── realtime_agents/    # OpenAI RealtimeAgent implementations
│   │   ├── main_agent.py
│   │   ├── information_agent.py
│   │   ├── reservation_agent.py
│   │   ├── guardrails.py   # Security filtering
│   │   ├── guardrail_session.py
│   │   └── voice_personality.py
│   ├── realtime_tools/     # Agent tool implementations
│   │   ├── api_client.py   # Singleton HTTP client
│   │   └── reservation.py  # Reservation tools
│   ├── services/           # Business logic
│   ├── models/             # Pydantic models
│   └── api/               # API endpoints
└── docs/                   # Documentation
```

## Development Guidelines

### Voice Interaction Best Practices
- Maintain conversation context throughout sessions
- Provide visual feedback for all audio states
- Handle interruptions gracefully via server-side VAD
- Test with different accents and speaking speeds
- Monitor guardrail statistics for security insights
- Use async context managers for session lifecycle

### Performance Requirements
- Audio latency: <500ms end-to-end
- Initial page load: <2 seconds
- Speech recognition accuracy: >95%
- WebSocket frame size: <700KB base64
- Audio format: PCM16, 24kHz, mono

### Browser Support
- Chrome 90+ (primary)
- Safari 14+ (secondary) 
- Edge 90+ (secondary)

## Security Features

### Guardrail System
- **Input filtering** for malicious prompts and system extraction attempts
- **Output sanitization** to prevent information leakage
- **Singapore phone validation** with privacy protection
- **Detailed logging** of all security events
- **Statistics tracking** for monitoring and analysis

## API Integration

### Reservation API
- **Endpoint**: POST /api/reservations
- **Phone Format**: Automatic +65 prefix for Singapore numbers
- **Async/Sync Bridge**: ThreadPoolExecutor for event loop compatibility
- **Error Handling**: Voice-friendly error messages

## Future Enhancements

### Phase 2
- Reservation modifications/cancellations
- Email confirmations
- Analytics dashboard with guardrail insights

### Phase 3
- Twilio integration for phone calls
- Multi-language support (Japanese, Mandarin, Korean)
- Visual menu browsing with images
- Table management system integration
