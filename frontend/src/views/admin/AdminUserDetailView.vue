<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppConfirmDialog from '@/components/app/AppConfirmDialog.vue';
import AppError from '@/components/app/AppError.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { changeUserStatus, getUserDetail, resetUserPasskey, updateUser } from '@/services/admin';
import { getTrackerSyncUserDetail, runTrackerSyncForUser } from '@/services/trackerSync';
import type { AdminUser, TrackerSyncUserDetail, UpdateUserPayload } from '@/types/admin';
import { formatBytes, formatDateTime } from '@/utils/format';

const route = useRoute();
const state = ref<'loading' | 'ready' | 'not-found' | 'error'>('loading');
const user = ref<AdminUser | null>(null);
const trackerDetail = ref<TrackerSyncUserDetail | null>(null);
const feedback = ref('');
const errorMessage = ref('');
const pendingAction = ref<'save-profile' | 'toggle-status' | 'reset-passkey' | 'sync-user' | null>(null);
const activeDialog = ref<'toggle-status' | 'reset-passkey' | null>(null);
const form = reactive({
  displayName: '',
  email: '',
  role: 'user',
});

const statusActionMeta = computed(() => {
  if (!user.value) {
    return {
      confirmLabel: '确认',
      description: '',
      tone: 'primary' as const,
    };
  }

  const isDisabling = user.value.status === 'active';

  return {
    confirmLabel: isDisabling ? '确认禁用' : '确认启用',
    description: isDisabling
      ? `禁用后，用户 ${user.value.displayName} 将无法继续登录、下载和使用 RSS。`
      : `启用后，用户 ${user.value.displayName} 将恢复正常访问权限。`,
    tone: isDisabling ? ('danger' as const) : ('primary' as const),
  };
});

const currentTrackerSync = computed(() => trackerDetail.value?.trackerSync ?? user.value?.trackerSync ?? null);
const currentXbtUser = computed(() => trackerDetail.value?.xbtUser ?? user.value?.xbtUser ?? null);
const recentLogs = computed(() => trackerDetail.value?.recentLogs ?? []);

const trackerFacts = computed(() => {
  if (!currentXbtUser.value) return [];

  return [
    {
      label: '可下载',
      value: currentXbtUser.value.canLeech === null ? '-' : currentXbtUser.value.canLeech ? '是' : '否',
    },
    {
      label: '已下载',
      value: currentXbtUser.value.downloaded === null ? '-' : formatBytes(currentXbtUser.value.downloaded),
    },
    {
      label: '已上传',
      value: currentXbtUser.value.uploaded === null ? '-' : formatBytes(currentXbtUser.value.uploaded),
    },
    {
      label: '完成数',
      value: currentXbtUser.value.completed === null ? '-' : `${currentXbtUser.value.completed}`,
    },
  ];
});

const fullProfilePayload = computed<UpdateUserPayload>(() => ({
  displayName: form.displayName.trim(),
  email: form.email.trim(),
  role: form.role as UpdateUserPayload['role'],
}));

const changedProfilePayload = computed<Partial<UpdateUserPayload>>(() => {
  if (!user.value) return {};

  const nextPayload: Partial<UpdateUserPayload> = {};

  if (form.displayName.trim() !== user.value.displayName) {
    nextPayload.displayName = form.displayName.trim();
  }

  if (form.email.trim() !== user.value.email) {
    nextPayload.email = form.email.trim();
  }

  if (form.role !== user.value.role) {
    nextPayload.role = form.role as UpdateUserPayload['role'];
  }

  return nextPayload;
});

const canSaveProfile = computed(() => {
  return Boolean(
    user.value &&
      form.displayName.trim() &&
      form.email.trim() &&
      form.role &&
      Object.keys(changedProfilePayload.value).length,
  );
});

function syncFormFromUser(nextUser: AdminUser) {
  form.displayName = nextUser.displayName;
  form.email = nextUser.email;
  form.role = nextUser.role;
}

async function fetchUserData(userId: number) {
  const [nextUser, nextTrackerDetail] = await Promise.all([
    getUserDetail(userId),
    getTrackerSyncUserDetail(userId),
  ]);

  return { nextUser, nextTrackerDetail };
}

async function loadUserDetail() {
  const userId = Number(route.params.id);

  state.value = 'loading';
  user.value = null;
  trackerDetail.value = null;
  feedback.value = '';
  errorMessage.value = '';

  try {
    const { nextUser, nextTrackerDetail } = await fetchUserData(userId);
    if (!nextUser || !nextTrackerDetail) {
      state.value = 'not-found';
      return;
    }

    user.value = nextUser;
    trackerDetail.value = nextTrackerDetail;
    syncFormFromUser(nextUser);
    state.value = 'ready';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '用户详情加载失败';
    state.value = 'error';
  }
}

