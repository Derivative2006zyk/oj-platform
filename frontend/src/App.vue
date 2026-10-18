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

html,
body {
  min-height: 100%;
  width: 100%;
  /* 允许双指放大后出现横向滚动条 */
  overflow-x: auto;
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  background-color: var(--color-bg-page);
  /* 防止放大时触摸变成选中文本（可选，防止误触） */
  -webkit-touch-callout: none;
}

#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow-x: auto;
  /* 确保内容区撑满 */
  min-width: 100vw; 
}

a {
  color: inherit;
  text-decoration: none;
}
</style>