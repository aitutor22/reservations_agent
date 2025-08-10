# Handoff Audio Delay Implementation

## Problem Statement
The OpenAI Realtime API provides instant agent handoffs, which feel unnatural in a phone conversation context. Users expect a brief pause during transfers, similar to real phone systems.

## Challenge
The OpenAI Realtime API does not support:
- Direct pause or silence insertion in speech synthesis
- Delay commands between agent transitions
- Timing control for handoff events

Text prompts like "wait 2 seconds before speaking" are ignored by the model as they don't control actual audio output.

## Solution: Client-Side Silence Buffer Injection

### Overview
We inject PCM16 silence buffers into the audio stream when handoff events are detected, creating a natural pause before the new agent speaks.

### Implementation Details

#### 1. Detection (session_manager.py)
```python
# Monitor for handoff tool calls in event stream
elif inner_type == 'response.function_call_arguments.done':
    tool_name = raw_data.get('name', 'unknown')
    
    # Detect handoff by tool name patterns
    is_handoff = (
        'transfer' in tool_name_lower or 
        'handoff' in tool_name_lower or
        'specialist' in tool_name_lower or
        'sakura' in tool_name_lower  # Our agents contain "Sakura"
    )
```

#### 2. Silence Generation
```python
def generate_silence_buffer(self, duration_seconds: float = 2.0) -> bytes:
    """Generate PCM16 silence buffer"""
    num_samples = int(24000 * duration_seconds)  # 24kHz sample rate
    silence_array = np.zeros(num_samples, dtype=np.int16)
    return silence_array.tobytes()
```

#### 3. Injection
```python
if is_handoff:
    self.handoff_pending = True
    silence_buffer = self.generate_silence_buffer()
    
    # Send silence as audio chunk
    yield {
        "type": "audio_chunk",
        "data": silence_buffer  # 48,000 zero samples = 2 seconds
    }
```

#### 4. Recovery
```python
# Clear flag when new agent starts speaking
elif inner_type == 'response.audio.delta':
    if self.handoff_pending:
        print("[RestaurantAgent] New agent starting to speak after handoff")
        self.handoff_pending = False
```

### Audio Specifications
- **Sample Rate**: 24,000 Hz (OpenAI requirement)
- **Format**: PCM16 (16-bit signed integers)
- **Duration**: 2 seconds
- **Buffer Size**: 96,000 bytes (48,000 samples × 2 bytes/sample)

### Benefits
1. **Natural Feel**: Simulates real phone transfer delays
2. **No API Changes**: Works with existing OpenAI Realtime API
3. **Configurable**: Easy to adjust delay duration
4. **Reliable**: Doesn't depend on model behavior

### Alternative Approaches Considered

#### 1. Model Instructions (Failed)
- Adding "pause for 2 seconds" to agent instructions
- Result: Ignored by model, no actual pause in audio

#### 2. VAD Settings (Limited)
- Increasing `silence_duration_ms` to 2000ms
- Result: Affects all pauses, makes conversation sluggish

#### 3. Frontend Delay (Complex)
- JavaScript timer-based pause
- Result: Requires complex synchronization, less reliable

### Future Improvements
- Add optional transition sound/tone during pause
- Make delay duration configurable per handoff type
- Consider shorter delays for certain transfers

## Testing
To verify the implementation:
1. Initiate a conversation requiring handoff
2. Request a reservation or ask for detailed menu info
3. Observe 2-second pause after "One moment, please"
4. Confirm new agent greets naturally after pause

## References
- OpenAI Realtime API does not currently support direct timing control
- PCM16 audio format: 16-bit signed integers, -32768 to 32767 range
- NumPy zeros create silence when interpreted as audio samples