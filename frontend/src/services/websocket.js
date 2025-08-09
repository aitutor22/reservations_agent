/**
 * WebSocket Service for real-time communication with backend
 */

class WebSocketService {
  constructor() {
    this.ws = null
    this.sessionId = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.messageQueue = []
    this.isConnecting = false
    this.heartbeatInterval = null
    this.listeners = new Map()
  }

  /**
   * Connect to WebSocket server
   * @param {string} sessionId - Session identifier
   * @param {Object} options - Connection options
   */
  connect(sessionId, options = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return Promise.resolve()
    }

    if (this.isConnecting) {
      console.log('WebSocket connection already in progress')
      return Promise.resolve()
    }

    this.sessionId = sessionId
    this.isConnecting = true

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `ws://localhost:8000/ws/${sessionId}`
        console.log(`Connecting to WebSocket: ${wsUrl}`)
        
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connected successfully')
          this.isConnecting = false
          this.reconnectAttempts = 0
          
          // Send session start message
          this.send({
            type: 'session:start',
            session_id: sessionId,
            timestamp: new Date().toISOString()
          })

          // Start heartbeat
          this.startHeartbeat()

          // Process queued messages
          this.processMessageQueue()

          // Emit connected event
          this.emit('connected', { sessionId })
          
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('WebSocket message received:', data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error, event.data)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnecting = false
          this.emit('error', { error })
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason)
          this.isConnecting = false
          this.stopHeartbeat()
          
          this.emit('disconnected', { 
            code: event.code, 
            reason: event.reason 
          })

          // Attempt reconnection if not a normal closure
          if (event.code !== 1000 && event.code !== 1001) {
            this.attemptReconnect()
          }
        }
      } catch (error) {
        console.error('Error creating WebSocket:', error)
        this.isConnecting = false
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.ws) {
      // Send session end message
      this.send({
        type: 'session:end',
        session_id: this.sessionId,
        timestamp: new Date().toISOString()
      })

      this.stopHeartbeat()
      this.reconnectAttempts = this.maxReconnectAttempts // Prevent reconnection
      this.ws.close(1000, 'User disconnected')
      this.ws = null
      this.sessionId = null
    }
  }

  /**
   * Send a message through WebSocket
   * @param {Object} message - Message to send
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const messageStr = JSON.stringify(message)
      console.log('Sending WebSocket message:', message)
      this.ws.send(messageStr)
      return true
    } else {
      console.log('WebSocket not connected, queuing message:', message)
      this.messageQueue.push(message)
      return false
    }
  }

  /**
   * Send a text message
   * @param {string} text - Text content to send
   */
  sendTextMessage(text) {
    return this.send({
      type: 'text:message',
      text: text,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Handle incoming WebSocket messages
   * @param {Object} data - Parsed message data
   */
  handleMessage(data) {
    const { type } = data

    switch (type) {
      case 'connection:established':
        console.log('Connection established:', data)
        break

      case 'text:response':
        this.emit('textResponse', {
          text: data.text || data.original,
          original: data.original,
          echo: data.echo
        })
        break

      case 'session:started':
        console.log('Session started:', data)
        this.emit('sessionStarted', data)
        break

      case 'session:ended':
        console.log('Session ended:', data)
        this.emit('sessionEnded', data)
        break

      case 'pong':
        console.log('Heartbeat pong received')
        break

      case 'error':
        console.error('Server error:', data)
        this.emit('serverError', data)
        break

      default:
        console.log('Unknown message type:', type, data)
        this.emit('message', data)
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({
          type: 'ping',
          timestamp: new Date().toISOString()
        })
      }
    }, 30000) // 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * Process queued messages
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      this.send(message)
    }
  }

  /**
   * Attempt to reconnect to WebSocket server
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      this.emit('reconnectFailed', {
        attempts: this.reconnectAttempts
      })
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)
    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      delay
    })

    setTimeout(() => {
      if (this.sessionId) {
        this.connect(this.sessionId).catch(error => {
          console.error('Reconnection failed:', error)
        })
      }
    }, delay)
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

  /**
   * Get connection status
   */
  get isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * Get connection state
   */
  get readyState() {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }
}

// Create singleton instance
const websocketService = new WebSocketService()

export default websocketService