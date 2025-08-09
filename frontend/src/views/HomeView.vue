<template>
  <div class="home">
    <ChatInterface />
  </div>
</template>

<script>
// @ is an alias to /src
import ChatInterface from '@/components/ChatInterface.vue'

export default {
  name: 'HomeView',
  components: {
    ChatInterface
  }
}
</script>

<style lang="scss" scoped>
.home {
  height: 100vh;
  overflow: hidden;
}
</style>
