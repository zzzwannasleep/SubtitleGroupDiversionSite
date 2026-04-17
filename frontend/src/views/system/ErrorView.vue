<template>
  <div class="app-surface p-10 text-center">
    <h1 class="text-2xl font-semibold text-slate-900">500</h1>
    <p class="mt-3 text-base text-slate-700">系统出现异常。</p>
    <p class="mt-2 text-sm text-slate-500">请稍后重试，必要时再进入后台继续排查。</p>
    <div class="mt-6 flex justify-center gap-2">
      <UiButton to="/releases" variant="primary">返回资源页</UiButton>
      <UiButton to="/admin" variant="secondary">前往后台</UiButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import UiButton from '@/components/ui/UiButton.vue';
</script>
