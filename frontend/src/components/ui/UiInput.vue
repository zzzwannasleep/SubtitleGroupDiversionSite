<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue?: string;
    type?: string;
    placeholder?: string;
    disabled?: boolean;
  }>(),
  {
    modelValue: '',
    type: 'text',
    placeholder: '',
    disabled: false,
  },
);

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();
</script>

<template>
  <input
    :value="modelValue"
    :type="type"
    :placeholder="placeholder"
    :disabled="disabled"
    class="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100"
    @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>

