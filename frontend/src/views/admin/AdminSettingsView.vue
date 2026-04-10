<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { getSettings, saveSiteSettings } from '@/services/admin';
import { useSiteSettingsStore } from '@/stores/siteSettings';
import type { LoginBackgroundType, SaveSiteSettingsPayload, SiteSettings } from '@/types/admin';
import { buildLoginBackgroundStyle, buildSiteMonogram, DEFAULT_LOGIN_BACKGROUND_CSS } from '@/utils/site-branding';

const siteSettingsStore = useSiteSettingsStore();

const loading = ref(true);
const failed = ref(false);
const isSaving = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const siteIconFile = ref<File | null>(null);
const loginBackgroundFile = ref<File | null>(null);
const siteIconLocalPreviewUrl = ref('');
const loginBackgroundLocalPreviewUrl = ref('');
const clearSiteIconFile = ref(false);
const clearLoginBackgroundFile = ref(false);

const form = reactive({
  siteName: '',
  siteDescription: '',
  loginNotice: '',
  allowPublicRegistration: false,
  rssBasePath: '',
  downloadNotice: '',
  siteIconUrl: '',
  siteIconFileUrl: '',
  loginBackgroundType: 'css' as LoginBackgroundType,
  loginBackgroundApiUrl: '',
  loginBackgroundFileUrl: '',
  loginBackgroundCss: DEFAULT_LOGIN_BACKGROUND_CSS,
});

const backgroundModeOptions = [
  { label: 'API 图片地址', value: 'api' },
  { label: '上传文件', value: 'file' },
  { label: 'CSS 背景', value: 'css' },
];

function revokeObjectUrl(url: string) {
  if (url.startsWith('blob:')) {
    URL.revokeObjectURL(url);
  }
}

function replacePreviewUrl(target: typeof siteIconLocalPreviewUrl, nextUrl: string) {
  revokeObjectUrl(target.value);
  target.value = nextUrl;
}

function resetFileState() {
  siteIconFile.value = null;
  loginBackgroundFile.value = null;
  clearSiteIconFile.value = false;
  clearLoginBackgroundFile.value = false;
  replacePreviewUrl(siteIconLocalPreviewUrl, '');
  replacePreviewUrl(loginBackgroundLocalPreviewUrl, '');
}

function applySettings(settings: SiteSettings) {
  Object.assign(form, {
    siteName: settings.siteName,
    siteDescription: settings.siteDescription,
    loginNotice: settings.loginNotice,
    allowPublicRegistration: settings.allowPublicRegistration,
    rssBasePath: settings.rssBasePath,
    downloadNotice: settings.downloadNotice,
    siteIconUrl: settings.siteIconUrl,
    siteIconFileUrl: settings.siteIconFileUrl,
    loginBackgroundType: settings.loginBackgroundType,
    loginBackgroundApiUrl: settings.loginBackgroundApiUrl,
    loginBackgroundFileUrl: settings.loginBackgroundFileUrl,
    loginBackgroundCss: settings.loginBackgroundCss || DEFAULT_LOGIN_BACKGROUND_CSS,
  });
  resetFileState();
}

async function loadSettings() {
  loading.value = true;
  failed.value = false;

  try {
    const settings = await getSettings();
    applySettings(settings);
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadSettings);

onBeforeUnmount(() => {
  resetFileState();
});

function handleSiteIconFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const nextFile = input.files?.[0] ?? null;
  siteIconFile.value = nextFile;
  clearSiteIconFile.value = false;
  replacePreviewUrl(siteIconLocalPreviewUrl, nextFile ? URL.createObjectURL(nextFile) : '');
}

function handleLoginBackgroundFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const nextFile = input.files?.[0] ?? null;
  loginBackgroundFile.value = nextFile;
  clearLoginBackgroundFile.value = false;
  replacePreviewUrl(
    loginBackgroundLocalPreviewUrl,
    nextFile ? URL.createObjectURL(nextFile) : '',
  );
}

