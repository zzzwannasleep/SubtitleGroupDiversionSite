<script setup lang="ts">
import { RouterLink } from "vue-router";

import { useI18n } from "@/composables/useI18n";
import type { TorrentListItem } from "@/types";
import { formatBytes, formatDate } from "@/utils/format";


defineProps<{
  items: TorrentListItem[];
}>();

const { locale, t } = useI18n();
</script>

<template>
  <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="hidden overflow-x-auto md:block">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-slate-500">
          <tr>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.category") }}</th>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.title") }}</th>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.size") }}</th>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.uploader") }}</th>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.stats") }}</th>
            <th class="px-4 py-3 font-medium">{{ t("torrentTable.created") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="item in items" :key="item.id" class="hover:bg-slate-50/70">
            <td class="px-4 py-4 text-slate-600">{{ item.category }}</td>
            <td class="px-4 py-4">
              <RouterLink :to="`/torrents/${item.id}`" class="font-semibold text-slate-900 hover:text-blue-700">
                {{ item.name }}
              </RouterLink>
              <p v-if="item.subtitle" class="mt-1 text-xs text-slate-500">{{ item.subtitle }}</p>
            </td>
            <td class="px-4 py-4 text-slate-600">{{ formatBytes(item.size_bytes) }}</td>
            <td class="px-4 py-4 text-slate-600">{{ item.owner }}</td>
            <td class="px-4 py-4 text-slate-600">
              S {{ item.seeders }} / L {{ item.leechers }} / N {{ item.snatches }}
            </td>
            <td class="px-4 py-4 text-slate-600">{{ formatDate(item.created_at, locale) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="grid gap-3 p-4 md:hidden">
      <RouterLink
        v-for="item in items"
        :key="item.id"
        :to="`/torrents/${item.id}`"
        class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{{ item.category }}</p>
            <h3 class="mt-2 text-base font-semibold text-slate-900">{{ item.name }}</h3>
            <p v-if="item.subtitle" class="mt-1 text-sm text-slate-500">{{ item.subtitle }}</p>
          </div>
          <span v-if="item.is_free" class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            {{ t("torrentTable.free") }}
          </span>
        </div>
        <div class="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-600">
          <span>{{ formatBytes(item.size_bytes) }}</span>
          <span>{{ item.owner }}</span>
          <span>S {{ item.seeders }}</span>
          <span>L {{ item.leechers }}</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
