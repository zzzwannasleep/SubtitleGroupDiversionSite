<script setup lang="ts">
export interface SelectOption {
  label: string;
  value: string;
}

withDefaults(
  defineProps<{
    modelValue?: string;
    options: SelectOption[];
    placeholder?: string;
    disabled?: boolean;
  }>(),
  {
    modelValue: '',
    placeholder: '',
    disabled: false,
  },
);

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();
</script>

<template>
  <select
    :value="modelValue"
    :disabled="disabled"
    class="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100"
    @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <option v-if="placeholder" value="">{{ placeholder }}</option>
    <option v-for="option in options" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</template>

