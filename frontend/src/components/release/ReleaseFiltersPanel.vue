<script setup lang="ts">
import AppCard from '@/components/app/AppCard.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import type { Category, Tag } from '@/types/release';

defineProps<{
  q: string;
  category: string;
  tag: string;
  sort: string;
  categories: Category[];
  tags: Tag[];
}>();

const emit = defineEmits<{
  'update:q': [value: string];
  'update:category': [value: string];
  'update:tag': [value: string];
  'update:sort': [value: string];
  apply: [];
  reset: [];
}>();
</script>

<template>
  <AppCard title="筛选条件" description="按关键词、分类、标签和排序方式筛选资源。">
    <form class="grid gap-4 lg:grid-cols-4" @submit.prevent="emit('apply')">
      <div>
        <label class="app-field-label">关键词</label>
        <UiInput :model-value="q" placeholder="标题 / 副标题 / 简介" @update:model-value="emit('update:q', $event)" />
      </div>
      <div>
        <label class="app-field-label">分类</label>
        <UiSelect
          :model-value="category"
          :options="categories.map((item) => ({ label: item.name, value: item.slug }))"
          placeholder="全部分类"
          @update:model-value="emit('update:category', $event)"
        />
      </div>
      <div>
        <label class="app-field-label">标签</label>
        <UiSelect
          :model-value="tag"
          :options="tags.map((item) => ({ label: item.name, value: item.slug }))"
          placeholder="全部标签"
          @update:model-value="emit('update:tag', $event)"
        />
      </div>
      <div>
        <label class="app-field-label">排序</label>
        <UiSelect
          :model-value="sort"
          :options="[
            { label: '最新发布', value: 'latest' },
            { label: '下载次数', value: 'downloads' },
            { label: '完成次数', value: 'completions' },
          ]"
          @update:model-value="emit('update:sort', $event)"
        />
      </div>
      <div class="flex items-end gap-2 lg:col-span-4">
        <UiButton type="submit" variant="primary">应用筛选</UiButton>
        <UiButton type="button" variant="ghost" @click="emit('reset')">重置</UiButton>
      </div>
    </form>
  </AppCard>
</template>

