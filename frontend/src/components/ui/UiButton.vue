<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, type RouteLocationRaw } from 'vue-router';

const props = withDefaults(
  defineProps<{
    to?: RouteLocationRaw;
    href?: string;
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    type?: 'button' | 'submit' | 'reset';
    block?: boolean;
    disabled?: boolean;
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    type: 'button',
    block: false,
    disabled: false,
  },
);

const componentTag = computed(() => {
  if (props.to) return RouterLink;
  if (props.href) return 'a';
  return 'button';
});

const classes = computed(() => {
  const base =
    'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-60';
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50',
    ghost: 'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };
  const sizes = {
    sm: 'h-9 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-11 px-5 text-base',
  };

  return [base, variants[props.variant], sizes[props.size], props.block ? 'w-full' : ''].join(' ');
});
</script>

<template>
  <component
    :is="componentTag"
    :to="to"
    :href="href"
    :type="componentTag === 'button' ? type : undefined"
    :class="classes"
    :disabled="disabled"
  >
    <slot />
  </component>
</template>

