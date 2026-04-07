<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import { useI18n } from "@/composables/useI18n";


type ConfirmTone = "default" | "danger";

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    tone?: ConfirmTone;
    busy?: boolean;
  }>(),
  {
    description: "",
    confirmLabel: "",
    cancelLabel: "",
    tone: "default",
    busy: false,
  },
);

const emit = defineEmits<{
  (event: "update:open", value: boolean): void;
  (event: "cancel"): void;
  (event: "confirm"): void;
}>();

const { t } = useI18n();
const confirmButtonRef = ref<HTMLButtonElement | null>(null);
const titleId = `confirm-dialog-title-${Math.random().toString(36).slice(2)}`;
const descriptionId = `confirm-dialog-description-${Math.random().toString(36).slice(2)}`;

function removeKeydownListener(): void {
  document.removeEventListener("keydown", handleKeydown);
}

function requestClose(): void {
  if (props.busy) {
    return;
  }

  emit("update:open", false);
  emit("cancel");
}

function requestConfirm(): void {
  if (props.busy) {
    return;
  }

  emit("confirm");
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key !== "Escape" || !props.open) {
    return;
  }

  event.preventDefault();
  requestClose();
}

watch(
  () => props.open,
  (isOpen) => {
    removeKeydownListener();
    if (!isOpen) {
      return;
    }

    document.addEventListener("keydown", handleKeydown);
    void nextTick(() => confirmButtonRef.value?.focus());
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  removeKeydownListener();
});
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div
        v-if="open"
        class="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm"
        role="presentation"
        @click.self="requestClose"
      >
        <section
          class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          :aria-describedby="description ? descriptionId : undefined"
        >
          <div class="flex items-start gap-4">
            <span
              class="mt-1 h-3 w-3 shrink-0 rounded-full"
              :class="tone === 'danger' ? 'bg-red-500' : 'bg-blue-600'"
              aria-hidden="true"
            />
            <div class="min-w-0">
              <h2 :id="titleId" class="text-lg font-semibold text-slate-950">{{ title }}</h2>
              <p v-if="description" :id="descriptionId" class="mt-2 text-sm leading-7 text-slate-600">
                {{ description }}
              </p>
            </div>
          </div>

          <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button
              class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-600/30 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="busy"
              @click="requestClose"
            >
              {{ cancelLabel || t("common.cancel") }}
            </button>
            <button
              ref="confirmButtonRef"
              class="rounded-xl px-4 py-3 text-sm font-semibold text-white transition focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
              :class="
                tone === 'danger'
                  ? 'bg-red-600 hover:bg-red-700 focus:ring-red-600/30'
                  : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-600/30'
              "
              type="button"
              :disabled="busy"
              @click="requestConfirm"
            >
              {{ busy ? t("common.working") : confirmLabel || t("common.confirm") }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
