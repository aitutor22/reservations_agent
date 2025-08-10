<template>
  <div class="voice-interface">
    <!-- Header -->
    <div class="header">
      <h1 class="title">Sakura Ramen House</h1>
      <div class="status-indicator" :class="connectionStatus">
        <span class="status-dot"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </div>

    <!-- Main Voice Button -->
    <div class="voice-container">
      <button 
        class="voice-button"
        :class="{ 'recording': isRecording, 'disabled': !isConnected }"
        @click="toggleRecording"
        :disabled="!isConnected"
      >
        <svg 
          class="mic-icon"
          width="48" 
          height="48" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2"
        >
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" y1="19" x2="12" y2="23"></line>
          <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
      </button>
      <p class="voice-hint">{{ buttonHint }}</p>
    </div>

    <!-- Transcript Toggle Button -->
    <button 
      class="transcript-toggle"
      @click="showTranscript = !showTranscript"
      :title="showTranscript ? 'Hide transcript' : 'Show transcript'"
    >
      <svg 
        width="24" 
        height="24" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2"
      >
        <path v-if="showTranscript" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle v-if="showTranscript" cx="12" cy="12" r="3"></circle>
        <path v-if="!showTranscript" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line v-if="!showTranscript" x1="1" y1="1" x2="23" y2="23"></line>
      </svg>
      <span class="toggle-label">{{ showTranscript ? 'Hide' : 'Show' }} Transcript</span>
    </button>

    <!-- Transcript Display (minimal) -->
    <div class="transcript-container" v-if="showTranscript">
      <div class="transcript-messages">
        <div 
          v-for="message in recentMessages" 
          :key="message.id"
          class="transcript-message"
          :class="message.role"
        >
          <span class="message-role">{{ message.role === 'user' ? 'You' : 'Assistant' }}:</span>
          <span class="message-text">{{ message.content }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * VoiceInterface.vue - Real-time Voice Recording and Processing Component
 * 
 * This component handles voice input for the Restaurant RealtimeAgent, converting
 * browser-captured audio to PCM16 format required by OpenAI's Realtime API.
 * 
 * AUDIO PROCESSING PIPELINE:
 * 1. Microphone → getUserMedia (native browser audio)
 * 2. MediaStream → AudioContext (Web Audio API processing)
 * 3. Float32 samples → PCM16 conversion (format required by OpenAI)
 * 4. PCM16 chunks → Base64 encoding (for WebSocket transport)
 * 5. WebSocket → Backend RealtimeAgent → OpenAI
 * 
 * WHY PCM16?
 * - PCM16 (Pulse Code Modulation, 16-bit) is the standard format for OpenAI's Realtime API
 * - It's an uncompressed audio format that represents audio as raw sample values
 * - Each sample is a 16-bit signed integer (-32768 to 32767)
 * - Provides good quality for speech at reasonable file sizes
 * - Standard format for telephony and voice applications
 * 
 * WHY NOT RECORD DIRECTLY AS PCM16?
 * - Browsers don't natively record in PCM16 format
 * - getUserMedia provides audio as Float32 values (-1.0 to 1.0)
 * - MediaRecorder API outputs compressed formats (WebM/Ogg)
 * - We need real-time streaming, not post-processing of recorded files
 * - ScriptProcessor allows us to access raw audio samples for conversion
 * 
 * TECHNICAL DETAILS:
 * - Sample Rate: 24,000 Hz (24kHz) - OpenAI's requirement for optimal speech
 * - Channels: 1 (mono) - Speech doesn't need stereo
 * - Buffer Size: 1024 samples (~43ms at 24kHz) - Closest power of 2 to OpenAI's 40ms
 * - Chunk Frequency: Every ~43ms for real-time streaming
 * - No buffering: Send immediately for lowest latency and best VAD response
 */

import { mapState, mapActions } from 'vuex'

export default {
  name: 'VoiceInterface',
  data() {
    return {
      isRecording: false,
      mediaRecorder: null,      // Not used - kept for reference
      audioContext: null,        // Web Audio API context for processing
      audioProcessor: null,      // ScriptProcessor node for real-time conversion
      showTranscript: false,     // Default to hidden for cleaner UI
      mediaStream: null         // Reference to microphone stream for cleanup
    }
  },
  computed: {
    ...mapState({
      connectionStatus: state => state.connectionStatus,
      messages: state => state.messages
    }),
    isConnected() {
      return this.connectionStatus === 'connected'
    },
    statusText() {
      switch(this.connectionStatus) {
        case 'connecting':
          return 'Connecting...'
        case 'connected':
          return 'Ready'
        case 'error':
          return 'Connection Error'
        default:
          return 'Not Connected'
      }
    },
    buttonHint() {
      if (!this.isConnected) {
        return 'Connecting to assistant...'
      }
      if (this.isRecording) {
        return 'Click to stop recording'
      }
      return 'Click to start speaking'
    },
    recentMessages() {
      // Show last 5 messages
      return this.messages.slice(-5)
    }
  },
  methods: {
    ...mapActions(['connectRealtimeAgent', 'sendAudioToAgent']),
    
    async toggleRecording() {
      if (!this.isConnected) return
      
      if (this.isRecording) {
        await this.stopRecording()
      } else {
        await this.startRecording()
      }
    },
    
    /**
     * Start audio recording and real-time PCM16 conversion
     * This is where we capture microphone audio and convert it to the format OpenAI expects
     */
    async startRecording() {
      try {
        // Step 1: Request microphone access with specific constraints
        // These constraints ensure we get audio in a format we can process efficiently
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,        // Mono audio (speech doesn't need stereo)
            sampleRate: 24000,      // 24kHz - OpenAI's required sample rate
            echoCancellation: true, // Remove echo from speakers
            noiseSuppression: true  // Reduce background noise
          } 
        })
        
        // Step 2: Create AudioContext for audio processing
        // AudioContext is the Web Audio API's main interface for processing audio
        // We specify 24kHz to match OpenAI's requirements
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000
        })
        
        // Step 3: Create audio source from microphone stream
        const source = this.audioContext.createMediaStreamSource(stream)
        
        // Step 4: Create ScriptProcessor for real-time audio processing
        // ScriptProcessor (deprecated but still widely used) gives us access to raw audio samples
        // Parameters: bufferSize (1024), inputChannels (1), outputChannels (1)
        // 1024 samples at 24kHz = ~43ms of audio per buffer (closest power of 2 to OpenAI's 40ms)
        this.audioProcessor = this.audioContext.createScriptProcessor(1024, 1, 1)
        
        // Step 5: Process audio in real-time - this is called ~23 times per second (every 43ms)
        this.audioProcessor.onaudioprocess = (event) => {
          // Get Float32 audio data from the input buffer
          // Float32 values range from -1.0 to 1.0
          const inputData = event.inputBuffer.getChannelData(0)
          
          // Convert Float32 to Int16 (PCM16)
          // This is the critical conversion that OpenAI requires
          const pcm16 = new Int16Array(inputData.length)
          for (let i = 0; i < inputData.length; i++) {
            // Step 5a: Clamp to prevent overflow (should already be -1 to 1, but be safe)
            const s = Math.max(-1, Math.min(1, inputData[i]))
            
            // Step 5b: Scale from Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
            // Negative values: -1.0 * 32768 = -32768 (0x8000)
            // Positive values: 1.0 * 32767 = 32767 (0x7FFF)
            // Note the asymmetry: we use 0x7FFF for positive to avoid overflow
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
          }
          
          // Step 6: Send immediately - OpenAI best practice for 40ms chunks
          // Convert PCM16 binary data to base64 string for WebSocket transport
          const base64Audio = this.arrayBufferToBase64(pcm16.buffer)
          
          // Send base64-encoded PCM16 audio via WebSocket
          this.$store.dispatch('sendAudioChunk', base64Audio)
        }
        
        // Step 7: Connect the audio processing pipeline
        // source (mic) → audioProcessor (conversion) → destination (speakers for monitoring)
        source.connect(this.audioProcessor)
        this.audioProcessor.connect(this.audioContext.destination)
        
        this.isRecording = true
        console.log('Recording started with PCM16 conversion (43ms chunks)')
        
        // Store stream reference for cleanup
        this.mediaStream = stream
        
      } catch (error) {
        console.error('Failed to start recording:', error)
        this.$store.commit('ADD_MESSAGE', {
          content: 'Failed to access microphone. Please check permissions.',
          role: 'system'
        })
      }
    },
    
    async stopRecording() {
      this.isRecording = false
      
      // Clean up audio processing
      if (this.audioProcessor) {
        this.audioProcessor.disconnect()
        this.audioProcessor = null
      }
      
      if (this.audioContext) {
        this.audioContext.close()
        this.audioContext = null
      }
      
      // Stop all tracks to release microphone
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
      
      console.log('Recording stopped')
      
      // Send end of audio signal
      this.sendEndOfAudio()
    },
    
    /**
     * Convert binary ArrayBuffer to base64 string
     * Required for sending binary audio data over WebSocket text frames
     * 
     * @param {ArrayBuffer} buffer - Binary audio data (PCM16 format)
     * @returns {string} Base64-encoded string
     */
    arrayBufferToBase64(buffer) {
      const bytes = new Uint8Array(buffer)
      let binary = ''
      // Convert bytes to binary string
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i])
      }
      // Encode binary string as base64
      return btoa(binary)
    },
    
    sendEndOfAudio() {
      // Signal end of audio input
      this.$store.dispatch('sendEndOfAudio')
    }
  },
  mounted() {
    // Connect to Restaurant RealtimeAgent on mount
    this.connectRealtimeAgent()
  },
  beforeDestroy() {
    // Clean up recording if active
    if (this.isRecording) {
      this.stopRecording()
    }
    
    // Disconnect WebSocket
    if (this.$store.state.websocket) {
      this.$store.state.websocket.close()
    }
  }
}
</script>

