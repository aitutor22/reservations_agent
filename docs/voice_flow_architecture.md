# Voice Flow Architecture - Restaurant RealtimeAgent

## Overview

The voice reservation system uses the OpenAI Agents SDK with RealtimeAgent for voice-enabled conversations. The architecture employs a WebSocket bridge between the browser and backend, where the RealtimeAgent manages the conversation with OpenAI's Realtime API. This design provides full control over the conversation flow while maintaining low latency voice interactions.

https://openai.github.io/openai-agents-python/realtime/guide/

NOTE: the sdk is constantly changing, and this is correct as of Aug 2025
https://github.com/openai/openai-agents-python/tree/main/src/agents/realtime
this is the full code

## Architecture Diagram

```
┌─────────────┐     WebSocket      ┌──────────────┐     OpenAI SDK      ┌────────────┐
│   Browser   │ ◄─────────────────► │   Backend    │ ◄─────────────────► │   OpenAI   │
│ (Vue.js)    │   PCM16/Base64      │ RealtimeAgent│    Session API      │ Realtime   │
└─────────────┘                     └──────────────┘                     └────────────┘
     │                                     │                                    │
     ├─ Audio Capture                      ├─ Session Management                ├─ Speech Recognition
     ├─ PCM16 Conversion                   ├─ Tool Execution                    ├─ Speech Synthesis  
     └─ Audio Playback                     └─ Context Management                └─ VAD Processing
```

## Core Components

### 1. Frontend - VoiceInterface.vue

The voice-first interface with a single microphone button for interaction:

**Audio Capture Pipeline**:
- **MediaRecorder API**: Captures microphone input
- **AudioContext**: Real-time PCM16 conversion at 24kHz
- **ScriptProcessor**: Processes audio in 4096-sample buffers
- **Buffer Management**: Accumulates and sends chunks every ~200-400ms
- **Base64 Encoding**: Converts PCM16 to base64 for WebSocket transport

**Key Implementation Details**:
```javascript
// Audio capture with PCM16 conversion
audioContext = new AudioContext({ sampleRate: 24000 })
audioProcessor = audioContext.createScriptProcessor(4096, 1, 1)

// Convert Float32 to Int16 (PCM16)
for (let i = 0; i < inputData.length; i++) {
  const s = Math.max(-1, Math.min(1, inputData[i]))
  pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
}

// Send chunks with size limits to prevent WebSocket frame errors
const chunksToSend = pcmBuffer.splice(0, Math.min(5, pcmBuffer.length))
```

### 2. WebSocket Communication Layer

**Endpoint**: `ws://localhost:8000/ws/realtime/agent`

**Message Types**:
- `audio_chunk`: Base64-encoded PCM16 audio data
- `text_message`: Text input (fallback option)
- `end_audio`: Signals end of audio input
- `assistant_transcript`: Bot's response transcription
- `user_transcript`: User's speech transcription
- `audio_interrupted`: User interrupted bot
- `audio_end`: Audio response completed

**Frame Size Management**:
- Maximum WebSocket frame: 1MB
- Audio chunks limited to ~700KB base64
- Automatic splitting of oversized chunks
- Periodic buffer flushing every 300ms

### 3. Backend - RestaurantRealtimeSession

**File**: `backend/realtime_agent.py`

The core session manager using OpenAI Agents SDK:

```python
class RestaurantRealtimeSession:
    def __init__(self):
        self.agent = None
        self.runner = None
        self.session = None
        self.session_context = None
        self.is_running = False
```

**Key Components**:

1. **RealtimeAgent Configuration**:
   ```python
   self.agent = RealtimeAgent(
       name="SakuraRamenAssistant",
       instructions="Friendly voice assistant for Sakura Ramen House...",
       tools=[get_restaurant_hours, make_reservation, ...]
   )
   ```

2. **RealtimeRunner Setup**:
   ```python
   self.runner = RealtimeRunner(
       starting_agent=self.agent,
       config={
           "model_settings": {
               "model_name": "gpt-4o-realtime-preview-2024-12-17",
               "voice": "verse",
               "modalities": ["text", "audio"],
               "turn_detection": {
                   "type": "server_vad",
                   "threshold": 0.5,
                   "silence_duration_ms": 500
               }
           }
       }
   )
   ```

