<script setup lang="ts">
import { NMessageProvider, NDialogProvider, NConfigProvider } from 'naive-ui'
// 移除未使用的导入和变量
</script>

<template>
  <n-config-provider>
    <n-dialog-provider>
      <n-message-provider>
        <router-view></router-view>
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
