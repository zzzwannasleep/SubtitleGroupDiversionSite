<template>
  <div class="app-surface p-10 text-center">
    <h1 class="text-2xl font-semibold text-slate-900">500</h1>
    <p class="mt-3 text-base text-slate-700">系统出现异常。</p>
    <p class="mt-2 text-sm text-slate-500">MVP 阶段建议优先显示页内错误态，必要时再统一跳转到这里。</p>
    <div class="mt-6 flex justify-center gap-2">
      <UiButton to="/" variant="primary">返回首页</UiButton>
      <UiButton to="/admin/tracker-sync" variant="secondary">查看同步状态</UiButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import UiButton from '@/components/ui/UiButton.vue';
</script>

