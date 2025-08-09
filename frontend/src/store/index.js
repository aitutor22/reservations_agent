import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    messages: [],
    isTyping: false,
    connectionStatus: 'idle',
    sessionId: null,
    currentAgentState: 'greeting',
    pendingReservation: null,
    confirmedReservation: null
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
    }
  },
  actions: {
    initializeChat({ commit }) {
      commit('SET_CONNECTION_STATUS', 'connecting')
      
      setTimeout(() => {
        commit('SET_CONNECTION_STATUS', 'connected')
        commit('SET_SESSION_ID', 'demo-session-' + Date.now())
        
        setTimeout(() => {
          commit('ADD_MESSAGE', {
            content: 'Hello! Welcome to our restaurant. I can help you with information about our hours, location, or making a reservation. How can I assist you today?',
            role: 'agent'
          })
        }, 1000)
      }, 1500)
    },
    
    sendMessage({ commit, dispatch }, messageContent) {
      commit('ADD_MESSAGE', {
        content: messageContent,
        role: 'user'
      })
      
      commit('SET_TYPING', true)
      
      setTimeout(() => {
        dispatch('generateAgentResponse', messageContent)
      }, 1000)
    },
    
    generateAgentResponse({ commit, state }, userMessage) {
      const lowerMessage = userMessage.toLowerCase()
      let response = ''
      
      if (lowerMessage.includes('hour') || lowerMessage.includes('open') || lowerMessage.includes('close')) {
        response = 'We are open Monday through Thursday from 11:30 AM to 10:00 PM, Friday and Saturday from 11:30 AM to 11:00 PM, and Sunday from 12:00 PM to 9:00 PM.'
      } else if (lowerMessage.includes('location') || lowerMessage.includes('address') || lowerMessage.includes('where')) {
        response = 'We are located at 123 Main Street, Downtown District. We\'re just two blocks from the Central Station, with convenient parking available.'
      } else if (lowerMessage.includes('special') || lowerMessage.includes('menu') || lowerMessage.includes('food')) {
        response = 'Today\'s specials include our signature Grilled Salmon with lemon butter sauce and our Chef\'s Special Pasta. Would you like to make a reservation to try them?'
      } else if (lowerMessage.includes('reservation') || lowerMessage.includes('book') || lowerMessage.includes('table')) {
        response = 'I\'d be happy to help you make a reservation. What date and time would you prefer, and how many people will be in your party?'
        commit('SET_AGENT_STATE', 'reservation')
      } else if (state.currentAgentState === 'reservation') {
        response = 'Great! Let me check availability for that. Could you please provide your name and phone number to confirm the reservation?'
      } else {
        response = 'I can help you with information about our hours, location, daily specials, or making a reservation. What would you like to know?'
      }
      
      setTimeout(() => {
        commit('SET_TYPING', false)
        commit('ADD_MESSAGE', {
          content: response,
          role: 'agent'
        })
      }, 500 + Math.random() * 1000)
    },
    
    clearChat({ commit }) {
      commit('CLEAR_SESSION')
    },
    
    updateConnectionStatus({ commit }, status) {
      commit('SET_CONNECTION_STATUS', status)
    }
  },
  modules: {
  }
})
