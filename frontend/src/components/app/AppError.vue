<script setup lang="ts">
import { TriangleAlert } from 'lucide-vue-next';
import AppStateBlock from '@/components/app/AppStateBlock.vue';

defineProps<{
  title?: string;
  description?: string;
}>();
</script>

<template>
  <AppStateBlock
    :title="title ?? '加载失败'"
    :description="description ?? '稍后重试，或检查服务端状态。'"
    tone="danger"
  >
    <template #icon>
      <TriangleAlert class="h-6 w-6" />
    </template>
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
  </AppStateBlock>
</template>
