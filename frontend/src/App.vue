<template>
  <div id="app-root">
    <NavBar />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import NavBar from './components/NavBar.vue'
</script>

<style>
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  background-color: var(--color-bg-page);
}

a {
  color: inherit;
  text-decoration: none;
}
</style>