function clearUploadedSiteIcon() {
  siteIconFile.value = null;
  clearSiteIconFile.value = true;
  form.siteIconFileUrl = '';
  replacePreviewUrl(siteIconLocalPreviewUrl, '');
}

function clearUploadedLoginBackground() {
  loginBackgroundFile.value = null;
  clearLoginBackgroundFile.value = true;
  form.loginBackgroundFileUrl = '';
  replacePreviewUrl(loginBackgroundLocalPreviewUrl, '');
}

const resolvedSiteIconPreviewUrl = computed(() => {
  if (siteIconLocalPreviewUrl.value) {
    return siteIconLocalPreviewUrl.value;
  }

  if (!clearSiteIconFile.value && form.siteIconFileUrl) {
    return form.siteIconFileUrl;
  }

  return form.siteIconUrl.trim();
});

const resolvedLoginBackgroundPreviewUrl = computed(() => {
  if (form.loginBackgroundType === 'file') {
    if (loginBackgroundLocalPreviewUrl.value) {
      return loginBackgroundLocalPreviewUrl.value;
    }

    if (!clearLoginBackgroundFile.value) {
      return form.loginBackgroundFileUrl;
    }

    return '';
  }

  if (form.loginBackgroundType === 'api') {
    return form.loginBackgroundApiUrl.trim();
  }

  return '';
});

const loginPreviewStyle = computed(() =>
  buildLoginBackgroundStyle({
    loginBackgroundType: form.loginBackgroundType,
    loginBackgroundCss: form.loginBackgroundCss,
    loginBackgroundResolvedUrl: resolvedLoginBackgroundPreviewUrl.value,
  }),
);

const brandMonogram = computed(() => buildSiteMonogram(form.siteName));
const currentBackgroundModeLabel = computed(() => {
  return backgroundModeOptions.find((item) => item.value === form.loginBackgroundType)?.label ?? 'CSS 背景';
});

