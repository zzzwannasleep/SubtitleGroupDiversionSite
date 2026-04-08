<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listCategoriesAdmin, saveCategoryItem } from '@/services/admin';
import type { Category } from '@/types/release';

const categories = ref<Category[]>([]);
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const form = reactive({
  name: '',
  slug: '',
});

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    categories.value = await listCategoriesAdmin();
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  feedback.value = '';
  errorMessage.value = '';

  try {
    await saveCategoryItem({ name: form.name, slug: form.slug });
    form.name = '';
    form.slug = '';
    feedback.value = '分类已保存。';
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存分类失败';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="分类管理" description="分类和标签页延续同一张表格卡片，不混多套样式。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="分类列表">
      <AppLoading v-if="loading" />
      <AppError v-else-if="failed" title="分类列表加载失败" description="请稍后重试，或检查分类接口。" />
      <AppEmpty v-else-if="!categories.length" title="还没有分类" description="创建第一个分类后会显示在这里。" />
      <UiTable v-else>
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
