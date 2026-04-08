<script setup lang="ts">
import { computed } from 'vue';
import {
  announcementStatusLabels,
  audienceLabels,
  releaseStatusLabels,
  roleLabels,
  syncStatusLabels,
  userStatusLabels,
  xbtFileStateLabels,
  xbtUserStateLabels,
} from '@/utils/labels';

const props = defineProps<{
  type:
    | 'role'
    | 'user-status'
    | 'release-status'
    | 'sync-status'
    | 'announcement-status'
    | 'audience'
    | 'xbt-user-state'
    | 'xbt-file-state';
  value: string;
}>();

const meta = computed(() => {
  const map = {
    role: {
      admin: [roleLabels.admin, 'bg-slate-900 text-white'],
      uploader: [roleLabels.uploader, 'bg-blue-100 text-blue-700'],
      user: [roleLabels.user, 'bg-slate-100 text-slate-700'],
    },
    'user-status': {
      active: [userStatusLabels.active, 'bg-green-100 text-green-700'],
      disabled: [userStatusLabels.disabled, 'bg-red-100 text-red-700'],
    },
    'release-status': {
      published: [releaseStatusLabels.published, 'bg-green-100 text-green-700'],
      draft: [releaseStatusLabels.draft, 'bg-amber-100 text-amber-700'],
      hidden: [releaseStatusLabels.hidden, 'bg-slate-200 text-slate-700'],
    },
    'sync-status': {
      success: [syncStatusLabels.success, 'bg-green-100 text-green-700'],
      warning: [syncStatusLabels.warning, 'bg-amber-100 text-amber-700'],
      failed: [syncStatusLabels.failed, 'bg-red-100 text-red-700'],
    },
    'announcement-status': {
      online: [announcementStatusLabels.online, 'bg-green-100 text-green-700'],
      draft: [announcementStatusLabels.draft, 'bg-amber-100 text-amber-700'],
      offline: [announcementStatusLabels.offline, 'bg-slate-200 text-slate-700'],
    },
    audience: {
      all: [audienceLabels.all, 'bg-blue-100 text-blue-700'],
      uploader: [audienceLabels.uploader, 'bg-violet-100 text-violet-700'],
      admin: [audienceLabels.admin, 'bg-slate-900 text-white'],
    },
    'xbt-user-state': {
      enabled: [xbtUserStateLabels.enabled, 'bg-green-100 text-green-700'],
      disabled: [xbtUserStateLabels.disabled, 'bg-red-100 text-red-700'],
      missing: [xbtUserStateLabels.missing, 'bg-slate-200 text-slate-700'],
      unavailable: [xbtUserStateLabels.unavailable, 'bg-amber-100 text-amber-700'],
    },
    'xbt-file-state': {
      whitelisted: [xbtFileStateLabels.whitelisted, 'bg-green-100 text-green-700'],
      deleted: [xbtFileStateLabels.deleted, 'bg-red-100 text-red-700'],
      missing: [xbtFileStateLabels.missing, 'bg-slate-200 text-slate-700'],
      unavailable: [xbtFileStateLabels.unavailable, 'bg-amber-100 text-amber-700'],
    },
  } as const;

  const fallback = ['未知', 'bg-slate-100 text-slate-700'];
  const current = map[props.type][props.value as keyof typeof map[typeof props.type]] ?? fallback;

  return {
    label: current[0],
    classes: current[1],
  };
});
</script>

<template>
  <span :class="['inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold', meta.classes]">
    {{ meta.label }}
  </span>
</template>
