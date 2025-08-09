/**
 * WebRTC Service for OpenAI Realtime API
 * Handles voice communication via WebRTC with ephemeral token authentication
 */

class WebRTCService {
  constructor() {
    this.pc = null
    this.localStream = null
    this.dataChannel = null
    this.ephemeralToken = null
    this.sessionId = null
    this.isConnecting = false
    this.isConnected = false
    this.listeners = new Map()
    
    // Audio elements
    this.remoteAudio = null
    
    // Configuration
    this.config = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
      ]
    }
  }

  /**
   * Initialize WebRTC connection with ephemeral token
   * @param {string} token - Ephemeral token from backend
   * @param {string} sessionId - Session identifier
   */
  async connect(token, sessionId) {
    if (this.isConnecting || this.isConnected) {
      console.log('WebRTC already connecting or connected')
      return
    }

    this.ephemeralToken = token
    this.sessionId = sessionId
    this.isConnecting = true

    try {
      // Step 1: Create RTCPeerConnection
      this.pc = new RTCPeerConnection(this.config)
      this.setupPeerConnectionHandlers()

      // Step 2: Get user media (microphone)
      await this.setupLocalAudio()

      // Step 3: Create data channel for Realtime API events
      this.setupDataChannel()

      // Step 4: Create offer
      const offer = await this.pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      })
      
      await this.pc.setLocalDescription(offer)

      // Step 5: Exchange SDP with OpenAI
      const answer = await this.exchangeSDP(offer)
      await this.pc.setRemoteDescription(answer)

      this.isConnecting = false
      this.isConnected = true
      this.emit('connected', { sessionId })

    } catch (error) {
      console.error('Failed to connect WebRTC:', error)
      this.isConnecting = false
      this.isConnected = false
      this.emit('error', { error })
      throw error
    }
  }

  /**
   * Setup local audio stream from microphone
   */
  async setupLocalAudio() {
    try {
      // Request microphone access
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 24000,
          channelCount: 1
        },
        video: false
      })

      // Add audio track to peer connection
      const audioTrack = this.localStream.getAudioTracks()[0]
      if (audioTrack) {
        this.pc.addTrack(audioTrack, this.localStream)
        console.log('Local audio track added to peer connection')
        this.emit('microphoneReady', { track: audioTrack })
      }

    } catch (error) {
      console.error('Failed to access microphone:', error)
      this.emit('microphoneError', { error })
      throw new Error('Microphone access denied or unavailable')
    }
  }

  /**
   * Setup data channel for Realtime API events
   */
  setupDataChannel() {
    // Create data channel for bidirectional communication
    this.dataChannel = this.pc.createDataChannel('oai-events', {
      ordered: true
    })

    this.dataChannel.onopen = () => {
      console.log('Data channel opened')
      this.emit('dataChannelOpen')
      
      // Send initial session configuration
      this.sendEvent({
        type: 'session.update',
        session: {
          instructions: 'You are a helpful assistant for Sakura Ramen House restaurant.',
          voice: 'verse',
          input_audio_format: 'pcm16',
          output_audio_format: 'pcm16'
        }
      })
    }

    this.dataChannel.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleRealtimeEvent(data)
      } catch (error) {
        console.error('Failed to parse data channel message:', error)
      }
    }

    this.dataChannel.onerror = (error) => {
      console.error('Data channel error:', error)
      this.emit('dataChannelError', { error })
    }

    this.dataChannel.onclose = () => {
      console.log('Data channel closed')
      this.emit('dataChannelClosed')
    }
  }

  /**
   * Setup peer connection event handlers
   */
  setupPeerConnectionHandlers() {
    // Handle incoming audio track from OpenAI
    this.pc.ontrack = (event) => {
      console.log('Received remote track:', event.track.kind)
      
      if (event.track.kind === 'audio') {
        // Create or get audio element for playback
        if (!this.remoteAudio) {
          this.remoteAudio = new Audio()
          this.remoteAudio.autoplay = true
        }
        
        // Attach remote stream to audio element
        if (event.streams && event.streams[0]) {
          this.remoteAudio.srcObject = event.streams[0]
          console.log('Remote audio connected')
          this.emit('remoteAudioConnected', { stream: event.streams[0] })
        }
      }
    }

    // Monitor connection state
    this.pc.onconnectionstatechange = () => {
      console.log('Connection state:', this.pc.connectionState)
      this.emit('connectionStateChange', { state: this.pc.connectionState })
      
      if (this.pc.connectionState === 'failed' || this.pc.connectionState === 'disconnected') {
        this.handleDisconnection()
      }
    }

    // Monitor ICE connection state
    this.pc.oniceconnectionstatechange = () => {
      console.log('ICE connection state:', this.pc.iceConnectionState)
      this.emit('iceStateChange', { state: this.pc.iceConnectionState })
    }

    // Handle ICE candidates (though OpenAI may not use trickle ICE)
    this.pc.onicecandidate = (event) => {
      if (event.candidate) {
        console.log('ICE candidate:', event.candidate)
      }
    }
  }

  /**
   * Exchange SDP offer/answer with OpenAI
   * @param {RTCSessionDescriptionInit} offer - Local SDP offer
   */
  async exchangeSDP(offer) {
    try {
      const response = await fetch('https://api.openai.com/v1/realtime', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.ephemeralToken}`,
          'Content-Type': 'application/sdp'
        },
        body: offer.sdp
      })

      if (!response.ok) {
        throw new Error(`SDP exchange failed: ${response.status}`)
      }

      const answerSdp = await response.text()
      
      return new RTCSessionDescription({
        type: 'answer',
        sdp: answerSdp
      })

    } catch (error) {
      console.error('SDP exchange error:', error)
      throw error
    }
  }

  /**
   * Handle incoming Realtime API events
   * @param {Object} event - Realtime API event
   */
  handleRealtimeEvent(event) {
    const { type } = event
    console.log('Realtime event:', type, event)

    switch (type) {
      case 'session.created':
        console.log('Session created:', event.session)
        this.emit('sessionCreated', event.session)
        break

      case 'session.updated':
        console.log('Session updated:', event.session)
        this.emit('sessionUpdated', event.session)
        break

      case 'conversation.item.created':
        // Handle conversation updates (text and transcriptions)
        if (event.item && event.item.content && event.item.content[0]) {
          const content = event.item.content[0]
          let text = ''
          
          // Extract text from different content types
          if (content.transcript) {
            // Audio transcription
            text = content.transcript
          } else if (content.text) {
            // Direct text response
            text = content.text
          } else if (typeof content === 'string') {
            // Plain string
            text = content
          }
          
          if (text) {
            if (event.item.role === 'user') {
              this.emit('userTranscript', {
                text: text,
                timestamp: event.item.created_at
              })
            } else if (event.item.role === 'assistant') {
              this.emit('assistantTranscript', {
                text: text,
                timestamp: event.item.created_at
              })
            }
          }
        }
        break

      case 'response.audio.delta':
        // Audio is being streamed (handled by ontrack)
        this.emit('audioStreaming')
        break

      case 'response.audio.done':
        // Audio response complete
        this.emit('audioComplete')
        break

      case 'error':
        console.error('Realtime API error:', event.error)
        this.emit('realtimeError', event.error)
        break

      default:
        // Emit generic event for other types
        this.emit('realtimeEvent', event)
    }
  }

  /**
   * Send event to OpenAI via data channel
   * @param {Object} event - Event to send
   */
  sendEvent(event) {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      const eventStr = JSON.stringify(event)
      this.dataChannel.send(eventStr)
      console.log('Sent event:', event.type)
      return true
    } else {
      console.warn('Data channel not ready, cannot send event')
      return false
    }
  }

  /**
   * Send text input (for hybrid mode)
   * @param {string} text - Text to send
   */
  sendText(text) {
    // Send the user's text message
    const sent = this.sendEvent({
      type: 'conversation.item.create',
      item: {
        type: 'message',
        role: 'user',
        content: [
          {
            type: 'input_text',
            text: text
          }
        ]
      }
    })
    
    if (sent) {
      // Trigger a response generation
      this.sendEvent({
        type: 'response.create'
      })
    }
    
    return sent
  }

  /**
   * Start recording audio
   */
  startRecording() {
    if (!this.isConnected) {
      console.warn('WebRTC not connected')
      return false
    }

    // Audio is continuously streaming when connected
    // This method is for UI state management
    this.emit('recordingStarted')
    return true
  }

  /**
   * Stop recording audio
   */
  stopRecording() {
    // Audio streaming continues, but we can signal end of input
    this.sendEvent({
      type: 'input_audio_buffer.commit'
    })
    
    this.emit('recordingStopped')
    return true
  }

  /**
   * Disconnect WebRTC connection
   */
  disconnect() {
    // Stop local audio
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => {
        track.stop()
      })
      this.localStream = null
    }

    // Close data channel
    if (this.dataChannel) {
      this.dataChannel.close()
      this.dataChannel = null
    }

    // Close peer connection
    if (this.pc) {
      this.pc.close()
      this.pc = null
    }

    // Stop remote audio
    if (this.remoteAudio) {
      this.remoteAudio.pause()
      this.remoteAudio.srcObject = null
      this.remoteAudio = null
    }

    this.isConnected = false
    this.isConnecting = false
    this.ephemeralToken = null
    this.sessionId = null

    this.emit('disconnected')
  }

  /**
   * Handle unexpected disconnection
   */
  handleDisconnection() {
    console.log('Handling unexpected disconnection')
    this.isConnected = false
    this.emit('unexpectedDisconnection')
    
    // Clean up resources
    this.disconnect()
  }

  /**
   * Get connection status
   */
  get connectionStatus() {
    if (this.isConnected) return 'connected'
    if (this.isConnecting) return 'connecting'
    return 'disconnected'
  }

  /**
   * Check if microphone is active
   */
  get isMicrophoneActive() {
    if (!this.localStream) return false
    const audioTrack = this.localStream.getAudioTracks()[0]
    return audioTrack && audioTrack.enabled && !audioTrack.muted
  }

  /**
   * Mute/unmute microphone
   * @param {boolean} muted - Whether to mute
   */
  setMicrophoneMuted(muted) {
    if (this.localStream) {
      const audioTrack = this.localStream.getAudioTracks()[0]
      if (audioTrack) {
        audioTrack.enabled = !muted
        this.emit('microphoneMuted', { muted })
        return true
      }
    }
    return false
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Event callback
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index !== -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  /**
   * Emit an event
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error)
        }
      })
    }
  }
}

// Create singleton instance
const webrtcService = new WebRTCService()

export default webrtcService