<style lang="scss" scoped>
.voice-interface {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  position: relative;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
  color: white;
  
  .title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 1rem;
  }
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2rem;
  backdrop-filter: blur(10px);
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }
  
  .status-text {
    font-size: 0.9rem;
    font-weight: 500;
  }
  
  &.connected {
    color: #10b981;
    .status-dot {
      background: #10b981;
    }
  }
  
  &.connecting {
    color: #f59e0b;
    .status-dot {
      background: #f59e0b;
      animation: pulse 1s infinite;
    }
  }
  
  &.error {
    color: #ef4444;
    .status-dot {
      background: #ef4444;
    }
  }
  
  &.idle {
    color: #6b7280;
    .status-dot {
      background: #6b7280;
    }
  }
}

.voice-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.voice-button {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  position: relative;
  
  &:hover:not(.disabled) {
    transform: scale(1.05);
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3);
  }
  
  &:active:not(.disabled) {
    transform: scale(0.95);
  }
  
  &.recording {
    background: #ef4444;
    animation: pulse-recording 1.5s infinite;
    
    .mic-icon {
      color: white;
    }
    
    &::before {
      content: '';
      position: absolute;
      top: -20px;
      left: -20px;
      right: -20px;
      bottom: -20px;
      border-radius: 50%;
      border: 3px solid rgba(239, 68, 68, 0.3);
      animation: ripple 1.5s infinite;
    }
  }
  
  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      transform: none;
    }
  }
  
  .mic-icon {
    color: #667eea;
    transition: color 0.3s ease;
  }
}

