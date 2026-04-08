<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue?: string;
    placeholder?: string;
    rows?: number;
  }>(),
  {
    modelValue: '',
    placeholder: '',
    rows: 5,
  },
);

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();
</script>

<template>
  <textarea
    :value="modelValue"
    :rows="rows"
    :placeholder="placeholder"
    class="w-full rounded-md border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
    @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>

