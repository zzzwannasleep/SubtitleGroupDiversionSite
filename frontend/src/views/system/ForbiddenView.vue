<template>
  <div class="app-surface p-10 text-center">
    <h1 class="text-2xl font-semibold text-slate-900">403</h1>
    <p class="mt-3 text-base text-slate-700">当前账号没有访问这里的权限。</p>
    <p class="mt-2 text-sm text-slate-500">请返回前台继续浏览资源，或使用有权限的账号登录。</p>
    <div class="mt-6 flex justify-center gap-2">
      <UiButton to="/releases" variant="primary">返回资源页</UiButton>
      <UiButton to="/login" variant="secondary">重新登录</UiButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import UiButton from '@/components/ui/UiButton.vue';
</script>
