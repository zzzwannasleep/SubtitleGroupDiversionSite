<script setup lang="ts">
import { ShieldX } from 'lucide-vue-next';
import AppStateBlock from '@/components/app/AppStateBlock.vue';
</script>

<template>
  <AppStateBlock title="没有访问权限" description="当前账号不具备该页面或该操作的权限。" tone="warning">
    <template #icon>
      <ShieldX class="h-6 w-6" />
    </template>
  </AppStateBlock>
</template>