async function handleSave() {
  isSaving.value = true;
  feedback.value = '';
  errorMessage.value = '';

  try {
    const payload: SaveSiteSettingsPayload = {
      siteName: form.siteName,
      siteDescription: form.siteDescription,
      loginNotice: form.loginNotice,
      allowPublicRegistration: form.allowPublicRegistration,
      rssBasePath: form.rssBasePath,
      downloadNotice: form.downloadNotice,
      siteIconUrl: form.siteIconUrl,
      siteIconFile: siteIconFile.value,
      clearSiteIconFile: clearSiteIconFile.value,
      loginBackgroundType: form.loginBackgroundType,
      loginBackgroundApiUrl: form.loginBackgroundApiUrl,
      loginBackgroundFile: loginBackgroundFile.value,
      clearLoginBackgroundFile: clearLoginBackgroundFile.value,
      loginBackgroundCss: form.loginBackgroundCss,
    };
    const savedSettings = await saveSiteSettings(payload);
    applySettings(savedSettings);
    siteSettingsStore.publishSettings(savedSettings);
    feedback.value = '站点设置已保存。';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存站点设置失败。';
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <AppPageHeader
    title="系统设置"
    description="统一维护站点图标、登录页背景和站点提示文案，保存后会立刻影响 favicon 与登录页。"
  >
    <template #actions>
      <UiButton variant="primary" :disabled="isSaving" @click="handleSave">
        {{ isSaving ? '保存中...' : '保存设置' }}
      </UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
  <AppLoading v-if="loading" />
  <AppError
    v-else-if="failed"
    title="系统设置加载失败"
    description="请稍后重试，或检查站点设置接口是否可用。"
  />

  <div v-else class="grid gap-6 2xl:grid-cols-[1.05fr_0.95fr]">
    <div class="space-y-6">
      <AppCard title="站点品牌" description="支持设置站点名称、描述和站点图标，图标会同步到登录页动画与 favicon。">
        <div class="grid gap-5">
          <div>
            <label class="app-field-label">站点名称</label>
            <UiInput v-model="form.siteName" placeholder="例如：星门字幕组" />
          </div>

          <div>
            <label class="app-field-label">站点描述</label>
            <UiInput v-model="form.siteDescription" placeholder="例如：内部资源浏览、下载与订阅入口" />
          </div>

          <div>
            <label class="app-field-label">站点图标 URL</label>
            <UiInput
              v-model="form.siteIconUrl"
              placeholder="https://cdn.example.com/assets/favicon.png"
            />
            <p class="app-field-help">
              可填写 API 返回的静态图片地址；如果同时上传文件，上传文件会优先显示。
            </p>
          </div>

          <div>
            <label class="app-field-label">上传站点图标</label>
            <input
              class="settings-file-input"
              type="file"
              accept="image/*,.svg"
              @change="handleSiteIconFileChange"
            />
            <div class="settings-file-row">
              <p class="app-field-help">
                建议使用正方形图标，支持 PNG、JPG、WebP、SVG。
              </p>
              <UiButton
                v-if="form.siteIconFileUrl || siteIconLocalPreviewUrl"
                size="sm"
                variant="ghost"
                @click="clearUploadedSiteIcon"
              >
                清除上传图标
              </UiButton>
            </div>
          </div>

          <div class="brand-preview">
            <div :class="['brand-preview__icon', resolvedSiteIconPreviewUrl ? 'brand-preview__icon--plain' : '']">
              <img
                v-if="resolvedSiteIconPreviewUrl"
                :src="resolvedSiteIconPreviewUrl"
                :alt="`${form.siteName} 图标预览`"
                class="brand-preview__image"
              />
              <span v-else class="brand-preview__fallback">{{ brandMonogram }}</span>
            </div>
            <div class="min-w-0 space-y-1">
              <p class="text-xs uppercase tracking-[0.24em] text-slate-400">品牌预览</p>
              <p class="truncate text-lg font-semibold text-slate-900">{{ form.siteName }}</p>
              <p class="text-sm leading-6 text-slate-500">{{ form.siteDescription }}</p>
            </div>
          </div>
        </div>
      </AppCard>

      <AppCard title="基础文案" description="这些文案会用于登录页提示、RSS 和下载页说明。">
        <div class="grid gap-5">
          <div>
            <label class="app-field-label">登录提示</label>
            <UiTextarea v-model="form.loginNotice" :rows="3" />
          </div>
          <label class="settings-toggle">
            <div class="settings-toggle__copy">
              <span class="settings-toggle__title">开启自由注册</span>
              <span class="settings-toggle__description">开启后登录页会显示注册按钮，访客可自行创建普通用户账号。</span>
            </div>
            <input v-model="form.allowPublicRegistration" type="checkbox" class="settings-toggle__input" />
          </label>
          <div>
            <label class="app-field-label">RSS 基础路径</label>
            <UiInput v-model="form.rssBasePath" />
          </div>
          <div>
            <label class="app-field-label">下载提示</label>
            <UiTextarea v-model="form.downloadNotice" :rows="3" />
          </div>
        </div>
      </AppCard>
    </div>

    <div class="space-y-6">
      <AppCard title="登录页背景" description="支持 API、文件、CSS 三种改法，切换后会直接驱动登录页背景层。">
        <div class="grid gap-5">
          <div>
            <label class="app-field-label">背景方案</label>
            <UiSelect v-model="form.loginBackgroundType" :options="backgroundModeOptions" />
          </div>

          <div v-if="form.loginBackgroundType === 'api'">
            <label class="app-field-label">API 图片地址</label>
            <UiInput
              v-model="form.loginBackgroundApiUrl"
              placeholder="https://images.example.com/login-wallpaper.jpg"
            />
            <p class="app-field-help">填写浏览器可直接访问的图片地址，支持 CDN 或图床接口。</p>
          </div>

          <div v-else-if="form.loginBackgroundType === 'file'">
            <label class="app-field-label">上传背景图</label>
            <input
              class="settings-file-input"
              type="file"
              accept="image/*"
              @change="handleLoginBackgroundFileChange"
            />
            <div class="settings-file-row">
              <p class="app-field-help">
                推荐使用横版大图，保存后登录页将使用该文件作为背景。
              </p>
              <UiButton
                v-if="form.loginBackgroundFileUrl || loginBackgroundLocalPreviewUrl"
                size="sm"
                variant="ghost"
                @click="clearUploadedLoginBackground"
              >
                清除上传背景
              </UiButton>
            </div>
          </div>

          <div v-else>
            <label class="app-field-label">CSS background 值</label>
            <UiTextarea
              v-model="form.loginBackgroundCss"
              :rows="6"
              placeholder="linear-gradient(135deg, #020617 0%, #172554 100%)"
            />
            <p class="app-field-help">
              直接填写 CSS 的 `background` 值，例如渐变、叠加纹理或带 url 的复合背景。
            </p>
          </div>
        </div>
      </AppCard>

      <AppCard title="登录页预览" description="这里会模拟登录页视觉，方便确认图标、标题和背景模式的组合效果。">
        <div class="login-preview" :style="loginPreviewStyle">
          <div class="login-preview__overlay" />
          <div class="login-preview__glow login-preview__glow--left" />
          <div class="login-preview__glow login-preview__glow--right" />

          <div class="login-preview__content">
            <div class="login-preview__brand">
              <div :class="['login-preview__brand-icon', resolvedSiteIconPreviewUrl ? 'login-preview__brand-icon--plain' : '']">
                <img
                  v-if="resolvedSiteIconPreviewUrl"
                  :src="resolvedSiteIconPreviewUrl"
                  :alt="`${form.siteName} 品牌图标`"
                  class="login-preview__brand-image"
                />
                <span v-else class="login-preview__brand-fallback">{{ brandMonogram }}</span>
              </div>
              <div class="space-y-2">
                <p class="text-xs uppercase tracking-[0.24em] text-slate-300/90">登录页预览</p>
                <h2 class="text-2xl font-semibold text-white">{{ form.siteName }}</h2>
                <p class="text-sm leading-7 text-slate-200/88">{{ form.siteDescription }}</p>
              </div>
            </div>

            <div class="login-preview__card">
              <div class="space-y-1">
                <p class="text-lg font-semibold text-white">登录系统</p>
                <p class="text-sm text-slate-300/90">当前背景方案：{{ currentBackgroundModeLabel }}</p>
              </div>
              <div class="space-y-3">
                <div class="login-preview__field">用户名</div>
                <div class="login-preview__field">密码</div>
              </div>
              <p v-if="form.loginNotice" class="text-xs leading-6 text-slate-300/88">{{ form.loginNotice }}</p>
              <div class="login-preview__actions">
                <div class="login-preview__button">登录</div>
                <div v-if="form.allowPublicRegistration" class="login-preview__button login-preview__button--secondary">
                  注册
                </div>
              </div>
            </div>
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<style scoped>
.settings-file-input {
  display: block;
  width: 100%;
  border: 1px dashed rgb(148 163 184 / 0.42);
  border-radius: 14px;
  background: rgb(248 250 252);
  padding: 0.75rem 0.9rem;
  color: rgb(51 65 85);
  font-size: 0.92rem;
}

.settings-file-row {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.settings-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 18px;
  background: rgb(248 250 252);
  padding: 1rem 1.05rem;
}

.settings-toggle__copy {
  display: grid;
  gap: 0.25rem;
}

.settings-toggle__title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(15 23 42);
}

.settings-toggle__description {
  font-size: 0.85rem;
  line-height: 1.7;
  color: rgb(100 116 139);
}

.settings-toggle__input {
  height: 1.2rem;
  width: 1.2rem;
  flex-shrink: 0;
  accent-color: rgb(37 99 235);
}

.brand-preview {
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgb(191 219 254 / 0.34), transparent 38%),
    linear-gradient(135deg, rgb(248 250 252), rgb(241 245 249));
  padding: 1.1rem;
}

