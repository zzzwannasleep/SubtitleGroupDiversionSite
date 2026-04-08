<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { getSettings, saveSiteSettings } from '@/services/admin';

const loading = ref(true);
const feedback = ref('');
const form = reactive({
  siteName: '',
  siteDescription: '',
  loginNotice: '',
  rssBasePath: '',
  downloadNotice: '',
});

onMounted(async () => {
  const settings = await getSettings();
  Object.assign(form, settings);
  loading.value = false;
});

async function handleSave() {
  await saveSiteSettings({ ...form });
  feedback.value = '系统设置已保存。';
}
</script>

<template>
  <AppPageHeader title="系统设置" description="把站点基础信息、登录提示和下载提示收敛到一页维护。" />
  <div v-if="feedback" class="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
    {{ feedback }}
  </div>
  <AppCard v-if="!loading" title="基础设置" description="MVP 先覆盖站点名称、描述、RSS 与下载提示。">
    <div class="grid gap-5">
      <div>
        <label class="app-field-label">站点名称</label>
        <UiInput v-model="form.siteName" />
      </div>
      <div>
        <label class="app-field-label">站点描述</label>
        <UiInput v-model="form.siteDescription" />
      </div>
      <div>
        <label class="app-field-label">登录提示</label>
        <UiTextarea v-model="form.loginNotice" :rows="3" />
      </div>
      <div>
        <label class="app-field-label">RSS 基础路径</label>
        <UiInput v-model="form.rssBasePath" />
      </div>
      <div>
        <label class="app-field-label">下载提示</label>
        <UiTextarea v-model="form.downloadNotice" :rows="3" />
      </div>
    </div>
    <template #footer>
      <UiButton variant="primary" @click="handleSave">保存设置</UiButton>
    </template>
  </AppCard>
</template>
