# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Ramen Restaurant Voice Reservation Agent - An AI-powered voice agent for ramen restaurant reservations using OpenAI Realtime API. This web-based application allows customers to inquire about restaurant information, ramen menu options, and manage reservations through natural voice conversations.

## Architecture

### Technology Stack
- **Frontend**: React 18+ with TypeScript
  - Styling: Tailwind CSS
  - State Management: React Context API (or Zustand for complex state)
  - Audio Handling: Web Audio API + WebRTC
  - Real-time Communication: WebSocket for audio streaming
  
- **Backend**: FastAPI with OpenAI Agents SDK
  - Voice Processing: OpenAI Realtime API (speech-to-speech)
  - WebSocket for persistent audio connection
  - Integration: POS system for reservation management (future)

### Key Components

1. **Agent Architecture**
   - Main greeting agent routes to specialized agents
   - Information agent handles hours, location, daily specials, ramen menu, and complex queries
   - Reservation agent manages bookings with tool calling
   - Multi-turn conversation support with context retention

2. **Frontend Components**
   - Voice Visualization Component (animated audio levels)
   - Control Panel (push-to-talk / tap-to-toggle)
   - Transcript Display (real-time updates)
   - Status Indicator (connection, latency)
   - Reservation Summary (confirmation display)

## Project Structure

```
reservation/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API and WebSocket services
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   └── public/
├── backend/                 # FastAPI application
│   ├── agents/             # OpenAI agent definitions
│   ├── services/           # Business logic
│   ├── api/               # API endpoints
│   └── models/            # Data models
└── docs/                   # Documentation

```

## Key Commands

### Development Setup
```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Testing
```bash
# Frontend
npm run test
npm run lint
npm run type-check

# Backend
pytest
```

## API Endpoints

### WebSocket Events
```typescript
// Client -> Server
- 'audio:chunk': { data: ArrayBuffer }
- 'audio:end': {}
- 'session:start': { timezone: string }
- 'session:end': {}

// Server -> Client
- 'audio:response': { data: ArrayBuffer }
- 'transcript:partial': { text: string; role: 'user' | 'agent' }
- 'transcript:final': { text: string; role: 'user' | 'agent' }
- 'agent:state': { state: string; context?: any }
- 'reservation:confirmed': { reservation: Reservation }
- 'error': { code: string; message: string }
```

### REST Endpoints
- `GET /api/health` - Health check
- `POST /api/session/create` - Create new session
- `DELETE /api/session/{sessionId}` - End session
- `GET /api/reservations/lookup?phone={phone}` - Look up reservations
- `POST /api/reservations` - Create new reservation
- `PUT /api/reservations/modify` - Modify existing booking
- `DELETE /api/reservations/cancel` - Cancel reservation

## Conversation Flows

### Information Query Flow
1. User asks about hours/location/daily specials/ramen varieties
2. Information agent responds with accurate ramen restaurant information (quick response or vector search)
3. Agent asks if user needs anything else
4. Routes to reservation agent if needed

### Reservation Creation Flow
1. User expresses intent to make reservation
2. Reservation agent collects:
   - Date and time
   - Party size
   - Name and contact info
3. Agent confirms availability
4. Creates reservation and provides confirmation number
5. Displays reservation summary

## Data Models

```typescript
interface Reservation {
  id: string;
  date: string;
  time: string;
  partySize: number;
  name: string;
  phone: string;
  email?: string;
  confirmationNumber: string;
  specialRequests?: string;
  seatingPreference?: 'counter' | 'table' | 'booth' | 'no-preference';
  dietaryRestrictions?: string[];
  status: 'confirmed' | 'cancelled' | 'modified';
}

interface AppState {
  connectionStatus: 'idle' | 'connecting' | 'connected' | 'error';
  sessionId: string | null;
  isRecording: boolean;
  transcript: TranscriptMessage[];
  currentAgentState: 'greeting' | 'information' | 'reservation' | 'confirmation';
  pendingReservation: Partial<Reservation> | null;
  confirmedReservation: Reservation | null;
}
```

## Development Guidelines

### Code Style
- Use TypeScript for type safety
- Follow React functional component patterns with hooks
- Implement proper error handling for all async operations
- Use proper WebSocket connection management with auto-reconnect

### Voice Interaction Best Practices
- Maintain <500ms audio latency
- Provide visual feedback for all audio states
- Handle interruptions gracefully
- Show partial transcripts during speech

### Security Requirements
- HTTPS only deployment
- Secure WebSocket (WSS) connections
- No storage of audio recordings
- Session timeout after 5 minutes of inactivity

## Performance Requirements
- Audio latency: <500ms end-to-end
- Initial page load: <2 seconds
- WebSocket reconnection: <3 seconds
- Speech recognition accuracy: >95%

## Browser Support
- Chrome 90+ (primary)
- Safari 14+ (secondary)
- Edge 90+ (secondary)
- Firefox 88+ (best effort)

## Implementation Phases

### Phase 1 - MVP (Current)
- Basic voice interface
- General information agent
- Simple reservation creation
- Web-only interface

### Phase 2 - Enhanced Features
- Reservation modifications/cancellations
- Improved error handling
- Analytics dashboard
- Email confirmations

### Phase 3 - Production Ready
- Twilio integration for phone calls
- Multi-language support
- Visual menu browsing
- Table management integration

## Important Notes

- Always test voice interactions with different accents and speaking speeds
- Ensure graceful fallbacks for all error states
- Maintain conversation context throughout the session
- Test on mobile devices for responsive design
- Follow WCAG 2.1 AA accessibility guidelines

## llms.txt - Making Your Code AI-Readable

### Overview

As AI coding assistants become integral to modern development workflows, ensuring your codebase is easily understood by Large Language Models (LLMs) is crucial. The `llms.txt` file serves as a structured guide that helps AI assistants quickly grasp your project's architecture, conventions, and key concepts.

### What is llms.txt?

The `llms.txt` file is a markdown-formatted document placed in your project root that provides LLMs with:
- High-level project overview and purpose
- Architecture descriptions and design decisions
- Key API endpoints and their functions
- Important business logic explanations
- Code organization and file structure
- Development conventions and patterns

### Why It Matters for This Project

For our ramen restaurant voice agent, having comprehensive LLM-readable documentation means:

1. **Faster Development**: When you or other developers use AI assistants (GitHub Copilot, Cursor, Claude, etc.), they'll have immediate context about the voice agent architecture, FastAPI endpoints, and OpenAI Realtime API integration.

2. **Better AI Suggestions**: LLMs can provide more accurate code completions and suggestions when they understand the reservation flow, agent handoff patterns, and POS integration requirements.

3. **Easier Onboarding**: New team members using AI tools can quickly understand the codebase structure, reducing ramp-up time.

4. **Consistent Code Generation**: AI assistants will follow your established patterns for WebSocket handling, state management, and error handling.

### Implementation Benefits

By maintaining an `llms.txt` file alongside traditional documentation:
- AI assistants understand your specific implementation of OpenAI's voice agents
- Code suggestions align with your ramen restaurant domain logic
- Debugging assistance includes context about your audio pipeline
- Refactoring suggestions maintain your architectural patterns

This small investment in AI-readable documentation pays dividends in development velocity and code quality, especially as your voice agent system grows in complexity.