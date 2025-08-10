# Frontend TODO

## Current Implementation
- ✅ Text chat via WebSocket (working)
- ✅ Message display and typing indicators
- ✅ Connection status management
- 🚧 Adding WebRTC audio alongside WebSocket

## Phase 1: Backend Token Generation ✅
- [x] Create /api/realtime/session endpoint
- [x] Generate ephemeral tokens
- [x] Configure Realtime API parameters

## Phase 2: Frontend WebRTC Foundation ✅
- [x] Create WebRTC service class
- [x] Implement RTCPeerConnection setup
- [x] Add getUserMedia for microphone
- [x] Setup data channel for events
- [x] Handle SDP offer/answer exchange
- [x] Update MessageInput for dual mode
- [x] Add voice/text mode toggle
- [x] Update Vuex store with WebRTC state

## Phase 3: Audio Integration (Future)
- [ ] Voice visualizer component
- [ ] Audio level indicators
- [ ] Push-to-talk vs toggle mode
- [ ] Voice activity detection

## Phase 4: UI Enhancement (Future)
- [ ] Recording state animations
- [ ] Transcription display
- [ ] Audio device selection
- [ ] Network quality indicator

## Phase 5: Production Ready (Future)
- [ ] Error recovery mechanisms
- [ ] Fallback to text on failure
- [ ] Mobile browser optimization
- [ ] Accessibility features

## Testing Checklist
- [ ] WebSocket text chat still works
- [ ] Ephemeral token generation
- [ ] Microphone permission request
- [ ] WebRTC connection establishment
- [ ] Audio streaming to OpenAI
- [ ] Receiving audio responses
- [ ] Mode switching (text ↔ voice)
- [ ] Error handling and recovery

## Technical Requirements
- **Browser Support**: Chrome 90+, Safari 14+, Edge 90+, Firefox 88+
- **Permissions**: Microphone access required for voice mode
- **Network**: WebRTC compatible (may require STUN/TURN)
- **API**: OpenAI Realtime API with ephemeral tokens

## Important Notes
- WebSocket remains primary for text testing
- WebRTC only activates in voice mode
- Both systems work independently
- Fallback to text if voice fails
- Never expose API keys in frontend code
- Use ephemeral tokens with 1-minute expiry

## Current Architecture
```
Text Mode (WebSocket):
Frontend → WebSocket → Backend → OpenAI Text API

Voice Mode (WebRTC):
Frontend → WebRTC → OpenAI Realtime API (direct P2P)
         ↓
    Ephemeral Token
         ↓
      Backend
```

## Development Guidelines
1. Maintain backward compatibility with text chat
2. Progressive enhancement approach
3. Clear user feedback for mode switching
4. Graceful degradation on failures
5. Security-first implementation