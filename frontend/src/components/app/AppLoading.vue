<script setup lang="ts">
import { LoaderCircle } from 'lucide-vue-next';
import AppStateBlock from '@/components/app/AppStateBlock.vue';
</script>

<template>
  <AppStateBlock title="正在加载" description="页面数据加载中，请稍候。" tone="info">
    <template #icon>
      <LoaderCircle class="h-6 w-6 animate-spin" />
    </template>
  </AppStateBlock>
</template>
