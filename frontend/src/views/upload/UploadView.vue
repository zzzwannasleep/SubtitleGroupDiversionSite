<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppCard from '@/components/app/AppCard.vue';
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
const feedback = ref('');

const form = reactive({
  title: '',
  subtitle: '',
  description: '',
  categorySlug: '',
  tagSlugs: [] as string[],
  torrentFileName: '',
});

onMounted(async () => {
  [categories.value, tags.value] = await Promise.all([listCategories(), listTags()]);
  form.categorySlug = categories.value[0]?.slug ?? '';
});

function toggleTag(slug: string) {
  if (form.tagSlugs.includes(slug)) {
    form.tagSlugs = form.tagSlugs.filter((item) => item !== slug);
    return;
  }

  form.tagSlugs = [...form.tagSlugs, slug];
}

async function submit(status: 'published' | 'draft') {
  if (!authStore.currentUser) return;
  const release = await createRelease({ ...form, status }, authStore.currentUser);
  feedback.value = status === 'published' ? `资源已发布：${release.title}` : `草稿已保存：${release.title}`;
}
</script>

<template>
  <AppPageHeader title="上传资源" description="仍属于前台布局，不混入后台管理区。" />

  <div v-if="feedback" class="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
    {{ feedback }}
  </div>

  <AppCard title="发布表单" description="上传页采用单列大表单，底部保留主要操作区。">
    <div class="space-y-5">
      <div>
        <label class="app-field-label">标题</label>
        <UiInput v-model="form.title" placeholder="例如：孤独摇滚！TV 01-12 合集" />
      </div>
      <div>
        <label class="app-field-label">副标题</label>
        <UiInput v-model="form.subtitle" placeholder="例如：BDRip 1080p 简繁内封" />
      </div>
      <div class="grid gap-5 md:grid-cols-2">
        <div>
          <label class="app-field-label">分类</label>
          <UiSelect
            v-model="form.categorySlug"
            :options="categories.map((item) => ({ label: item.name, value: item.slug }))"
          />
        </div>
        <div>
          <label class="app-field-label">torrent 文件名</label>
          <UiInput v-model="form.torrentFileName" placeholder="demo-release.torrent" />
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
      </div>
      <div>
        <label class="app-field-label">简介</label>
        <UiTextarea v-model="form.description" placeholder="简要说明版本、字幕、片源和注意事项" />
      </div>
    </div>

    <template #footer>
      <div class="flex flex-wrap items-center gap-2">
        <UiButton variant="primary" @click="submit('published')">发布资源</UiButton>
        <UiButton variant="secondary" @click="submit('draft')">保存草稿</UiButton>
      </div>
    </template>
  </AppCard>
</template>

