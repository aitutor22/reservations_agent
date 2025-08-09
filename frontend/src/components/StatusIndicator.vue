<template>
  <div class="status-indicator" :class="statusClass">
    <span class="status-dot"></span>
    <span class="status-text">{{ statusText }}</span>
  </div>
</template>

<script>
export default {
  name: 'StatusIndicator',
  props: {
    status: {
      type: String,
      default: 'idle',
      validator: value => ['idle', 'connecting', 'connected', 'error'].includes(value)
    }
  },
  computed: {
    statusClass() {
      return `status-${this.status}`
    },
    statusText() {
      const statusMap = {
        idle: 'Offline',
        connecting: 'Connecting...',
        connected: 'Connected',
        error: 'Connection Error'
      }
      return statusMap[this.status] || 'Unknown'
    }
  }
}
</script>

<style lang="scss" scoped>
.status-indicator {
  display: flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
  }
  
  .status-text {
    white-space: nowrap;
  }
  
  &.status-idle {
    background: #f7fafc;
    color: #718096;
    
    .status-dot {
      background: #cbd5e0;
    }
  }
  
  &.status-connecting {
    background: #fef5e7;
    color: #f39c12;
    
    .status-dot {
      background: #f39c12;
      animation: blink 1s infinite;
      
      &::before {
        background: #f39c12;
      }
    }
  }
  
  &.status-connected {
    background: #edfff5;
    color: #10b981;
    
    .status-dot {
      background: #10b981;
      
      &::before {
        background: #10b981;
      }
    }
  }
  
  &.status-error {
    background: #fef2f2;
    color: #ef4444;
    
    .status-dot {
      background: #ef4444;
      animation: shake 0.5s;
      
      &::before {
        display: none;
      }
    }
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 0.3;
    transform: translate(-50%, -50%) scale(1.5);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(2);
  }
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-2px);
  }
  75% {
    transform: translateX(2px);
  }
}

@media (max-width: 640px) {
  .status-indicator {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    
    .status-dot {
      width: 6px;
      height: 6px;
      margin-right: 0.375rem;
    }
  }
}
</style>