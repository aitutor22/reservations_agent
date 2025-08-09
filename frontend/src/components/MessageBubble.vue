<template>
  <div class="message-bubble" :class="messageClass">
    <div class="message-content">
      <p class="message-text">{{ message.content }}</p>
      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MessageBubble',
  props: {
    message: {
      type: Object,
      required: true
    },
    isLastMessage: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    messageClass() {
      return {
        'user-message': this.message.role === 'user',
        'agent-message': this.message.role === 'agent',
        'last-message': this.isLastMessage
      }
    }
  },
  methods: {
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.message-bubble {
  display: flex;
  margin: 0.75rem 0;
  animation: slideIn 0.3s ease-out;
  
  &.user-message {
    justify-content: flex-end;
    
    .message-content {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 1.25rem 1.25rem 0.25rem 1.25rem;
      margin-left: 20%;
      
      .message-time {
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }
  
  &.agent-message {
    justify-content: flex-start;
    
    .message-content {
      background: white;
      color: #2d3748;
      border-radius: 1.25rem 1.25rem 1.25rem 0.25rem;
      margin-right: 20%;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
      
      .message-time {
        color: #718096;
      }
    }
  }
  
  &.last-message {
    .message-content::after {
      content: '';
      position: absolute;
      bottom: -2px;
      width: 0;
      height: 0;
    }
    
    &.user-message .message-content::after {
      right: 0;
      border-style: solid;
      border-width: 0 0 10px 10px;
      border-color: transparent transparent transparent #764ba2;
    }
    
    &.agent-message .message-content::after {
      left: 0;
      border-style: solid;
      border-width: 0 10px 10px 0;
      border-color: transparent white transparent transparent;
    }
  }
}

.message-content {
  position: relative;
  padding: 0.75rem 1rem;
  max-width: 70%;
  word-wrap: break-word;
  
  .message-text {
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.4;
    white-space: pre-wrap;
  }
  
  .message-time {
    display: block;
    font-size: 0.7rem;
    margin-top: 0.25rem;
    opacity: 0.8;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .message-bubble {
    margin: 0.5rem 0;
    
    &.user-message .message-content {
      margin-left: 15%;
    }
    
    &.agent-message .message-content {
      margin-right: 15%;
    }
  }
  
  .message-content {
    max-width: 80%;
    padding: 0.6rem 0.9rem;
    
    .message-text {
      font-size: 0.9rem;
    }
    
    .message-time {
      font-size: 0.65rem;
    }
  }
}
</style>