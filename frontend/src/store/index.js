import Vue from 'vue'
import Vuex from 'vuex'
import websocketService from '@/services/websocket'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    messages: [],
    isTyping: false,
    connectionStatus: 'idle',
    sessionId: null,
    currentAgentState: 'greeting',
    pendingReservation: null,
    confirmedReservation: null,
    websocket: null
  },
  getters: {
    sortedMessages: state => {
      return state.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    },
    isConnected: state => state.connectionStatus === 'connected',
    hasActiveSession: state => state.sessionId !== null
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
    }
  },
  modules: {
  }
})
