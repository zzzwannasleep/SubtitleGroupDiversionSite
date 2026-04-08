<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listCategoriesAdmin, saveCategoryItem } from '@/services/admin';
import type { Category } from '@/types/release';

const categories = ref<Category[]>([]);
const form = reactive({
  name: '',
  slug: '',
});

async function loadData() {
  categories.value = await listCategoriesAdmin();
}

async function handleSave() {
  await saveCategoryItem({ name: form.name, slug: form.slug });
  form.name = '';
  form.slug = '';
  await loadData();
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="分类管理" description="分类和标签页延续同一张表格卡片，不混多套样式。" />
  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="分类列表">
      <UiTable>
        <thead>
          <tr>
            <th>名称</th>
            <th>Slug</th>
            <th>排序</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in categories" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.slug }}</td>
            <td>{{ item.sortOrder }}</td>
          </tr>
        </tbody>
      </UiTable>
    </AppCard>
    <AppCard title="新建分类">
      <div class="space-y-4">
        <div>
          <label class="app-field-label">名称</label>
          <UiInput v-model="form.name" />
        </div>
        <div>
          <label class="app-field-label">Slug</label>
          <UiInput v-model="form.slug" />
        </div>
      </div>
      <template #footer>
        <UiButton variant="primary" @click="handleSave">保存分类</UiButton>
      </template>
    </AppCard>
  </div>
</template>

