import Vue from 'vue'
import Vuex from 'vuex'
import websocketService from '@/services/websocket'
import webrtcService from '@/services/webrtc'

Vue.use(Vuex)

// Audio context for playing PCM16 audio
let audioContext = null
let audioQueue = []
let isPlaying = false

// Function to play PCM16 audio data
async function playPCM16Audio(blob) {
  try {
    // Initialize audio context on first use
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 24000 // Match OpenAI's PCM16 format
      })
    }

    // Convert blob to ArrayBuffer
    const arrayBuffer = await blob.arrayBuffer()
    const int16Array = new Int16Array(arrayBuffer)
    
    // Convert Int16 to Float32 for Web Audio API
    const float32Array = new Float32Array(int16Array.length)
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0 // Convert to -1.0 to 1.0 range
    }
    
    // Create audio buffer
    const audioBuffer = audioContext.createBuffer(1, float32Array.length, 24000)
    audioBuffer.getChannelData(0).set(float32Array)
    
    // Queue the audio for playback
    audioQueue.push(audioBuffer)
    
    // Play if not already playing
    if (!isPlaying) {
      playNextInQueue()
    }
  } catch (error) {
    console.error('Error playing audio:', error)
  }
}

// Play the next audio buffer in the queue
function playNextInQueue() {
  if (audioQueue.length === 0) {
    isPlaying = false
    return
  }
  
  isPlaying = true
  const audioBuffer = audioQueue.shift()
  
  const source = audioContext.createBufferSource()
  source.buffer = audioBuffer
  source.connect(audioContext.destination)
  
  source.onended = () => {
    playNextInQueue() // Play next chunk when this one ends
  }
  
  source.start(0)
}

