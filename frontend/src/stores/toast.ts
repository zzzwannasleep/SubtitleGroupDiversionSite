import { ref } from "vue";
import { defineStore } from "pinia";


export type ToastTone = "success" | "error" | "info" | "warning";

export interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
  title?: string;
}

interface ToastOptions {
  tone?: ToastTone;
  message: string;
  title?: string;
  durationMs?: number;
}


const DEFAULT_DURATION_MS = 3800;


export const useToastStore = defineStore("toast", () => {
  const toasts = ref<ToastItem[]>([]);
  let nextId = 1;

  function dismiss(id: number): void {
    toasts.value = toasts.value.filter((toast) => toast.id !== id);
  }

  function push(options: ToastOptions): number {
    const id = nextId;
    nextId += 1;

    const toast: ToastItem = {
      id,
      tone: options.tone ?? "info",
      message: options.message,
      title: options.title,
    };

    toasts.value = [...toasts.value, toast];

    if (options.durationMs !== 0) {
      window.setTimeout(() => dismiss(id), options.durationMs ?? DEFAULT_DURATION_MS);
    }

    return id;
  }

  function success(message: string, title?: string): number {
    return push({ tone: "success", message, title });
  }

  function error(message: string, title?: string): number {
    return push({ tone: "error", message, title, durationMs: 6000 });
  }

  function warning(message: string, title?: string): number {
    return push({ tone: "warning", message, title });
  }

  function info(message: string, title?: string): number {
    return push({ tone: "info", message, title });
  }

  return {
    toasts,
    dismiss,
    push,
    success,
    error,
    warning,
    info,
  };
});
