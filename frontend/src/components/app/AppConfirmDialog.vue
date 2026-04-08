<script setup lang="ts">
import { computed } from 'vue';
import { CircleAlert, RotateCcw, ShieldAlert, TriangleAlert } from 'lucide-vue-next';
import UiButton from '@/components/ui/UiButton.vue';
import UiDialog from '@/components/ui/UiDialog.vue';

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    description: string;
    confirmLabel?: string;
    cancelLabel?: string;
    tone?: 'primary' | 'danger' | 'warning';
    pending?: boolean;
  }>(),
  {
    confirmLabel: '确认',
    cancelLabel: '取消',
    tone: 'primary',
    pending: false,
  },
);

const emit = defineEmits<{
  close: [];
  confirm: [];
}>();

const iconClasses = computed(() => {
  const map = {
    primary: 'bg-blue-50 text-blue-600',
    warning: 'bg-amber-50 text-amber-600',
    danger: 'bg-red-50 text-red-600',
  } as const;

  return map[props.tone];
});

const confirmVariant = computed(() => (props.tone === 'danger' ? 'danger' : 'primary'));
const iconComponent = computed(() => {
  const map = {
    primary: RotateCcw,
    warning: CircleAlert,
    danger: ShieldAlert,
  } as const;

  return map[props.tone] ?? TriangleAlert;
});

function handleClose() {
  if (props.pending) return;
  emit('close');
}

function handleConfirm() {
  if (props.pending) return;
  emit('confirm');
}
</script>

<template>
  <UiDialog :open="open" :title="title" :description="description" @close="handleClose">
    <div class="flex items-start gap-4">
      <div :class="['flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl', iconClasses]">
        <component :is="iconComponent" class="h-5 w-5" />
      </div>
      <div class="space-y-2 text-sm leading-6 text-slate-600">
        <slot>
          <p>请确认这次操作会按当前页面权限立即提交到后端。</p>
        </slot>
      </div>
    </div>

    <template #footer>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <UiButton variant="secondary" :disabled="pending" @click="handleClose">
          {{ cancelLabel }}
        </UiButton>
        <UiButton :variant="confirmVariant" :disabled="pending" @click="handleConfirm">
          {{ pending ? '处理中...' : confirmLabel }}
        </UiButton>
      </div>
    </template>
  </UiDialog>
</template>
