<template>
  <div class="app-surface p-10 text-center">
    <h1 class="text-2xl font-semibold text-slate-900">404</h1>
    <p class="mt-3 text-base text-slate-700">页面或资源不存在。</p>
    <p class="mt-2 text-sm text-slate-500">链接可能有误，或者对应内容已被隐藏。</p>
    <div class="mt-6 flex justify-center gap-2">
      <UiButton to="/releases" variant="primary">返回资源页</UiButton>
      <UiButton to="/me" variant="secondary">我的账户</UiButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import UiButton from '@/components/ui/UiButton.vue';
</script>
