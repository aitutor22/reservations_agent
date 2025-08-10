# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Ramen Restaurant Voice Reservation Agent - A production-ready voice agent for restaurant reservations using OpenAI Agents SDK with RealtimeAgent. This system enables natural voice conversations for restaurant inquiries and reservation management through a WebSocket bridge architecture.

## Current Implementation Status

✅ **Working Features:**
- Voice input/output via browser microphone
- Real-time speech-to-speech conversation with OpenAI Realtime API
- Server-side Voice Activity Detection (VAD) with proper interruption handling
- Restaurant information queries (hours, location, menu)
- Reservation creation with tool execution
- PCM16 audio processing pipeline with proper chunking
- WebSocket frame size management (<1MB limit)
- Async session lifecycle management

## Architecture

### Technology Stack
- **Frontend**: Vue.js 2.x with Vuex
  - Audio Processing: Web Audio API (ScriptProcessor)
  - PCM16 Conversion: Real-time Float32 to Int16
  - WebSocket: Base64-encoded audio transport
  - Chunk Management: 5-buffer limit (~850ms) with periodic flushing
  
- **Backend**: FastAPI with OpenAI Agents SDK
  - RealtimeAgent: Restaurant-specific voice assistant with handoff capability
  - RealtimeRunner: Session management with async context managers
  - Voice Processing: Server-side VAD, no manual interruption state
  - Tools: Restaurant hours, menu, reservations via function_tool decorators
  - API Integration: httpx for async REST calls to backend services

### Critical Implementation Details

1. **Audio Pipeline (frontend/src/components/VoiceInterface.vue)**
   - Sample Rate: 24kHz mono (OpenAI requirement)
   - Buffer Size: 4096 samples (~170ms)
   - Conversion: Float32 [-1,1] → Int16 [-32768,32767]
   - Chunking: Max 5 buffers per send (~850ms)
   - Flushing: Every 300ms to prevent buffer accumulation

2. **Session Management (backend/realtime_agent.py)**
   - MUST use async context managers for session lifecycle
   - Audio truncation errors are recoverable warnings
   - No manual interruption state management - let SDK handle VAD
   - Proper cleanup with __aenter__/__aexit__ pattern

3. **WebSocket Protocol (ws://localhost:8000/ws/realtime/agent)**
   - Message types: audio_chunk, text_message, end_audio
   - Audio format: Base64-encoded PCM16
   - Frame size limit: <700KB base64 (~525KB binary)
   - Binary frames for audio responses from backend

## Project Structure

```
reservation/
├── frontend/                 # Vue.js 2.x application (voice-only interface)
│   ├── src/
│   │   ├── components/      # VoiceInterface component
│   │   ├── store/          # Vuex state management
│   │   ├── router/         # Single-page routing
│   │   └── views/          # HomeView with voice interface
│   └── public/
├── backend/                 # FastAPI application
│   ├── realtime_agents/    # OpenAI RealtimeAgent implementation
│   ├── services/           # Business logic
│   ├── api/               # API endpoints
│   └── models/            # Data models
└── docs/                   # Documentation
    ├── frontend/           # Frontend-specific docs
    └── backend/            # Backend-specific docs
        ├── realtime_agent_api_integration.md  # API integration patterns
        └── networking_architecture.md          # Network strategies
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
# venv or conda
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# to run
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

### Primary WebSocket Endpoint
`ws://localhost:8000/ws/realtime/agent` - Restaurant RealtimeAgent

**Client → Server Messages:**
```javascript
{ type: 'audio_chunk', audio: string }  // Base64-encoded PCM16
{ type: 'text_message', text: string }  // Text input (fallback)
{ type: 'end_audio' }                   // Signal end of audio
```

**Server → Client Messages:**
```javascript
// Binary frames for audio
ArrayBuffer  // PCM16 audio data (24kHz, mono)

// JSON frames for events
{ type: 'assistant_transcript', transcript: string }
{ type: 'user_transcript', transcript: string }
{ type: 'audio_interrupted' }  // User interrupted bot
{ type: 'audio_end' }          // Audio response complete
{ type: 'session_started', session_id: string }
{ type: 'error', error: string }
{ type: 'warning', message: string }  // Recoverable issues
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
- Vue.js 2.x with Options API (current implementation)
- Vuex for state management
- Proper async/await error handling
- No manual WebSocket reconnection needed (session-based)

### Voice Interaction Best Practices
- Audio latency: ~500-800ms (WebSocket bridge adds ~200ms)
- Visual feedback: Recording indicator, status dots
- Interruption handling: Automatic via server-side VAD
- Transcripts: Real-time display of both user and assistant

### API Integration Best Practices
- Function tools use httpx.AsyncClient for non-blocking REST calls
- Connection pooling with singleton client pattern
- Internal networking (localhost, Docker service names, K8s DNS)
- User-friendly error messages for voice interactions
- See `docs/backend/realtime_agent_api_integration.md` for details

### Critical Lessons Learned
1. **VAD Management**: Never manage interruption state manually - let RealtimeSession handle it
2. **Audio Errors**: "Audio content already shorter" errors are recoverable, don't terminate session
3. **Frame Size**: Always validate chunk size before sending (<700KB base64)
4. **Context Managers**: Always use async context managers for session lifecycle
5. **Buffer Flushing**: Implement periodic flushing to prevent audio accumulation
6. **Handoff Delays**: OpenAI Realtime API doesn't support pause insertion; inject silence buffers (2s of zeros at 24kHz) after detecting handoff tool calls for natural transfer delays

### Security Requirements
- HTTPS for production deployment
- WSS for production WebSocket
- No audio recording persistence
- Session cleanup on disconnect

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

- Test voice interactions with interruptions and overlapping speech
- Monitor WebSocket frame sizes to prevent disconnections
- Use backend/docs/voice_flow_architecture.md for detailed implementation reference
- Audio format MUST be PCM16, 24kHz, mono for OpenAI compatibility
- Always use proper async context managers in Python async code
- Never block audio sends based on interruption state

## docs/backend/llms.txt and docs/frontend/llm.txt - Making Your Code AI-Readable

### Overview

As AI coding assistants become integral to modern development workflows, ensuring your codebase is easily understood by Large Language Models (LLMs) is crucial. The `llms.txt` files serves as a structured guide that helps AI assistants quickly grasp your project's architecture, conventions, and key concepts.

### What is llms.txt?

The `llms.txt` file is a markdown-formatted document placed in `docs/backend/llms.txt` and `docs/frontend/llm.txt` that provides LLMs with:
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

By maintaining `docs/backend/llms.txt` and `docs/frontend/llm.txt` alongside traditional documentation:
- AI assistants understand your specific implementation of OpenAI's voice agents
- Code suggestions align with your ramen restaurant domain logic
- Debugging assistance includes context about your audio pipeline
- Refactoring suggestions maintain your architectural patterns

PLEASE UPDATE THESE FILES PRIOR TO ANY COMMIT

This small investment in AI-readable documentation pays dividends in development velocity and code quality, especially as your voice agent system grows in complexity.