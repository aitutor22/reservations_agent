<template>
  <div class="chat-interface">
    <div class="chat-header">
      <img class="logo" src="/img/logo.png" alt="Restaurant Logo">
      <h1 class="restaurant-name">Restaurant Reservations</h1>
      <StatusIndicator :status="connectionStatus" />
    </div>
    
    <MessageList 
      :messages="messages"
      :isTyping="isTyping"
    />
    
    <MessageInput 
      @sendMessage="handleSendMessage"
      :disabled="connectionStatus !== 'connected'"
    />
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'
import StatusIndicator from './StatusIndicator.vue'

export default {
  name: 'ChatInterface',
  components: {
    MessageList,
    MessageInput,
    StatusIndicator
  },
  computed: {
    ...mapState({
      messages: state => state.messages,
      isTyping: state => state.isTyping,
      connectionStatus: state => state.connectionStatus
    })
  },
  methods: {
    ...mapActions(['sendMessage']),
    handleSendMessage(message) {
      this.sendMessage(message)
    }
  },
  mounted() {
    this.$store.dispatch('initializeChat')
  },
  beforeDestroy() {
    // Clean up WebSocket connection when component is destroyed
    this.$store.dispatch('disconnectWebSocket')
  }
}
</script>

<style lang="scss" scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(180deg, #e3f2fd 0%, #ffffff 100%);
  position: relative;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;

  .logo {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }

  .restaurant-name {
    flex: 1;
    margin: 0 1rem;
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
  }
}

@media (max-width: 640px) {
  .chat-header {
    padding: 0.75rem 1rem;
    
    .restaurant-name {
      font-size: 1rem;
    }
    
    .logo {
      width: 32px;
      height: 32px;
    }
  }
}
</style>