.voice-hint {
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  text-align: center;
  opacity: 0.9;
}

.transcript-toggle {
  position: absolute;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 2rem;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
  
  .toggle-label {
    @media (max-width: 640px) {
      display: none; // Hide label on mobile, show icon only
    }
  }
}

.transcript-container {
  position: absolute;
  bottom: 2rem;
  left: 2rem;
  right: 2rem;
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 1rem;
  padding: 1rem;
  max-height: 120px;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.transcript-messages {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.transcript-message {
  display: flex;
  gap: 0.5rem;
  font-size: 0.9rem;
  line-height: 1.4;
  
  .message-role {
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .message-text {
    color: #4a5568;
  }
  
  &.user {
    .message-role {
      color: #667eea;
    }
  }
  
  &.agent {
    .message-role {
      color: #764ba2;
    }
  }
  
  &.system {
    .message-role {
      color: #6b7280;
    }
    .message-text {
      font-style: italic;
    }
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

@keyframes pulse-recording {
  0% {
    box-shadow: 0 10px 40px rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 10px 50px rgba(239, 68, 68, 0.6);
  }
  100% {
    box-shadow: 0 10px 40px rgba(239, 68, 68, 0.4);
  }
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

@media (max-width: 640px) {
  .header {
    .title {
      font-size: 2rem;
    }
    .subtitle {
      font-size: 1rem;
    }
  }
  
  .voice-button {
    width: 120px;
    height: 120px;
    
    .mic-icon {
      width: 36px;
      height: 36px;
    }
  }
  
  .voice-hint {
    font-size: 1rem;
  }
  
  .transcript-toggle {
    bottom: 1rem;
    right: 1rem;
    padding: 0.5rem 0.75rem;
  }
  
  .transcript-container {
    left: 1rem;
    right: 1rem;
    bottom: 1rem;
    max-height: 100px;
    padding: 0.75rem;
  }
  
  .transcript-message {
    font-size: 0.85rem;
  }
}
</style>