export default new Vuex.Store({
  state: {
    messages: [],
    isTyping: false,
    connectionStatus: 'idle',
    sessionId: null,
    currentAgentState: 'greeting',
    pendingReservation: null,
    confirmedReservation: null,
    websocket: null,
    // WebRTC state
    webrtc: null,
    webrtcStatus: 'idle', // idle, connecting, connected, error
    isVoiceMode: false,
    isRecording: false,
    ephemeralToken: null,
    microphonePermission: null // null, granted, denied
  },
  getters: {
    sortedMessages: state => {
      return state.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    },
    isConnected: state => state.connectionStatus === 'connected',
    hasActiveSession: state => state.sessionId !== null,
    isWebRTCReady: state => state.webrtcStatus === 'connected',
    isInVoiceMode: state => state.isVoiceMode
  },
  mutations: {
    ADD_MESSAGE(state, message) {
      state.messages.push({
        id: Date.now() + Math.random(),
        content: message.content,
        role: message.role,
        timestamp: message.timestamp || new Date().toISOString(),
        isFinal: message.isFinal !== false
      })
    },
    SET_TYPING(state, isTyping) {
      state.isTyping = isTyping
    },
    SET_CONNECTION_STATUS(state, status) {
      state.connectionStatus = status
    },
    SET_SESSION_ID(state, sessionId) {
      state.sessionId = sessionId
    },
    SET_AGENT_STATE(state, agentState) {
      state.currentAgentState = agentState
    },
    SET_PENDING_RESERVATION(state, reservation) {
      state.pendingReservation = reservation
    },
    SET_CONFIRMED_RESERVATION(state, reservation) {
      state.confirmedReservation = reservation
    },
    SET_WEBSOCKET(state, websocket) {
      state.websocket = websocket
    },
    // WebRTC mutations
    SET_WEBRTC(state, webrtc) {
      state.webrtc = webrtc
    },
    SET_WEBRTC_STATUS(state, status) {
      state.webrtcStatus = status
    },
    SET_VOICE_MODE(state, enabled) {
      state.isVoiceMode = enabled
    },
    SET_RECORDING(state, recording) {
      state.isRecording = recording
    },
    SET_EPHEMERAL_TOKEN(state, token) {
      state.ephemeralToken = token
    },
    SET_MICROPHONE_PERMISSION(state, permission) {
      state.microphonePermission = permission
    },
    CLEAR_MESSAGES(state) {
      state.messages = []
    },
    CLEAR_SESSION(state) {
      state.messages = []
      state.isTyping = false
      state.connectionStatus = 'idle'
      state.sessionId = null
      state.currentAgentState = 'greeting'
      state.pendingReservation = null
      state.confirmedReservation = null
      state.websocket = null
      // Clear WebRTC state
      state.webrtc = null
      state.webrtcStatus = 'idle'
      state.isVoiceMode = false
      state.isRecording = false
      state.ephemeralToken = null
      state.microphonePermission = null
    }
  },
  actions: {
    async initializeChat({ commit, dispatch }) {
      commit('SET_CONNECTION_STATUS', 'connecting')
      
      try {
        // Create a new session first
        const response = await fetch('http://localhost:8000/api/session/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          throw new Error('Failed to create session')
        }
        
        const data = await response.json()
        const sessionId = data.session_id
        
        commit('SET_SESSION_ID', sessionId)
        commit('SET_WEBSOCKET', websocketService)
        
        // Set up WebSocket event listeners
        websocketService.on('connected', () => {
          commit('SET_CONNECTION_STATUS', 'connected')
        })
        
        websocketService.on('disconnected', () => {
          commit('SET_CONNECTION_STATUS', 'idle')
        })
        
        websocketService.on('reconnecting', ({ attempt, maxAttempts }) => {
          commit('SET_CONNECTION_STATUS', 'connecting')
          console.log(`Reconnecting... (${attempt}/${maxAttempts})`)
        })
        
        websocketService.on('textResponse', ({ text }) => {
          commit('SET_TYPING', false)
          commit('ADD_MESSAGE', {
            content: text,
            role: 'agent'
          })
        })
        
        websocketService.on('error', (error) => {
          console.error('WebSocket error:', error)
          commit('SET_CONNECTION_STATUS', 'error')
        })
        
        // Connect to WebSocket
        await websocketService.connect(sessionId)
        
        // Send initial greeting after connection
        setTimeout(() => {
          commit('ADD_MESSAGE', {
            content: 'Hello! Welcome to Ichiban Ramen House. I can help you with information about our hours, location, or making a reservation. How can I assist you today?',
            role: 'agent'
          })
        }, 500)
        
      } catch (error) {
        console.error('Failed to initialize chat:', error)
        commit('SET_CONNECTION_STATUS', 'error')
        
        // Fallback message
        commit('ADD_MESSAGE', {
          content: 'Sorry, I\'m having trouble connecting to the server. Please try again later.',
          role: 'agent'
        })
      }
    },
    
    sendMessage({ commit, state }, messageContent) {
      // Add user message to chat
      commit('ADD_MESSAGE', {
        content: messageContent,
        role: 'user'
      })
      
      // Send message via WebSocket
      if (websocketService.isConnected) {
        commit('SET_TYPING', true)
        websocketService.sendTextMessage(messageContent)
      } else {
        // If not connected, show error message
        commit('ADD_MESSAGE', {
          content: 'Sorry, I\'m not connected to the server. Please wait while I reconnect...',
          role: 'agent'
        })
        
        // Try to reconnect
        if (state.sessionId) {
          websocketService.connect(state.sessionId).catch(error => {
            console.error('Failed to reconnect:', error)
          })
        }
      }
    },
    
    async disconnectWebSocket({ commit, state }) {
      if (websocketService.isConnected) {
        websocketService.disconnect()
      }
      
      // End session on backend
      if (state.sessionId) {
        try {
          await fetch(`http://localhost:8000/api/session/${state.sessionId}`, {
            method: 'DELETE'
          })
        } catch (error) {
          console.error('Failed to end session:', error)
        }
      }
      
      commit('CLEAR_SESSION')
    },
    
    clearChat({ dispatch }) {
      dispatch('disconnectWebSocket')
    },
    
    updateConnectionStatus({ commit }, status) {
      commit('SET_CONNECTION_STATUS', status)
    },
    
    // WebRTC Actions
    async initializeWebRTC({ commit, state }) {
      commit('SET_WEBRTC_STATUS', 'connecting')
      commit('SET_VOICE_MODE', true)
      
      try {
        // Get ephemeral token from backend
        const response = await fetch('http://localhost:8000/api/realtime/session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          throw new Error('Failed to get ephemeral token')
        }
        
        const data = await response.json()
        const ephemeralKey = data.ephemeral_key
        
        if (!ephemeralKey) {
          throw new Error('No ephemeral key received')
        }
        
        commit('SET_EPHEMERAL_TOKEN', ephemeralKey)
        commit('SET_WEBRTC', webrtcService)
        
        // Set up WebRTC event listeners
        webrtcService.on('connected', () => {
          commit('SET_WEBRTC_STATUS', 'connected')
          commit('SET_MICROPHONE_PERMISSION', 'granted')
          console.log('WebRTC connected')
        })
        
        webrtcService.on('disconnected', () => {
          commit('SET_WEBRTC_STATUS', 'idle')
          commit('SET_VOICE_MODE', false)
          commit('SET_RECORDING', false)
        })
        
        webrtcService.on('error', (error) => {
          console.error('WebRTC error:', error)
          commit('SET_WEBRTC_STATUS', 'error')
        })
        
        webrtcService.on('microphoneError', (error) => {
          console.error('Microphone error:', error)
          commit('SET_MICROPHONE_PERMISSION', 'denied')
          commit('SET_WEBRTC_STATUS', 'error')
        })
        
        webrtcService.on('userTranscript', ({ text }) => {
          // Add user transcription to messages
          commit('ADD_MESSAGE', {
            content: text,
            role: 'user'
          })
        })
        
        webrtcService.on('assistantTranscript', ({ text }) => {
          // Add assistant transcription to messages
          commit('ADD_MESSAGE', {
            content: text,
            role: 'agent'
          })
        })
        
        // Connect WebRTC with ephemeral token
        await webrtcService.connect(ephemeralKey, data.session_id)
        
      } catch (error) {
        console.error('Failed to initialize WebRTC:', error)
        commit('SET_WEBRTC_STATUS', 'error')
        commit('SET_VOICE_MODE', false)
        
        // Show error message
        commit('ADD_MESSAGE', {
          content: `Failed to initialize voice mode: ${error.message}`,
          role: 'system'
        })
        
        throw error
      }
    },
    
    async disconnectWebRTC({ commit, state }) {
      if (webrtcService.isConnected) {
        webrtcService.disconnect()
      }
      
      commit('SET_WEBRTC_STATUS', 'idle')
      commit('SET_VOICE_MODE', false)
      commit('SET_RECORDING', false)
      commit('SET_EPHEMERAL_TOKEN', null)
    },
    
    startRecording({ commit }) {
      if (webrtcService.isConnected) {
        webrtcService.startRecording()
        commit('SET_RECORDING', true)
      }
    },
    
    stopRecording({ commit }) {
      if (webrtcService.isConnected) {
        webrtcService.stopRecording()
        commit('SET_RECORDING', false)
      }
    },
    
    sendTextViaWebRTC({ commit }, text) {
      // Add user message to chat UI immediately
      commit('ADD_MESSAGE', {
        content: text,
        role: 'user'
      })
      
      // Send text through WebRTC data channel to Realtime API
      if (webrtcService.isConnected) {
        console.log('Sending text through WebRTC data channel:', text)
        const sent = webrtcService.sendText(text)
        
        if (!sent) {
          console.error('Failed to send text via WebRTC')
          commit('ADD_MESSAGE', {
            content: 'Failed to send message. Please try again.',
            role: 'system'
          })
        }
      } else {
        console.warn('WebRTC not connected, cannot send text')
        commit('ADD_MESSAGE', {
          content: 'Voice connection not ready. Please wait...',
          role: 'system'
        })
      }
    },
    
    // Restaurant RealtimeAgent via WebSocket (Backend-routed)
    async connectRealtimeAgent({ commit }) {
      commit('SET_CONNECTION_STATUS', 'connecting')
      commit('ADD_MESSAGE', {
        content: 'Connecting to Sakura Ramen House voice assistant...',
        role: 'system'
      })
      
      try {
        // Connect to the restaurant agent WebSocket endpoint
        const ws = new WebSocket('ws://localhost:8000/ws/realtime/agent')
        
        ws.onopen = () => {
          console.log('Connected to Restaurant RealtimeAgent')
          commit('SET_CONNECTION_STATUS', 'connected')
          commit('ADD_MESSAGE', {
            content: 'Welcome to Sakura Ramen House! How can I help you today?',
            role: 'agent'
          })
          
          // Store WebSocket for sending messages
          commit('SET_WEBSOCKET', ws)
        }
        
        ws.onmessage = (event) => {
          try {
            // Try to parse as JSON first
            const data = JSON.parse(event.data)
            console.log('RealtimeAgent event:', data)
            
            if (data.type === 'assistant_transcript') {
              commit('ADD_MESSAGE', {
                content: data.transcript,
                role: 'agent'
              })
            } else if (data.type === 'user_transcript') {
              // Update the last user message with transcription
              console.log('User transcript:', data.transcript)
            } else if (data.type === 'error') {
              commit('ADD_MESSAGE', {
                content: `Error: ${data.error}`,
                role: 'system'
              })
            } else if (data.type === 'session_started') {
              console.log('Session started:', data.session_id)
            }
          } catch (e) {
            // If not JSON, might be binary audio data
            if (event.data instanceof Blob) {
              console.log('Received audio data:', event.data.size, 'bytes')
              // Play audio response using Web Audio API
              playPCM16Audio(event.data)
            }
          }
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          commit('SET_CONNECTION_STATUS', 'error')
          commit('ADD_MESSAGE', {
            content: 'Connection error. Please check console.',
            role: 'system'
          })
        }
        
        ws.onclose = () => {
          console.log('WebSocket closed')
          commit('SET_CONNECTION_STATUS', 'idle')
          commit('ADD_MESSAGE', {
            content: 'Disconnected from RealtimeAgent.',
            role: 'system'
          })
        }
        
      } catch (error) {
        console.error('Failed to connect to RealtimeAgent:', error)
        commit('SET_CONNECTION_STATUS', 'error')
        commit('ADD_MESSAGE', {
          content: `Failed to connect: ${error.message}`,
          role: 'system'
        })
      }
    },
    
    // Send message to Restaurant RealtimeAgent
    sendToRealtimeAgent({ state, commit }, message) {
      if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        // Add user message to UI
        commit('ADD_MESSAGE', {
          content: message,
          role: 'user'
        })
        
        // Send as text message to RealtimeAgent
        state.websocket.send(JSON.stringify({
          type: 'text_message',
          text: message
        }))
      } else {
        commit('ADD_MESSAGE', {
          content: 'Not connected to the restaurant assistant. Please use connectRealtimeAgent() first.',
          role: 'system'
        })
      }
    },
    
    // Send audio chunk to Restaurant RealtimeAgent
    async sendAudioChunk({ state }, base64Audio) {
      if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        try {
          // Send base64-encoded PCM16 audio
          state.websocket.send(JSON.stringify({
            type: 'audio_chunk',
            audio: base64Audio
          }))
          console.log('Sent audio chunk (base64 PCM16)')
        } catch (error) {
          console.error('Failed to send audio chunk:', error)
        }
      }
    },
    
    // Signal end of audio input
    sendEndOfAudio({ state }) {
      if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
        state.websocket.send(JSON.stringify({
          type: 'end_audio'
        }))
        console.log('Sent end of audio signal')
      }
    }
  },
  modules: {
  }
})
