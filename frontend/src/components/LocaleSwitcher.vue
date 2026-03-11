<script setup lang="ts">
import type { LocaleCode } from "@/locales";
import { useLocaleStore } from "@/stores/locale";
import { useI18n } from "@/composables/useI18n";


interface Props {
  variant?: "light" | "auth";
}


const props = withDefaults(defineProps<Props>(), {
  variant: "light",
});

const localeStore = useLocaleStore();
const { t } = useI18n();

function updateLocale(event: Event): void {
  localeStore.setLocale((event.target as HTMLSelectElement).value as LocaleCode);
}
</script>

<template>
  <label class="inline-flex">
    <span class="sr-only">{{ t("common.language") }}</span>
    <select
      :value="localeStore.locale"
      :aria-label="t('common.language')"
      class="rounded-full border px-3 py-2 text-sm font-medium transition"
      :class="
        props.variant === 'auth'
          ? 'border-[color:var(--auth-border)] bg-[color:var(--auth-surface-elevated)] text-[color:var(--auth-text)]'
          : 'border-slate-200 bg-white text-slate-700'
      "
      @change="updateLocale"
    >
      <option v-for="option in localeStore.options" :key="option.code" :value="option.code">
        {{ option.nativeLabel }}
      </option>
    </select>
  </label>
</template>
