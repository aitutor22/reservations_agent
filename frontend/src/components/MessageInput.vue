<template>
  <div class="message-input-container">
    <form @submit.prevent="sendMessage" class="message-form">
      <div class="input-wrapper">
        <input
          v-model="messageText"
          type="text"
          class="message-input"
          :placeholder="placeholder"
          :disabled="disabled"
          @keypress.enter.prevent="sendMessage"
          ref="messageInput"
        />
        <div class="input-actions">
          <button
            type="button"
            class="voice-button"
            :disabled="disabled"
            @click="toggleVoiceMode"
            :title="voiceMode ? 'Switch to text' : 'Switch to voice (coming soon)'"
          >
            <svg v-if="!voiceMode" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="10" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </button>
          <button
            type="submit"
            class="send-button"
            :disabled="!canSend"
            :class="{ 'active': canSend }"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </form>
    <div class="input-hint">
      {{ voiceMode ? 'Voice mode coming soon. Using text input for now.' : 'Type a message or click the mic for voice input (coming soon)' }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'MessageInput',
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      messageText: '',
      voiceMode: false
    }
  },
  computed: {
    canSend() {
      return this.messageText.trim().length > 0 && !this.disabled
    },
    placeholder() {
      if (this.disabled) {
        return 'Connecting...'
      }
      return this.voiceMode ? 'Voice mode (coming soon)' : 'Type your message...'
    }
  },
  methods: {
    sendMessage() {
      if (!this.canSend) return
      
      const message = this.messageText.trim()
      this.$emit('sendMessage', message)
      this.messageText = ''
      this.$refs.messageInput.focus()
    },
    toggleVoiceMode() {
      this.voiceMode = !this.voiceMode
      if (!this.voiceMode) {
        this.$refs.messageInput.focus()
      }
    }
  },
  mounted() {
    this.$refs.messageInput.focus()
  }
}
</script>

<style lang="scss" scoped>
.message-input-container {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 1rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

.message-form {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #f7fafc;
  border-radius: 2rem;
  padding: 0.5rem;
  transition: all 0.3s ease;
  
  &:focus-within {
    background: white;
    box-shadow: 0 0 0 2px #667eea;
  }
}

.message-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  color: #2d3748;
  
  &::placeholder {
    color: #a0aec0;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-right: 0.5rem;
}

.voice-button,
.send-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #718096;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover:not(:disabled) {
    background: #edf2f7;
    color: #4a5568;
  }
  
  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.send-button {
  &.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    
    &:hover {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
  }
}

.input-hint {
  font-size: 0.75rem;
  color: #718096;
  text-align: center;
  margin-top: 0.5rem;
  opacity: 0.8;
}

@media (max-width: 640px) {
  .message-input-container {
    padding: 0.75rem;
  }
  
  .input-wrapper {
    padding: 0.375rem;
  }
  
  .message-input {
    font-size: 0.95rem;
    padding: 0.375rem 0.75rem;
  }
  
  .voice-button,
  .send-button {
    width: 32px;
    height: 32px;
    
    svg {
      width: 18px;
      height: 18px;
    }
  }
  
  .input-hint {
    font-size: 0.7rem;
  }
}
</style>