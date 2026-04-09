<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import ReleaseListTable from '@/components/release/ReleaseListTable.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiDialog from '@/components/ui/UiDialog.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { listAdminReleases, toggleReleaseStatus } from '@/services/releases';
import { getTrackerSyncReleaseDetail, runTrackerSyncForRelease } from '@/services/trackerSync';
import type { TrackerSyncReleaseDetail } from '@/types/admin';
import type { Release } from '@/types/release';
import { formatDateTime } from '@/utils/format';

const releases = ref<Release[]>([]);
const status = ref<'all' | 'published' | 'draft' | 'hidden'>('all');
const loading = ref(true);
const failed = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const pendingAction = ref(false);
const targetRelease = ref<Release | null>(null);
const trackerDialogTarget = ref<Release | null>(null);
const trackerDetail = ref<TrackerSyncReleaseDetail | null>(null);
const trackerLoading = ref(false);
const trackerErrorMessage = ref('');
const pendingReleaseSync = ref(false);

const trackerFacts = computed(() => {
  if (!trackerDetail.value?.xbtFile) return [];

  return [
    {
      label: 'Seeders',
      value: trackerDetail.value.xbtFile.seeders === null ? '-' : `${trackerDetail.value.xbtFile.seeders}`,
    },
    {
      label: 'Leechers',
      value: trackerDetail.value.xbtFile.leechers === null ? '-' : `${trackerDetail.value.xbtFile.leechers}`,
    },
    {
      label: '完成数',
      value: trackerDetail.value.xbtFile.completed === null ? '-' : `${trackerDetail.value.xbtFile.completed}`,
    },
    {
      label: '最近镜像更新时间',
      value: trackerDetail.value.xbtFile.updatedAt ? formatDateTime(trackerDetail.value.xbtFile.updatedAt) : '-',
    },
  ];
});

