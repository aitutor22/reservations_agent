# Voice Flow Architecture

## Overview

The voice reservation system uses WebRTC for real-time voice communication, establishing a direct connection between the user's browser and OpenAI's Realtime API. This architecture ensures low latency (<500ms) voice interactions while minimizing backend server load.

## Communication Flow

### 1. Initial Setup (Backend Hit)

**Endpoint**: `POST /api/realtime/session` (backend/main.py:151-229)

This is the only backend interaction in the WebRTC flow:

- **Token Generation**: Backend requests an ephemeral token from OpenAI API
- **Token Validity**: 60 seconds from creation
- **Response Payload**:
  ```json
  {
    "session_id": "uuid",
    "ephemeral_key": "eph_xxx",
    "expires_at": 1234567890,
    "model": "gpt-4o-realtime-preview-2024-12-17",
    "voice": "verse",
    "instructions": "...",
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500
    }
  }
  ```

### 2. WebRTC Connection Setup (Direct to OpenAI)

**No backend involvement from this point forward**

#### Connection Process (frontend/src/services/webrtc.js):

1. **Create RTCPeerConnection** (line 45)
   ```javascript
   config: {
     iceServers: [
       { urls: 'stun:stun.l.google.com:19302' }
     ]
   }
   ```

2. **Setup Local Audio Stream** (lines 82-108)
   - Request microphone permissions
   - Configure audio constraints:
     ```javascript
     audio: {
       echoCancellation: true,
       noiseSuppression: true,
       autoGainControl: true,
       sampleRate: 24000,  // OpenAI requirement
       channelCount: 1      // Mono audio
     }
     ```

3. **Create Data Channel** (lines 114-154)
   - Channel name: `oai-events`
   - Ordered delivery: true
   - Handles bidirectional event communication

4. **SDP Exchange** (lines 208-234)
   - Create local offer
   - Send SDP to: `https://api.openai.com/v1/realtime`
   - Headers: `Authorization: Bearer ${ephemeralToken}`
   - Receive and set remote answer

### 3. Audio Processing Pipeline

#### Input (User ’ OpenAI):
- **Capture**: Browser getUserMedia API
- **Format**: PCM16 (16-bit PCM audio)
- **Sample Rate**: 24kHz mono
- **Transport**: WebRTC audio track
- **Processing**: Real-time echo cancellation, noise suppression

#### Output (OpenAI ’ User):
- **Format**: PCM16
- **Delivery**: Via `ontrack` event (line 161)
- **Playback**: HTML Audio element with autoplay
- **Stream**: Continuous audio streaming

### 4. Data Channel Events

The data channel (`oai-events`) handles all non-audio communication:

#### Outbound Events (Browser ’ OpenAI):
- `session.update` - Configure session parameters
- `conversation.item.create` - Send text messages
- `response.create` - Trigger response generation
- `input_audio_buffer.commit` - Signal end of audio input

#### Inbound Events (OpenAI ’ Browser):
- `session.created` - Session initialization confirmed
- `session.updated` - Configuration changes acknowledged
- `conversation.item.created` - New conversation items (transcripts)
- `response.audio.delta` - Audio streaming in progress
- `response.audio.done` - Audio response complete
- `error` - Error notifications

## Session Lifecycle

### 1. Session Creation
- Frontend requests ephemeral token from backend
- Token valid for 60 seconds
- Multiple sessions can exist simultaneously

### 2. Connection States
```
idle ’ connecting ’ connected ’ disconnected
         “             “
       failed        failed
```

### 3. Connection Monitoring
- **RTCPeerConnection states**: Monitor via `onconnectionstatechange`
- **ICE states**: Track via `oniceconnectionstatechange`
- **Auto-reconnection**: Not implemented (requires new token)

### 4. Graceful Disconnection
- Stop all local media tracks
- Close data channel
- Close peer connection
- Clean up audio elements

## Alternative: WebSocket Communication

**Endpoint**: `/ws/{session_id}` (backend/main.py:302-306)

The WebSocket path is an alternative to WebRTC, used when:
- WebRTC is not supported by the browser
- Firewall/network restrictions block WebRTC
- Testing/debugging purposes
- Server-side audio processing is required

### WebSocket vs WebRTC Comparison

| Aspect | WebRTC | WebSocket |
|--------|---------|-----------|
| **Latency** | <500ms | 500-1500ms |
| **Backend Load** | Minimal (token only) | High (all audio) |
| **Audio Path** | Browser ” OpenAI | Browser ” Backend ” OpenAI |
| **Scalability** | Excellent | Limited by backend |
| **Browser Support** | Modern browsers | All browsers |
| **NAT Traversal** | STUN/TURN required | Standard HTTP |

## Voice Activity Detection (VAD)

Server-side VAD configuration:
- **Type**: `server_vad` (OpenAI handles silence detection)
- **Threshold**: 0.5 (sensitivity level)
- **Prefix Padding**: 300ms (capture before speech starts)
- **Silence Duration**: 500ms (end-of-speech detection)

Benefits:
- Automatic turn-taking in conversation
- Reduced latency between user input and response
- Natural conversation flow

## Security Considerations

### 1. Ephemeral Token Model
- **Short-lived**: 60-second validity window
- **Single-use**: One token per session
- **No persistence**: Tokens not stored in backend
- **Scope-limited**: Only allows Realtime API access

### 2. Direct Client Connection Benefits
- Audio never touches your backend servers
- Reduced attack surface (no audio processing vulnerabilities)
- No audio data storage or logging
- End-to-end encryption via WebRTC

### 3. CORS Configuration
- Restricted origins in production
- Credentials required for token endpoint
- WebRTC inherently cross-origin safe

### 4. Authentication Flow
```
User ’ Backend (authenticate) ’ Ephemeral Token
User ’ OpenAI (with token) ’ Direct WebRTC
```

## Error Handling

### Token Expiration
- Monitor token expiry time
- Request new token before expiration
- Graceful reconnection with new token

### Connection Failures
- ICE gathering failures ’ Retry with TURN server
- Network disconnection ’ Show user notification
- OpenAI service issues ’ Fallback to WebSocket

### Audio Permission Denied
- Clear user messaging about microphone requirements
- Fallback to text input mode
- Retry permission request option

## Performance Optimizations

### 1. Audio Configuration
- 24kHz sample rate (optimal for speech)
- Mono channel (reduces bandwidth)
- Hardware echo cancellation when available

### 2. Network Optimization
- STUN for optimal routing
- No video tracks (audio-only)
- Efficient data channel for events

### 3. Resource Management
- Single Audio element reuse
- Proper cleanup on disconnection
- Event listener management

## Monitoring and Debugging

### Key Metrics to Track
- Connection establishment time
- Audio latency (mouth-to-ear)
- Token refresh success rate
- Connection stability (disconnection rate)

### Debug Information
- RTCPeerConnection stats API
- Data channel message logs
- Audio level monitoring
- Network quality indicators

## Future Enhancements

### Planned Improvements
1. **Automatic Reconnection**: Handle token expiry gracefully
2. **TURN Server Support**: For restrictive networks
3. **Audio Recording**: Optional conversation recording
4. **Multi-language Support**: Dynamic voice/language selection
5. **Fallback Strategies**: Automatic WebSocket fallback
6. **Connection Pooling**: Reuse connections across sessions