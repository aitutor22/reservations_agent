# Ramen Restaurant Voice Reservation Agent

An AI-powered voice agent for **Sakura Ramen House** reservations using OpenAI Realtime API. This web-based application allows customers to inquire about restaurant information, ramen menu options, and manage reservations through natural voice conversations.

## Architecture Overview

### Agent System
The application uses a **3-agent architecture** for optimal conversation flow:

1. **Greeting Agent** - Entry point that welcomes customers and routes conversations
2. **Information Agent** - Handles all restaurant information queries with dual response system:
   - **Quick responses** for basic info (hours, location, phone, policies)
   - **Vector search** for complex menu and dining queries
3. **Reservation Agent** - Manages booking requests (currently walk-in only with digital queue)

### Technology Stack
- **Frontend**: React 18+ with TypeScript, Tailwind CSS
- **Backend**: FastAPI with OpenAI Agents SDK  
- **Voice Processing**: OpenAI Realtime API (speech-to-speech)
- **Real-time Communication**: WebSocket for audio streaming
- **Knowledge Base**: Vector store for complex queries

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- OpenAI API key

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
```

## Key Features

### Voice Interactions
- **Real-time speech-to-speech** processing
- **Natural conversation flow** with interruption handling
- **Multi-turn conversations** with context retention
- **<500ms audio latency** for responsive experience

### Restaurant Information
- Operating hours and location
- Ramen menu varieties (tonkotsu, shoyu, miso, shio)
- Daily specials and limited-time offerings
- Dietary accommodations and customization options
- Wait times and seating policies

### Reservation System
- Walk-in only policy communication
- Digital queue system information
- Availability and wait time estimates
- Future reservation system integration ready

## Testing the Information Agent

You can test the enhanced Information Agent directly:

```bash
cd backend
python agents/information_agent.py --test
```

This will run through common queries and show whether they use quick responses or vector search.

## Project Structure

```
reservations_agent/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API and WebSocket services
│   │   └── types/          # TypeScript type definitions
│   └── public/
├── backend/                 # FastAPI application
│   ├── agents/             # OpenAI agent definitions
│   │   ├── greeting_agent.py
│   │   ├── information_agent.py (Information Agent)
│   │   └── reservation_agent.py
│   ├── services/           # Business logic
│   ├── knowledge/          # Vector store management
│   └── api/               # API endpoints
└── docs/                   # Documentation
```

## Development Guidelines

### Voice Interaction Best Practices
- Maintain conversation context throughout sessions
- Provide visual feedback for all audio states
- Handle interruptions gracefully
- Test with different accents and speaking speeds

### Performance Requirements
- Audio latency: <500ms end-to-end
- Initial page load: <2 seconds
- Speech recognition accuracy: >95%

### Browser Support
- Chrome 90+ (primary)
- Safari 14+ (secondary) 
- Edge 90+ (secondary)

## Future Enhancements

### Phase 2
- Reservation modifications/cancellations
- Email confirmations
- Analytics dashboard

### Phase 3
- Twilio integration for phone calls
- Multi-language support (Japanese, Mandarin, Korean)
- Visual menu browsing with images
- Table management system integration
