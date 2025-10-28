<script setup lang="ts">
import ChatView from './views/ChatView.vue'
</script>

<template>
  <ChatView />
</template>

<style>
#app {
  height: 100vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding:0;
  background-image: url('./assets/background.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
</style>
