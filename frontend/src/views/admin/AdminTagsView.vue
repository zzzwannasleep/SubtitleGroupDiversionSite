<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listTagsAdmin, saveTagItem } from '@/services/admin';
import type { Tag } from '@/types/release';

const tags = ref<Tag[]>([]);
const form = reactive({
  name: '',
  slug: '',
});

async function loadData() {
  tags.value = await listTagsAdmin();
}

async function handleSave() {
  await saveTagItem({ name: form.name, slug: form.slug });
  form.name = '';
  form.slug = '';
  await loadData();
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="标签管理" description="标签输入统一在上，风格与分类页保持一致。" />
  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="标签列表">
      <UiTable>
        <thead>
          <tr>
            <th>名称</th>
            <th>Slug</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in tags" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.slug }}</td>
          </tr>
        </tbody>
      </UiTable>
    </AppCard>
    <AppCard title="新建标签">
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
        <UiButton variant="primary" @click="handleSave">保存标签</UiButton>
      </template>
    </AppCard>
  </div>
</template>