3. **Session Lifecycle with Context Manager**:
   ```python
   # Proper session initialization
   self.session_context = await self.runner.run()
   self.session = await self.session_context.__aenter__()
   
   # Proper cleanup
   await self.session_context.__aexit__(None, None, None)
   ```

### 4. Restaurant-Specific Tools

The RealtimeAgent has access to custom function tools:

- `get_current_time()`: Current time information
- `get_restaurant_hours()`: Operating hours
- `get_restaurant_location()`: Address and contact
- `get_menu_info()`: Ramen varieties and prices
- `check_availability()`: Table availability check
- `make_reservation()`: Create reservations

## Audio Data Flow

### Input Flow (User → Assistant)

1. **Browser Audio Capture**:
   - getUserMedia() with constraints: 24kHz, mono, echo cancellation
   - Real-time Float32 → Int16 conversion
   - Buffer accumulation (4096 samples per chunk)

2. **Frontend Processing**:
   - Combine buffers (max 5 buffers/~400ms)
   - Convert to base64 string
   - Size validation (<700KB per chunk)
   - Send via WebSocket

3. **Backend Processing**:
   - Receive base64 audio string
   - Decode to PCM16 bytes
   - Forward to RealtimeAgent session
   - Session handles speech recognition

4. **OpenAI Processing**:
   - Speech-to-text (Whisper)
   - Intent understanding
   - Tool execution if needed
   - Response generation

### Output Flow (Assistant → User)

1. **OpenAI Response**:
   - Text-to-speech generation
   - PCM16 audio at 24kHz
   - Base64-encoded chunks in events

2. **Backend Processing**:
   - Receive `response.audio.delta` events
   - Decode base64 to bytes
   - Forward as binary WebSocket frames

3. **Frontend Playback**:
   - Receive binary audio data
   - Queue management for smooth playback
   - Web Audio API for PCM16 playback
   - Interrupt handling for VAD

## Voice Activity Detection (VAD)

### Configuration

Server-side VAD managed by OpenAI:
- **Type**: `server_vad` 
- **Threshold**: 0.5 (sensitivity)
- **Prefix Padding**: 300ms (capture before speech)
- **Silence Duration**: 500ms (end detection)

### Key Lessons Learned

1. **Don't Manage Interruption State**:
   - ❌ Wrong: Track `audio_interrupted` flag to block sends
   - ✅ Right: Let RealtimeSession handle interruptions internally
   - The session automatically manages audio truncation and turn-taking

2. **Audio Truncation Errors Are Recoverable**:
   - Error: "Audio content of Xms is already shorter than Yms"
   - Cause: Continuing to send audio after interruption
   - Solution: Treat as warning, continue session

3. **Proper Event Handling**:
   ```python
   # Just notify, don't block
   elif event_type == "audio_interrupted":
       print("Audio interrupted by user")
       yield {"type": "audio_interrupted"}
   ```

## WebSocket Frame Size Management

### The Problem
WebSocket frames have a 1MB limit. Audio accumulation can exceed this.

### Solutions Implemented

1. **Chunk Size Limiting**:
   ```javascript
   // Take at most 5 buffers (~400ms)
   const chunksToSend = pcmBuffer.splice(0, Math.min(5, pcmBuffer.length))
   ```

2. **Size Validation**:
   ```javascript
   if (base64Audio.length > 700000) {
       // Split into smaller pieces
       const firstHalf = pcm16.slice(0, halfLength)
       const secondHalf = pcm16.slice(halfLength)
   }
   ```

3. **Periodic Flushing**:
   ```javascript
   setInterval(() => {
       if (pcmBuffer.length > 0) {
           sendPCM16Chunk()
       }
   }, 300) // Every 300ms
   ```

## Session Management Best Practices

### Context Manager Pattern

Always use async context managers for session lifecycle:

```python
# Correct approach (from OpenAI example)
async def start_session(self):
    self.session_context = await self.runner.run()
    self.session = await self.session_context.__aenter__()

async def stop_session(self):
    if self.session_context:
        await self.session_context.__aexit__(None, None, None)
```

### Error Recovery

Not all errors are fatal:

