<template>
  <div class="home">
    <VoiceInterface />
  </div>
</template>

<script>
// @ is an alias to /src
import VoiceInterface from '@/components/VoiceInterface.vue'

export default {
  name: 'HomeView',
  components: {
    VoiceInterface
  }
}
</script>

<style lang="scss" scoped>
.home {
  height: 100vh;
  overflow: hidden;
}
</style>