async function loadReleases() {
  loading.value = true;
  failed.value = false;

  try {
    const data = await listAdminReleases({ status: status.value });
    releases.value = data.results;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

function openToggleDialog(release: Release) {
  targetRelease.value = release;
}

async function handleToggle() {
  if (!targetRelease.value) return;

  const release = targetRelease.value;
  const nextStatus = release.status === 'hidden' ? 'published' : 'hidden';

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = true;

  try {
    await toggleReleaseStatus(release.id, nextStatus);
    feedback.value = nextStatus === 'hidden' ? `已隐藏资源：${release.title}` : `已恢复资源：${release.title}`;
    targetRelease.value = null;
    await loadReleases();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新资源状态失败';
  } finally {
    pendingAction.value = false;
  }
}

async function loadTrackerDetail(releaseId: number) {
  trackerLoading.value = true;
  trackerErrorMessage.value = '';
  trackerDetail.value = null;

  try {
    trackerDetail.value = await getTrackerSyncReleaseDetail(releaseId);
    if (!trackerDetail.value) {
      trackerErrorMessage.value = '当前资源没有可用的 XBT 同步详情。';
    }
  } catch (error) {
    trackerErrorMessage.value = error instanceof Error ? error.message : '加载资源 XBT 详情失败';
  } finally {
    trackerLoading.value = false;
  }
}

async function openTrackerDialog(release: Release) {
  trackerDialogTarget.value = release;
  await loadTrackerDetail(release.id);
}

function closeTrackerDialog() {
  trackerDialogTarget.value = null;
  trackerDetail.value = null;
  trackerErrorMessage.value = '';
  trackerLoading.value = false;
}

async function handleRunReleaseSync() {
  if (!trackerDialogTarget.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingReleaseSync.value = true;

  try {
    await runTrackerSyncForRelease(trackerDialogTarget.value.id);
    feedback.value = `已手动触发资源 XBT 同步：${trackerDialogTarget.value.title}`;
    await Promise.all([loadReleases(), loadTrackerDetail(trackerDialogTarget.value.id)]);
  } catch (error) {
    trackerErrorMessage.value = error instanceof Error ? error.message : '手动同步资源到 XBT 失败';
  } finally {
    pendingReleaseSync.value = false;
  }
}

onMounted(loadReleases);
</script>

<template>
  <AppPageHeader title="资源管理" description="后台可查看全部资源，并执行隐藏、恢复和资源级 XBT 同步操作。" />
  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <AppCard title="资源列表" description="支持状态筛选、前台可见性调整，以及资源级 XBT 详情入口。">
    <div class="mb-4 flex flex-wrap gap-3">
      <UiSelect
        v-model="status"
        :options="[
          { label: '全部状态', value: 'all' },
          { label: '已发布', value: 'published' },
          { label: '草稿', value: 'draft' },
          { label: '已隐藏', value: 'hidden' },
        ]"
      />
      <UiButton variant="primary" @click="loadReleases">筛选</UiButton>
    </div>
    <AppLoading v-if="loading" />
    <AppError v-else-if="failed" title="资源管理加载失败" description="请稍后重试，或检查资源管理接口。" />
    <AppEmpty v-else-if="!releases.length" title="没有匹配的资源" description="当前筛选条件下没有可管理资源。" />
    <ReleaseListTable v-else :releases="releases" show-status>
      <template #actions="{ release }">
        <UiButton :to="`/releases/${release.id}`" size="sm">查看</UiButton>
        <UiButton variant="secondary" size="sm" @click="openTrackerDialog(release)">XBT 详情</UiButton>
        <UiButton variant="ghost" size="sm" :disabled="pendingAction" @click="openToggleDialog(release)">
          {{ release.status === 'hidden' ? '恢复' : '隐藏' }}
        </UiButton>
      </template>
    </ReleaseListTable>
  </AppCard>

  <AppConfirmDialog
    :open="targetRelease !== null"
    :title="targetRelease?.status === 'hidden' ? '确认恢复该资源' : '确认隐藏该资源'"
    :description="
      targetRelease?.status === 'hidden'
        ? `恢复后，资源《${targetRelease?.title ?? ''}》会重新出现在前台列表和详情页中。`
        : `隐藏后，资源《${targetRelease?.title ?? ''}》将从前台浏览入口移除，仅管理员仍可查看。`
    "
    :confirm-label="targetRelease?.status === 'hidden' ? '确认恢复' : '确认隐藏'"
    :tone="targetRelease?.status === 'hidden' ? 'primary' : 'warning'"
    :pending="pendingAction"
    @close="targetRelease = null"
    @confirm="handleToggle"
  >
    <p>这个动作只改变前台可见性，不会删除资源记录和已有的下载审计信息。</p>
  </AppConfirmDialog>

  <UiDialog
    :open="trackerDialogTarget !== null"
    :title="trackerDialogTarget ? `${trackerDialogTarget.title} / XBT 详情` : 'XBT 详情'"
    description="这里接入了资源级同步详情接口，可查看白名单镜像与最近同步日志。"
    width-class="max-w-4xl"
    @close="closeTrackerDialog"
  >
    <AppLoading v-if="trackerLoading" />
    <AppError
      v-else-if="trackerErrorMessage"
      title="资源 XBT 详情加载失败"
      :description="trackerErrorMessage"
    />
    <template v-else-if="trackerDetail">
      <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div class="space-y-6">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex flex-wrap items-center gap-2">
              <AppStatusBadge type="release-status" :value="trackerDetail.release.status" />
              <AppStatusBadge type="xbt-file-state" :value="trackerDetail.xbtFile.state" />
            </div>
            <dl class="mt-4 grid gap-3 sm:grid-cols-2">
              <div>
                <dt class="text-xs text-slate-500">资源 ID</dt>
                <dd class="mt-1 text-sm font-medium text-slate-900">{{ trackerDetail.release.id }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">发布者 ID</dt>
                <dd class="mt-1 text-sm font-medium text-slate-900">{{ trackerDetail.release.createdById }}</dd>
              </div>
              <div class="sm:col-span-2">
                <dt class="text-xs text-slate-500">Infohash</dt>
                <dd class="mt-1 break-all text-sm font-medium text-slate-900">{{ trackerDetail.release.infohash }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">发布时间</dt>
                <dd class="mt-1 text-sm font-medium text-slate-900">
                  {{ formatDateTime(trackerDetail.release.publishedAt) }}
                </dd>
              </div>
              <div>
                <dt class="text-xs text-slate-500">最近同步</dt>
                <dd class="mt-1 text-sm font-medium text-slate-900">
                  {{ trackerDetail.trackerSync ? formatDateTime(trackerDetail.trackerSync.updatedAt) : '-' }}
                </dd>
              </div>
            </dl>
          </div>

          <div>
            <p class="mb-2 text-sm text-slate-500">最近同步日志</p>
            <UiTable v-if="trackerDetail.recentLogs.length">
              <thead>
                <tr>
                  <th>状态</th>
                  <th>说明</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in trackerDetail.recentLogs" :key="item.id">
                  <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
                  <td>{{ item.message }}</td>
                  <td class="whitespace-nowrap text-slate-500">{{ formatDateTime(item.updatedAt) }}</td>
                </tr>
              </tbody>
            </UiTable>
            <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              当前还没有资源级同步日志。
            </p>
          </div>
        </div>

        <div class="space-y-6">
          <div>
            <p class="mb-2 text-sm text-slate-500">同步摘要</p>
            <div v-if="trackerDetail.trackerSync" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div class="flex items-center justify-between gap-3">
                <AppStatusBadge type="sync-status" :value="trackerDetail.trackerSync.status" />
                <span class="text-xs text-slate-500">{{ formatDateTime(trackerDetail.trackerSync.updatedAt) }}</span>
              </div>
              <p class="mt-3 text-sm leading-6 text-slate-600">{{ trackerDetail.trackerSync.message }}</p>
            </div>
            <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              当前还没有同步摘要。
            </p>
          </div>

          <div>
            <p class="mb-2 text-sm text-slate-500">XBT 镜像状态</p>
            <div class="grid gap-3">
              <div
                v-for="item in trackerFacts"
                :key="item.label"
                class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <p class="text-xs text-slate-500">{{ item.label }}</p>
                <p class="mt-2 text-sm font-medium text-slate-900">{{ item.value }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <div class="flex flex-wrap gap-2">
          <UiButton v-if="trackerDialogTarget" :to="`/releases/${trackerDialogTarget.id}`" variant="ghost">
            打开资源页
          </UiButton>
          <UiButton variant="secondary" @click="closeTrackerDialog">关闭</UiButton>
        </div>
        <UiButton
          variant="primary"
          :disabled="!trackerDialogTarget || pendingReleaseSync"
          @click="handleRunReleaseSync"
        >
          {{ pendingReleaseSync ? '同步中...' : '手动同步到 XBT' }}
        </UiButton>
      </div>
    </template>
  </UiDialog>
</template>
