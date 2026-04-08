<script setup lang="ts">
import { Inbox } from 'lucide-vue-next';
import AppStateBlock from '@/components/app/AppStateBlock.vue';

defineProps<{
  title?: string;
  description?: string;
}>();
</script>

<template>
  <AppStateBlock
    :title="title ?? '暂无内容'"
    :description="description ?? '当前条件下还没有可展示的数据。'"
  >
    <template #icon>
      <Inbox class="h-6 w-6" />
    </template>
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
  </AppStateBlock>
</template>
