<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    open: boolean;
    title?: string;
    description?: string;
    closeOnOverlay?: boolean;
    widthClass?: string;
  }>(),
  {
    title: '',
    description: '',
    closeOnOverlay: true,
    widthClass: 'max-w-lg',
  },
);

const emit = defineEmits<{
  close: [];
}>();

const panelClasses = computed(() => [
  'w-full rounded-2xl border border-slate-200 bg-white shadow-xl',
  props.widthClass,
]);

function handleClose() {
  emit('close');
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) {
    handleClose();
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (typeof document === 'undefined') return;
    document.body.style.overflow = isOpen ? 'hidden' : '';
  },
  { immediate: true },
);

watch(
  () => props.open,
  (isOpen) => {
    if (typeof window === 'undefined') return;

    if (isOpen) {
      window.addEventListener('keydown', handleKeydown);
      return;
    }

    window.removeEventListener('keydown', handleKeydown);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.body.style.overflow = '';
  }

  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', handleKeydown);
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/45 px-4 py-6"
        @click="closeOnOverlay ? handleClose() : undefined"
      >
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="translate-y-3 scale-[0.98] opacity-0"
          enter-to-class="translate-y-0 scale-100 opacity-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="translate-y-0 scale-100 opacity-100"
          leave-to-class="translate-y-3 scale-[0.98] opacity-0"
        >
          <div
            v-if="open"
            :class="panelClasses"
            role="dialog"
            aria-modal="true"
            :aria-label="title || '对话框'"
            @click.stop
          >
            <header v-if="title || description || $slots.header" class="app-card-header border-b-0 pb-0">
              <div class="space-y-1">
                <h2 v-if="title" class="text-lg font-semibold text-slate-900">{{ title }}</h2>
                <p v-if="description" class="text-sm leading-6 text-slate-500">{{ description }}</p>
              </div>
              <div v-if="$slots.header" class="flex items-center gap-2">
                <slot name="header" />
              </div>
            </header>

            <div class="app-card-body">
              <slot />
            </div>

            <footer v-if="$slots.footer" class="app-card-footer">
              <slot name="footer" />
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