.brand-preview__icon {
  display: flex;
  height: 4.75rem;
  width: 4.75rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 1.4rem;
  background:
    linear-gradient(145deg, rgb(96 165 250 / 0.42), rgb(15 23 42 / 0.9)),
    rgb(15 23 42);
  box-shadow:
    0 18px 28px rgb(37 99 235 / 0.15),
    inset 0 1px 0 rgb(255 255 255 / 0.1);
}

.brand-preview__icon--plain {
  background: transparent;
  box-shadow: none;
}

.brand-preview__image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.brand-preview__fallback {
  color: white;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-preview {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  min-height: 420px;
  padding: 1.5rem;
  background: #020617;
}

.login-preview__overlay,
.login-preview__glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-preview__overlay {
  background:
    linear-gradient(180deg, rgb(2 6 23 / 0.16), rgb(2 6 23 / 0.42)),
    linear-gradient(90deg, rgb(255 255 255 / 0.04) 1px, transparent 1px),
    linear-gradient(rgb(255 255 255 / 0.04) 1px, transparent 1px);
  background-size: auto, 56px 56px, 56px 56px;
}

.login-preview__glow {
  filter: blur(84px);
  opacity: 0.38;
}

.login-preview__glow--left {
  inset: auto auto -10% -12%;
  height: 16rem;
  width: 16rem;
  border-radius: 9999px;
  background: rgb(59 130 246 / 0.62);
}

.login-preview__glow--right {
  inset: 8% -12% auto auto;
  height: 14rem;
  width: 14rem;
  border-radius: 9999px;
  background: rgb(244 114 182 / 0.4);
}

.login-preview__content {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 1.5rem;
}

.login-preview__brand {
  border: 1px solid rgb(148 163 184 / 0.18);
  border-radius: 24px;
  background: linear-gradient(180deg, rgb(15 23 42 / 0.74), rgb(15 23 42 / 0.46));
  backdrop-filter: blur(18px);
  padding: 1.2rem;
}

.login-preview__brand-icon {
  margin-bottom: 1rem;
  display: flex;
  height: 4.75rem;
  width: 4.75rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 1.4rem;
  background:
    linear-gradient(145deg, rgb(96 165 250 / 0.35), rgb(15 23 42 / 0.92)),
    rgb(15 23 42);
  box-shadow:
    0 18px 36px rgb(37 99 235 / 0.22),
    inset 0 1px 0 rgb(255 255 255 / 0.1);
}

.login-preview__brand-icon--plain {
  background: transparent;
  box-shadow: none;
}

.login-preview__brand-image {
  height: 100%;
  width: 100%;
  object-fit: contain;
}

.login-preview__brand-fallback {
  color: white;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.login-preview__card {
  border: 1px solid rgb(148 163 184 / 0.18);
  border-radius: 24px;
  background: linear-gradient(180deg, rgb(15 23 42 / 0.9), rgb(15 23 42 / 0.82));
  box-shadow: 0 28px 60px rgb(2 6 23 / 0.26);
  backdrop-filter: blur(18px);
  padding: 1.2rem;
}

.login-preview__field {
  border: 1px solid rgb(148 163 184 / 0.14);
  border-radius: 14px;
  background: rgb(30 41 59 / 0.84);
  color: rgb(226 232 240 / 0.94);
  padding: 0.78rem 0.85rem;
  font-size: 0.92rem;
}

.login-preview__actions {
  margin-top: 1rem;
  display: grid;
  gap: 0.75rem;
}

.login-preview__button {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgb(59 130 246), rgb(96 165 250));
  color: white;
  font-weight: 600;
  min-height: 2.8rem;
}

.login-preview__button--secondary {
  border: 1px solid rgb(148 163 184 / 0.2);
  background: rgb(255 255 255 / 0.14);
  color: rgb(241 245 249);
}

@media (min-width: 768px) {
  .login-preview__content {
    grid-template-columns: minmax(0, 1fr) minmax(300px, 0.9fr);
    align-items: center;
  }
}
</style>
