<script setup lang="ts">
import { useI18n } from "@/composables/useI18n";
import { useToastStore, type ToastTone } from "@/stores/toast";


const toastStore = useToastStore();
const { t } = useI18n();

const toneClasses: Record<ToastTone, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-950",
  error: "border-red-200 bg-red-50 text-red-950",
  warning: "border-amber-200 bg-amber-50 text-amber-950",
  info: "border-sky-200 bg-sky-50 text-sky-950",
};

const markerClasses: Record<ToastTone, string> = {
  success: "bg-emerald-500",
  error: "bg-red-500",
  warning: "bg-amber-500",
  info: "bg-sky-500",
};
</script>

<template>
  <div
    class="pointer-events-none fixed right-4 top-4 z-[80] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-3"
    aria-live="polite"
    aria-atomic="false"
  >
    <TransitionGroup name="toast-list" tag="div" class="contents">
      <article
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="pointer-events-auto overflow-hidden rounded-2xl border shadow-lg backdrop-blur"
        :class="toneClasses[toast.tone]"
        :role="toast.tone === 'error' ? 'alert' : 'status'"
      >
        <div class="flex gap-3 p-4">
          <span class="mt-1 h-3 w-3 shrink-0 rounded-full" :class="markerClasses[toast.tone]" />
          <div class="min-w-0 flex-1">
            <p v-if="toast.title" class="text-sm font-semibold">{{ toast.title }}</p>
            <p class="text-sm leading-6" :class="{ 'mt-1': toast.title }">{{ toast.message }}</p>
          </div>
          <button
            class="shrink-0 rounded-lg px-2 text-sm font-semibold text-current/70 transition hover:bg-white/60 hover:text-current focus:outline-none focus:ring-2 focus:ring-current/30"
            type="button"
            :aria-label="t('common.dismissNotification')"
            @click="toastStore.dismiss(toast.id)"
          >
            x
          </button>
        </div>
      </article>
    </TransitionGroup>
  </div>
</template>
