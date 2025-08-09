<template>
  <div class="message-list" ref="messageContainer">
    <div class="messages-wrapper">
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-icon">👋</div>
        <h2>Welcome to Restaurant Reservations</h2>
        <p>How can I help you today? You can ask about our hours, location, or make a reservation.</p>
      </div>
      
      <MessageBubble
        v-for="(message, index) in messages"
        :key="index"
        :message="message"
        :isLastMessage="index === messages.length - 1"
      />
      
      <div v-if="isTyping" class="typing-indicator">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MessageBubble from './MessageBubble.vue'

export default {
  name: 'MessageList',
  components: {
    MessageBubble
  },
  props: {
    messages: {
      type: Array,
      default: () => []
    },
    isTyping: {
      type: Boolean,
      default: false
    }
  },
  watch: {
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true
    },
    isTyping() {
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    }
  },
  methods: {
    scrollToBottom() {
      const container = this.$refs.messageContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }
  },
  mounted() {
    this.scrollToBottom()
  }
}
</script>

<style lang="scss" scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  scroll-behavior: smooth;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 3px;
    
    &:hover {
      background: #a0aec0;
    }
  }
}

.messages-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 1rem;
}

.welcome-message {
  text-align: center;
  padding: 3rem 1rem;
  color: #4a5568;
  
  .welcome-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    animation: wave 1s ease-in-out;
  }
  
  h2 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: #2d3748;
  }
  
  p {
    font-size: 1rem;
    opacity: 0.8;
    max-width: 400px;
    margin: 0 auto;
  }
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  margin: 0.5rem 0;
  
  .typing-dots {
    display: flex;
    align-items: center;
    background: #e2e8f0;
    border-radius: 1.5rem;
    padding: 0.5rem 1rem;
    
    span {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #718096;
      margin: 0 2px;
      animation: typing 1.4s infinite;
      
      &:nth-child(2) {
        animation-delay: 0.2s;
      }
      
      &:nth-child(3) {
        animation-delay: 0.4s;
      }
    }
  }
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-10deg); }
  75% { transform: rotate(10deg); }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .message-list {
    padding: 0.5rem;
  }
  
  .welcome-message {
    padding: 2rem 1rem;
    
    h2 {
      font-size: 1.25rem;
    }
    
    p {
      font-size: 0.9rem;
    }
  }
}
</style>