<script setup lang="ts">
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiTable from '@/components/ui/UiTable.vue';
import type { Release } from '@/types/release';
import { formatBytes, formatDateTime } from '@/utils/format';

defineProps<{
  releases: Release[];
  showStatus?: boolean;
}>();
</script>

<template>
  <UiTable>
    <thead>
      <tr>
        <th>资源</th>
        <th>分类</th>
        <th>大小</th>
        <th>发布时间</th>
        <th>发布者</th>
        <th v-if="showStatus">状态</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="release in releases" :key="release.id">
        <td class="min-w-[240px]">
          <div class="space-y-1">
            <p class="font-medium text-slate-900">{{ release.title }}</p>
            <p class="text-xs text-slate-500">{{ release.subtitle }}</p>
          </div>
        </td>
        <td>{{ release.category.name }}</td>
        <td>{{ formatBytes(release.sizeBytes) }}</td>
        <td>{{ formatDateTime(release.publishedAt) }}</td>
        <td>{{ release.createdBy.displayName }}</td>
        <td v-if="showStatus">
          <AppStatusBadge type="release-status" :value="release.status" />
        </td>
        <td>
          <div class="flex flex-wrap items-center gap-2">
            <slot name="actions" :release="release" />
          </div>
        </td>
      </tr>
    </tbody>
  </UiTable>
</template>

