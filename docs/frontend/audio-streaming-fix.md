# Audio Streaming Architecture Fix Documentation

## Problem Statement

The voice interface was experiencing intermittent static and glitches in both:
1. **Audio recording**: When sending user's voice to OpenAI
2. **Audio playback**: When playing OpenAI's response

## Root Causes Identified

### Recording Issues
- **Variable chunk sizes**: Buffering 2-5 chunks (340-850ms) created inconsistent timing
- **Async flush timer**: 300ms periodic flush conflicted with 170ms audio processing, causing race conditions
- **Buffer accumulation**: Large chunks exceeded OpenAI's recommended 40ms size by 10-20x

### Playback Issues
- **Gap-based scheduling**: Using `onended` events created 5-20ms gaps between chunks
- **JavaScript thread jitter**: Event-based playback suffered from garbage collection and execution delays
- **No scheduling precision**: JavaScript timers have ~5-20ms variance vs audio thread's 0.02ms precision

## Solutions Implemented

### 1. Recording: Aligned with OpenAI Best Practices

**Before:**
```javascript
// 4096 samples = 170ms chunks
this.audioProcessor = createScriptProcessor(4096, 1, 1)
// Accumulated 2-5 buffers before sending
// Had 300ms flush timer racing with audio processor
```

**After:**
```javascript
// 1024 samples = 43ms chunks (closest power of 2 to OpenAI's 40ms)
this.audioProcessor = createScriptProcessor(1024, 1, 1)
// Send immediately - no buffering, no flush timer
```

**Benefits:**
- Consistent 43ms chunks match OpenAI's recommendation
- No timing conflicts or race conditions
- Better Voice Activity Detection (VAD) responsiveness
- Simpler, more maintainable code

### 2. Playback: Scheduled Audio with Precise Timing

**Before:**
```javascript
source.onended = () => {
  playNextInQueue() // Gap between chunks!
}
source.start(0)
```

**After:**
```javascript
// Track exact timing
if (nextPlayTime < audioContext.currentTime) {
  nextPlayTime = audioContext.currentTime + 0.05 // 50ms buffer
}
source.start(nextPlayTime) // Precise scheduling
nextPlayTime += audioBuffer.duration // No gaps!
```

**Benefits:**
- Zero gaps between audio chunks
- Uses audio thread's high-precision scheduler (0.02ms accuracy)
- Handles network jitter with 50ms initial buffer
- Eliminates clicks/pops at chunk boundaries

## Technical Details

### PCM16 Audio Format
- **Sample Rate**: 24,000 Hz (OpenAI requirement)
- **Bit Depth**: 16-bit signed integers (-32768 to 32767)
- **Channels**: Mono (1 channel)
- **Byte Order**: Little-endian
- **Chunk Size**: ~43ms (1024 samples)

### Conversion Pipeline

#### Recording (Float32 → PCM16):
```javascript
// Browser captures as Float32 [-1.0, 1.0]
const s = Math.max(-1, Math.min(1, inputData[i]))
// Convert to Int16 [-32768, 32767]
pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
```

#### Playback (PCM16 → Float32):
```javascript
// Receive as Int16 [-32768, 32767]
// Convert to Float32 [-1.0, 1.0]
float32Array[i] = int16Array[i] / 32768.0
```

### WebSocket Protocol

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "audio": "<base64_encoded_pcm16>"
}
```

**Server → Client:**
- Binary frames containing raw PCM16 bytes
- Maximum frame size: 512KB (respects sample boundaries)

## Performance Metrics

### Before Fix
- Chunk size variance: 340-850ms
- Timing jitter: 5-20ms between chunks
- Audio artifacts: Clicks, pops, static
- Latency: Inconsistent due to buffering

### After Fix
- Chunk size: Consistent 43ms
- Timing precision: <0.02ms (audio thread)
- Audio quality: Smooth, continuous
- Latency: Predictable 50ms initial buffer

## Best Practices Applied

1. **Follow API specifications**: Use recommended chunk sizes
2. **Leverage platform capabilities**: Use Web Audio API's scheduling
3. **Avoid JavaScript timing**: Use audio thread for precision
4. **Handle network variability**: Add small latency buffer
5. **Keep it simple**: Remove unnecessary buffering logic

## Troubleshooting Guide

### If static returns:
1. Check browser console for chunk size logs
2. Verify sample rate matches (24kHz)
3. Ensure WebSocket frames < 1MB
4. Check for JavaScript errors blocking audio thread

### Common issues:
- **"AudioContext not allowed"**: User must interact with page first
- **"createScriptProcessor is deprecated"**: Still works, AudioWorklet is future
- **Network delays**: Increase initial buffer from 50ms to 100ms if needed

## Future Improvements

1. **AudioWorklet**: Replace deprecated ScriptProcessor
2. **Adaptive buffering**: Adjust latency based on network conditions
3. **Opus compression**: Reduce bandwidth usage
4. **WebRTC DataChannel**: Lower latency than WebSocket
5. **Visualizations**: Add waveform/spectrum display

## References

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Web Audio API Specification](https://webaudio.github.io/web-audio-api/)
- [PCM Audio Format](https://en.wikipedia.org/wiki/Pulse-code_modulation)
- [AudioContext.currentTime scheduling](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/currentTime)

## Implementation Files

- **Frontend Recording**: `/frontend/src/components/VoiceInterface.vue`
- **Frontend Playback**: `/frontend/src/store/index.js`
- **Backend Processing**: `/backend/realtime_agents/session_manager.py`
- **WebSocket Handler**: `/backend/main.py`

---

*Last Updated: 2025*
*Fixed Issues: Audio static, timing glitches, chunk synchronization*