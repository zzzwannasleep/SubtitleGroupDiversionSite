<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { FileUp } from 'lucide-vue-next';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTextarea from '@/components/ui/UiTextarea.vue';
import { createRelease, listCategories, listTags } from '@/services/releases';
import { useAuthStore } from '@/stores/auth';
import type { Category, Tag } from '@/types/release';

const authStore = useAuthStore();
const categories = ref<Category[]>([]);
const tags = ref<Tag[]>([]);
const loading = ref(true);
const submitting = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const fileInputKey = ref(0);

const form = reactive({
  title: '',
  subtitle: '',
  description: '',
  categorySlug: '',
  tagSlugs: [] as string[],
  torrentFile: null as File | null,
  torrentFileName: '',
});

const validationMessage = computed(() => {
  if (!form.title.trim()) return '请先填写标题。';
  if (!form.subtitle.trim()) return '请先填写副标题。';
  if (!form.categorySlug) return '请先选择分类。';
  if (!form.description.trim()) return '请先填写简介。';
  if (!form.torrentFile && !form.torrentFileName) return '请先选择一个 .torrent 文件。';
  return '';
});

const canSubmit = computed(() => !validationMessage.value && !submitting.value);
const selectedCategory = computed(() => categories.value.find((item) => item.slug === form.categorySlug) ?? null);
const selectedTags = computed(() => tags.value.filter((item) => form.tagSlugs.includes(item.slug)));

async function loadOptions() {
  loading.value = true;
  errorMessage.value = '';

  try {
    const [categoryList, tagList] = await Promise.all([listCategories(), listTags()]);
    categories.value = categoryList;
    tags.value = tagList;
    form.categorySlug = categoryList[0]?.slug ?? '';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '分类和标签加载失败。';
  } finally {
    loading.value = false;
  }
}

function toggleTag(slug: string) {
  if (form.tagSlugs.includes(slug)) {
    form.tagSlugs = form.tagSlugs.filter((item) => item !== slug);
    return;
  }

  form.tagSlugs = [...form.tagSlugs, slug];
}

function handleTorrentChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  form.torrentFile = file;
  form.torrentFileName = file?.name ?? '';
}

function resetForm() {
  form.title = '';
  form.subtitle = '';
  form.description = '';
  form.categorySlug = categories.value[0]?.slug ?? '';
  form.tagSlugs = [];
  form.torrentFile = null;
  form.torrentFileName = '';
  fileInputKey.value += 1;
}

async function submit(status: 'published' | 'draft') {
  if (!authStore.currentUser) return;
  if (!canSubmit.value) {
    feedback.value = '';
    errorMessage.value = validationMessage.value;
    return;
  }

  errorMessage.value = '';
  feedback.value = '';
  submitting.value = true;

  try {
    const release = await createRelease(
      {
        title: form.title,
        subtitle: form.subtitle,
        description: form.description,
        categorySlug: form.categorySlug,
        tagSlugs: form.tagSlugs,
        torrentFile: form.torrentFile,
        torrentFileName: form.torrentFileName,
        status,
      },
      authStore.currentUser,
    );
    feedback.value = status === 'published' ? `资源已发布：${release.title}` : `草稿已保存：${release.title}`;
    resetForm();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提交资源失败。';
  } finally {
    submitting.value = false;
  }
}

onMounted(loadOptions);
</script>

<template>
  <AppPageHeader
    title="上传资源"
    description="这里只负责站内资源发布。上传的 torrent 会在后端自动转成 private 模板，不要求你手动先处理。"
  />

  <AppLoading v-if="loading" />
  <template v-else>
    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="mx-auto max-w-5xl">
      <AppCard title="发布表单" description="保留真正影响浏览和下载的信息，把发布动作尽量压缩到一屏内。">
        <div class="space-y-6">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex items-start gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-100 text-blue-700">
                <FileUp class="h-5 w-5" />
              </div>
              <div class="space-y-1">
                <h3 class="text-base font-semibold text-slate-900">发布时自动私有化</h3>
                <p class="text-sm leading-6 text-slate-600">
                  这里上传的 torrent 不再要求你手动先做成 private。后端会自动改写后再入库。
                </p>
              </div>
            </div>
          </div>

          <div class="space-y-5">
            <div>
              <label class="app-field-label">标题</label>
              <UiInput v-model="form.title" placeholder="例如：孤独摇滚！TV 01-12 合集" />
              <p class="app-field-help">标题会直接出现在首页、列表页和详情页。</p>
            </div>

            <div>
              <label class="app-field-label">副标题</label>
              <UiInput v-model="form.subtitle" placeholder="例如：BDRip 1080p 简繁内封" />
              <p class="app-field-help">建议补充分辨率、字幕语言和片源版本。</p>
            </div>

            <div class="grid gap-5 md:grid-cols-2">
              <div>
                <label class="app-field-label">分类</label>
                <UiSelect
                  v-model="form.categorySlug"
                  :options="categories.map((item) => ({ label: item.name, value: item.slug }))"
                  placeholder="请选择分类"
                />
                <p class="app-field-help">
                  {{ selectedCategory ? `当前将发布到“${selectedCategory.name}”分类。` : '请选择一个分类。' }}
                </p>
              </div>

              <div>
                <label class="app-field-label">torrent 文件</label>
                <input
                  :key="fileInputKey"
                  type="file"
                  accept=".torrent,application/x-bittorrent"
                  class="block h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  @change="handleTorrentChange"
                />
                <p class="app-field-help">
                  {{
                    form.torrentFileName
                      ? `已选择：${form.torrentFileName}`
                      : '请选择一个 .torrent 文件，系统会自动转成 private 模板。'
                  }}
                </p>
              </div>
            </div>

            <div>
              <label class="app-field-label">标签</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="tag in tags"
                  :key="tag.slug"
                  type="button"
                  :class="[
                    'rounded-full px-3 py-1.5 text-sm transition',
                    form.tagSlugs.includes(tag.slug)
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200',
                  ]"
                  @click="toggleTag(tag.slug)"
                >
                  {{ tag.name }}
                </button>
              </div>
              <p class="app-field-help">
                {{ selectedTags.length ? `已选择 ${selectedTags.length} 个标签。` : '标签用于列表筛选和 RSS 订阅。' }}
              </p>
            </div>

            <div>
              <label class="app-field-label">简介</label>
              <UiTextarea v-model="form.description" placeholder="简要说明版本、字幕、片源和注意事项" />
              <p class="app-field-help">
                {{ validationMessage || '提交前请确认标题、分类、简介和 torrent 文件已填写完整。' }}
              </p>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <p class="text-sm text-slate-500">站内发布仍然只对上传者和管理员开放。</p>
            <div class="flex flex-wrap items-center gap-2">
              <UiButton variant="primary" :disabled="!canSubmit" @click="submit('published')">
                {{ submitting ? '正在提交...' : '发布资源' }}
              </UiButton>
              <UiButton variant="secondary" :disabled="!canSubmit" @click="submit('draft')">
                保存草稿
              </UiButton>
            </div>
          </div>
        </template>
      </AppCard>
    </div>
  </template>
</template>
