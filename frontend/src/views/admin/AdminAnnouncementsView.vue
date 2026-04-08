<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { listAnnouncements, saveAnnouncementItem } from '@/services/admin';
import type { Announcement } from '@/types/admin';

const announcements = ref<Announcement[]>([]);
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const form = reactive({
  title: '',
  content: '',
  status: 'online',
  audience: 'all',
});

async function loadData() {
  loading.value = true;
  failed.value = false;

  try {
    announcements.value = await listAnnouncements();
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
    await saveAnnouncementItem({
      title: form.title,
      content: form.content,
      status: form.status as Announcement['status'],
      audience: form.audience as Announcement['audience'],
    });
    form.title = '';
    form.content = '';
    form.status = 'online';
    form.audience = 'all';
    feedback.value = '公告已保存。';
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存公告失败';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader title="公告管理" description="前台公告条与后台公告管理共享一套数据源。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="公告列表">
      <AppLoading v-if="loading" />
      <AppError v-else-if="failed" title="公告列表加载失败" description="请稍后重试，或检查公告接口。" />
      <AppEmpty v-else-if="!announcements.length" title="暂无公告" description="新建公告后会显示在这里。" />
      <div v-else class="space-y-3">
        <div
          v-for="item in announcements"
          :key="item.id"
          class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="font-medium text-slate-900">{{ item.title }}</p>
              <p class="mt-1 text-sm text-slate-500">{{ item.content }}</p>
            </div>
            <div class="flex flex-col items-end gap-2">
              <AppStatusBadge type="announcement-status" :value="item.status" />
              <AppStatusBadge type="audience" :value="item.audience" />
            </div>
          </div>
        </div>
      </div>
    </AppCard>

    <AppCard title="新建公告">
      <div class="space-y-4">
        <div>
          <label class="app-field-label">标题</label>
          <UiInput v-model="form.title" />
        </div>
        <div>
          <label class="app-field-label">内容</label>
          <UiTextarea v-model="form.content" :rows="4" />
        </div>
        <div>
          <label class="app-field-label">状态</label>
          <UiSelect
            v-model="form.status"
            :options="[
              { label: '上线', value: 'online' },
              { label: '草稿', value: 'draft' },
              { label: '下线', value: 'offline' },
            ]"
          />
        </div>
        <div>
          <label class="app-field-label">可见范围</label>
          <UiSelect
            v-model="form.audience"
            :options="[
              { label: '全部用户', value: 'all' },
              { label: '上传者', value: 'uploader' },
              { label: '管理员', value: 'admin' },
            ]"
          />
        </div>
      </div>
      <template #footer>
        <UiButton variant="primary" @click="handleSave">保存公告</UiButton>
      </template>
    </AppCard>
  </div>
</template>