async function refreshUserDetailSilently() {
  const userId = Number(route.params.id);
  const { nextUser, nextTrackerDetail } = await fetchUserData(userId);

  if (nextUser && nextTrackerDetail) {
    user.value = nextUser;
    trackerDetail.value = nextTrackerDetail;
    syncFormFromUser(nextUser);
    state.value = 'ready';
  }
}

async function handleSaveProfile() {
  if (!user.value || !canSaveProfile.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = 'save-profile';

  try {
    const method = Object.keys(changedProfilePayload.value).length === 3 ? 'PUT' : 'PATCH';
    const payload = method === 'PUT' ? fullProfilePayload.value : changedProfilePayload.value;

    await updateUser(user.value.id, payload, method);
    await refreshUserDetailSilently();
    feedback.value = method === 'PUT' ? '用户资料已完整更新。' : '用户资料已局部更新。';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新用户资料失败';
  } finally {
    pendingAction.value = null;
  }
}

async function toggleStatus() {
  if (!user.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = 'toggle-status';

  try {
    await changeUserStatus({
      userId: user.value.id,
      nextStatus: user.value.status === 'active' ? 'disabled' : 'active',
    });
    await refreshUserDetailSilently();
    feedback.value = `用户状态已切换为 ${user.value?.status ?? '-'}`;
    activeDialog.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '切换用户状态失败';
  } finally {
    pendingAction.value = null;
  }
}

async function handleResetPasskey() {
  if (!user.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = 'reset-passkey';

  try {
    await resetUserPasskey(user.value.id);
    await refreshUserDetailSilently();
    feedback.value = 'passkey 已重置，并已同步刷新该用户的 XBT 状态。';
    activeDialog.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置 passkey 失败';
  } finally {
    pendingAction.value = null;
  }
}

async function handleRunUserSync() {
  if (!user.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = 'sync-user';

  try {
    await runTrackerSyncForUser(user.value.id);
    await refreshUserDetailSilently();
    feedback.value = '已手动触发该用户的 XBT 同步。';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '手动同步用户到 XBT 失败';
  } finally {
    pendingAction.value = null;
  }
}

watch(() => route.params.id, loadUserDetail, { immediate: true });
</script>

<template>
  <AppLoading v-if="state === 'loading'" />
  <AppNotFound v-else-if="state === 'not-found' || !user" />
  <AppError v-else-if="state === 'error'" title="用户详情加载失败" :description="errorMessage">
    <template #actions>
      <UiButton variant="primary" @click="loadUserDetail">重试</UiButton>
    </template>
  </AppError>
  <template v-else>
    <AppPageHeader :title="user.displayName" description="用户详情页已接入资料编辑、单用户 XBT 同步与最近同步日志。">
      <template #actions>
        <UiButton variant="ghost" @click="loadUserDetail">刷新详情</UiButton>
      </template>
    </AppPageHeader>

    <AppAlert v-if="feedback" variant="success" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

    <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <div class="space-y-6">
        <AppCard title="基础信息" description="用户名、最近登录和发布数保持只读，显示名、邮箱与角色可直接修改。">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <dt class="text-sm text-slate-500">用户名</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ user.username }}</dd>
            </div>
            <div>
              <dt class="text-sm text-slate-500">状态</dt>
              <dd class="mt-1"><AppStatusBadge type="user-status" :value="user.status" /></dd>
            </div>
            <div>
              <dt class="text-sm text-slate-500">最近登录</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ formatDateTime(user.lastLoginAt) }}</dd>
            </div>
            <div>
              <dt class="text-sm text-slate-500">已发布资源</dt>
              <dd class="mt-1 font-medium text-slate-900">{{ user.createdReleaseCount }}</dd>
            </div>
          </div>

          <div class="mt-6 grid gap-4">
            <div>
              <label class="app-field-label">显示名</label>
              <UiInput v-model="form.displayName" placeholder="例如：资源整理组" />
            </div>
            <div>
              <label class="app-field-label">邮箱</label>
              <UiInput v-model="form.email" placeholder="例如：member@subtitle.local" />
            </div>
            <div>
              <label class="app-field-label">角色</label>
              <UiSelect
                v-model="form.role"
                :options="[
                  { label: '普通用户', value: 'user' },
                  { label: '上传者', value: 'uploader' },
                  { label: '管理员', value: 'admin' },
                ]"
              />
            </div>
          </div>

          <template #footer>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <span class="text-sm text-slate-500">
                本页会在仅改动部分字段时走 `PATCH`，全部字段改动时走 `PUT`。
              </span>
              <UiButton
                variant="primary"
                :disabled="pendingAction !== null || !canSaveProfile"
                @click="handleSaveProfile"
              >
                {{ pendingAction === 'save-profile' ? '保存中...' : '保存用户资料' }}
              </UiButton>
            </div>
          </template>
        </AppCard>
      </div>

      <div class="space-y-6">
        <AppCard title="passkey">
          <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {{ user.passkey }}
          </p>
        </AppCard>

        <AppCard title="XBT 状态" description="这里接入了单用户同步详情接口，可查看镜像状态和最近日志。">
          <div class="space-y-4">
            <div>
              <p class="mb-2 text-sm text-slate-500">最近同步</p>
              <div v-if="currentTrackerSync" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between gap-3">
                  <AppStatusBadge type="sync-status" :value="currentTrackerSync.status" />
                  <span class="text-xs text-slate-500">{{ formatDateTime(currentTrackerSync.updatedAt) }}</span>
                </div>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ currentTrackerSync.message }}</p>
              </div>
              <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                暂无同步记录。
              </p>
            </div>

            <div>
              <div class="mb-2 flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">XBT 镜像状态</p>
                <AppStatusBadge
                  v-if="currentXbtUser"
                  type="xbt-user-state"
                  :value="currentXbtUser.state"
                />
              </div>
              <div v-if="currentXbtUser" class="grid gap-3 sm:grid-cols-2">
                <div
                  v-for="item in trackerFacts"
                  :key="item.label"
                  class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <p class="text-xs text-slate-500">{{ item.label }}</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">{{ item.value }}</p>
                </div>
              </div>
              <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                当前没有可展示的 XBT 镜像状态。
              </p>
            </div>

            <div>
              <p class="mb-2 text-sm text-slate-500">最近同步日志</p>
              <UiTable v-if="recentLogs.length">
                <thead>
                  <tr>
                    <th>状态</th>
                    <th>说明</th>
                    <th>时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in recentLogs" :key="item.id">
                    <td><AppStatusBadge type="sync-status" :value="item.status" /></td>
                    <td>{{ item.message }}</td>
                    <td class="whitespace-nowrap text-slate-500">{{ formatDateTime(item.updatedAt) }}</td>
                  </tr>
                </tbody>
              </UiTable>
              <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                还没有单用户同步日志。
              </p>
            </div>
          </div>
        </AppCard>

        <AppCard title="管理动作" description="状态切换、passkey 重置和单用户同步都会即时触发对应联动。">
          <div class="flex flex-wrap gap-2">
            <UiButton
              variant="secondary"
              :disabled="pendingAction !== null"
              @click="handleRunUserSync"
            >
              {{ pendingAction === 'sync-user' ? '同步中...' : '手动同步到 XBT' }}
            </UiButton>
            <UiButton
              :variant="user.status === 'active' ? 'danger' : 'primary'"
              :disabled="pendingAction !== null"
              @click="activeDialog = 'toggle-status'"
            >
              {{ user.status === 'active' ? '禁用用户' : '启用用户' }}
            </UiButton>
            <UiButton
              variant="secondary"
              :disabled="pendingAction !== null"
              @click="activeDialog = 'reset-passkey'"
            >
              重置 passkey
            </UiButton>
          </div>
        </AppCard>
      </div>
    </div>

    <AppConfirmDialog
      :open="activeDialog === 'toggle-status'"
      :title="user.status === 'active' ? '确认禁用该用户' : '确认启用该用户'"
      :description="statusActionMeta.description"
      :confirm-label="statusActionMeta.confirmLabel"
      :tone="statusActionMeta.tone"
      :pending="pendingAction === 'toggle-status'"
      @close="activeDialog = null"
      @confirm="toggleStatus"
    >
      <p>管理员动作会立即写入用户状态，并影响前台权限、RSS 和后续 XBT 同步。</p>
    </AppConfirmDialog>

    <AppConfirmDialog
      :open="activeDialog === 'reset-passkey'"
      title="确认重置 passkey"
      description="旧 passkey 会立刻失效，用户需要更新下载器或 RSS 客户端中的认证信息。"
      confirm-label="确认重置"
      tone="warning"
      :pending="pendingAction === 'reset-passkey'"
      @close="activeDialog = null"
      @confirm="handleResetPasskey"
    >
      <p>这个操作适合泄露排查或凭据轮换场景，完成后建议同步通知对应成员。</p>
    </AppConfirmDialog>
  </template>
</template>