```python
if "already shorter than" in error_str:
    # Audio sync issue - recoverable
    yield {"type": "warning", "message": "Audio sync issue"}
    # Continue session
else:
    # Fatal error
    self.is_running = False
    break
```

## Common Pitfalls and Solutions

### 1. VAD Interruption Handling

**Problem**: Bot stops responding after interruption
**Mistake**: Managing interruption state manually
**Solution**: Remove state management, let session handle it

### 2. WebSocket Frame Size

**Problem**: "Frame exceeds limit of 1048576 bytes"
**Mistake**: Sending entire audio buffer at once
**Solution**: Chunk limiting and size validation

### 3. Session Lifecycle

**Problem**: Session dies with "sent 1009" errors
**Mistake**: Not using context managers properly
**Solution**: Follow OpenAI's example pattern

### 4. Audio Format

**Problem**: "Invalid audio format" errors
**Mistake**: Sending wrong format or encoding
**Solution**: PCM16, 24kHz, mono, base64-encoded

### 5. Timing Issues

**Problem**: Audio truncation errors during interruptions
**Mistake**: Continuing to send audio after interruption
**Solution**: Handle as recoverable warning

## Performance Optimizations

### Audio Processing
- Buffer size: 4096 samples (optimal for real-time)
- Chunk frequency: Every 200-400ms
- Maximum chunk: 5 buffers (~400ms audio)
- Base64 size limit: 700KB per chunk

### Network Efficiency
- WebSocket binary frames for audio responses
- JSON for control messages only
- Periodic buffer flushing
- Size validation before sending

### Resource Management
- Proper AudioContext cleanup
- MediaStream track stopping
- Interval timer cleanup
- Session context cleanup

## Monitoring and Debugging

### Key Metrics

1. **Audio Quality**:
   - Chunk sizes (should be <700KB)
   - Send frequency (every 200-400ms)
   - Buffer accumulation

2. **Session Health**:
   - Interruption frequency
   - Error recovery rate
   - Session duration

3. **Tool Execution**:
   - Tool call success rate
   - Response times
   - Error handling

### Debug Logging

```javascript
// Frontend
console.log(`Sending audio chunk: ${sizeKB}KB`)

// Backend
print(f"[RestaurantAgent] Audio interrupted by user")
print(f"[RestaurantAgent] Calling tool: {tool_name}")
```

## Comparison: WebSocket vs WebRTC Approach

| Aspect | Our WebSocket Approach | Direct WebRTC |
|--------|------------------------|---------------|
| **Architecture** | Browser → Backend → OpenAI | Browser → OpenAI |
| **Control** | Full (custom tools, context) | Limited (no custom tools) |
| **Latency** | ~500-800ms | <500ms |
| **Complexity** | Moderate | High |
| **Tool Support** | Yes (full SDK) | No |
| **Session Management** | Backend controlled | Client controlled |
| **Error Recovery** | Easier | Harder |
| **Scalability** | Backend-limited | Excellent |

## Why We Chose WebSocket + RealtimeAgent

1. **Custom Tools**: Restaurant-specific functionality (reservations, menu)
2. **Control**: Full conversation management and context
3. **Simplicity**: Easier to debug and maintain
4. **Flexibility**: Can modify behavior without client updates
5. **Consistency**: Same backend for voice and text

## Future Enhancements

### Immediate Improvements
1. **Connection pooling**: Reuse sessions for efficiency
2. **Audio compression**: Reduce bandwidth usage
3. **Retry logic**: Automatic reconnection on failures
4. **Metric collection**: Performance monitoring

### Long-term Goals
1. **Multi-language support**: Dynamic voice selection
2. **Conversation history**: Persistent context
3. **Advanced tools**: Payment processing, loyalty programs
4. **Analytics**: Conversation insights and patterns
5. **Fallback strategies**: Graceful degradation

## Conclusion

The WebSocket + RealtimeAgent architecture provides the perfect balance of control and performance for a restaurant voice assistant. By learning from common pitfalls (especially around VAD and session management), we've built a robust system that handles real-world conversation patterns while maintaining the ability to execute restaurant-specific operations through custom tools.

The key insight: Let the OpenAI SDK handle the complex parts (VAD, audio processing) while focusing on business logic and user experience.