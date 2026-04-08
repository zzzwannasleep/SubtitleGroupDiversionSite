<script setup lang="ts">
import { SearchX } from 'lucide-vue-next';
import AppStateBlock from '@/components/app/AppStateBlock.vue';
</script>

<template>
  <AppStateBlock title="页面或资源不存在" description="可能已被删除、隐藏，或链接地址有误。">
    <template #icon>
      <SearchX class="h-6 w-6" />
    </template>
  </AppStateBlock>
</template>
