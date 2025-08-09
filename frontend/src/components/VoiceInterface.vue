<template>
  <div class="voice-interface">
    <!-- Header -->
    <div class="header">
      <h1 class="title">Sakura Ramen House</h1>
      <p class="subtitle">Voice Assistant</p>
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
import { mapState, mapActions } from 'vuex'

export default {
  name: 'VoiceInterface',
  data() {
    return {
      isRecording: false,
      mediaRecorder: null,
      audioContext: null,
      audioProcessor: null,
      pcmBuffer: [],
      showTranscript: true
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
    
    async startRecording() {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 24000,
            echoCancellation: true,
            noiseSuppression: true
          } 
        })
        
        // Create AudioContext for PCM16 conversion
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000
        })
        
        const source = this.audioContext.createMediaStreamSource(stream)
        
        // Create ScriptProcessor for real-time PCM conversion
        // 4096 samples buffer size, 1 input channel, 1 output channel
        this.audioProcessor = this.audioContext.createScriptProcessor(4096, 1, 1)
        
        this.pcmBuffer = []
        
        // Process audio in real-time
        this.audioProcessor.onaudioprocess = (event) => {
          const inputData = event.inputBuffer.getChannelData(0)
          
          // Convert Float32 to Int16 (PCM16)
          const pcm16 = new Int16Array(inputData.length)
          for (let i = 0; i < inputData.length; i++) {
            // Clamp values between -1 and 1, then scale to Int16
            const s = Math.max(-1, Math.min(1, inputData[i]))
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
          }
          
          // Add to buffer
          this.pcmBuffer.push(pcm16)
          
          // Send chunks every ~200ms worth of audio (approx 2 buffers)
          // This reduces network overhead and avoids overwhelming the session
          if (this.pcmBuffer.length >= 2) {
            this.sendPCM16Chunk()
          }
        }
        
        // Connect audio nodes
        source.connect(this.audioProcessor)
        this.audioProcessor.connect(this.audioContext.destination)
        
        this.isRecording = true
        console.log('Recording started with PCM16 conversion')
        
        // Store stream reference for cleanup
        this.mediaStream = stream
        
        // Also periodically flush buffer to prevent accumulation
        this.flushInterval = setInterval(() => {
          if (this.pcmBuffer.length > 0 && this.isRecording) {
            this.sendPCM16Chunk()
          }
        }, 300) // Flush every 300ms
        
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
      
      // Clear flush interval
      if (this.flushInterval) {
        clearInterval(this.flushInterval)
        this.flushInterval = null
      }
      
      // Send any remaining buffered audio
      if (this.pcmBuffer.length > 0) {
        this.sendPCM16Chunk()
      }
      
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
    
    sendPCM16Chunk() {
      if (this.pcmBuffer.length === 0) return
      
      // Limit chunk size to prevent WebSocket frame size errors
      // Take at most 5 buffers (~400ms of audio) at a time
      const chunksToSend = this.pcmBuffer.splice(0, Math.min(5, this.pcmBuffer.length))
      
      // Combine the chunks to send
      const totalLength = chunksToSend.reduce((sum, chunk) => sum + chunk.length, 0)
      const combinedPCM16 = new Int16Array(totalLength)
      let offset = 0
      
      for (const chunk of chunksToSend) {
        combinedPCM16.set(chunk, offset)
        offset += chunk.length
      }
      
      // Convert Int16Array to base64
      const base64Audio = this.arrayBufferToBase64(combinedPCM16.buffer)
      
      // Check size before sending (base64 is ~1.33x larger than binary)
      // Max safe size: ~700KB binary -> ~930KB base64
      if (base64Audio.length > 700000) {
        console.warn('Audio chunk too large, splitting...')
        // If still too large, send in smaller pieces
        const halfLength = Math.floor(combinedPCM16.length / 2)
        const firstHalf = combinedPCM16.slice(0, halfLength)
        const secondHalf = combinedPCM16.slice(halfLength)
        
        this.$store.dispatch('sendAudioChunk', this.arrayBufferToBase64(firstHalf.buffer))
        setTimeout(() => {
          this.$store.dispatch('sendAudioChunk', this.arrayBufferToBase64(secondHalf.buffer))
        }, 50)
      } else {
        // Send base64-encoded PCM16 audio
        this.$store.dispatch('sendAudioChunk', base64Audio)
      }
    },
    
    arrayBufferToBase64(buffer) {
      const bytes = new Uint8Array(buffer)
      let binary = ''
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i])
      }
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
  max-height: 200px;
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
  
  .transcript-container {
    left: 1rem;
    right: 1rem;
    bottom: 1rem;
    max-height: 150px;
    padding: 0.75rem;
  }
  
  .transcript-message {
    font-size: 0.85rem;
  }
}
</style>