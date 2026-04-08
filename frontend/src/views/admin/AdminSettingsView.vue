<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { getSettings, saveSiteSettings } from '@/services/admin';

const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const form = reactive({
  siteName: '',
  siteDescription: '',
  loginNotice: '',
  rssBasePath: '',
  downloadNotice: '',
});

async function loadSettings() {
  loading.value = true;
  failed.value = false;

  try {
    const settings = await getSettings();
    Object.assign(form, settings);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadSettings);

async function handleSave() {
  await saveSiteSettings({ ...form });
  feedback.value = '系统设置已保存。';
}
</script>

<template>
  <AppPageHeader title="系统设置" description="把站点基础信息、登录提示和下载提示收敛到一页维护。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppLoading v-if="loading" />
  <AppError v-else-if="failed" title="系统设置加载失败" description="请稍后重试，或检查系统设置接口。" />
  <AppCard v-else title="基础设置" description="MVP 先覆盖站点名称、描述、RSS 与下载提示。">
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
