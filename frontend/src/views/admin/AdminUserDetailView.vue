<script setup lang="ts">
import { computed, ref, watch } from 'vue';
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
import { changeUserStatus, getUserDetail, resetUserPasskey } from '@/services/admin';
import type { AdminUser } from '@/types/admin';
import { formatBytes, formatDateTime } from '@/utils/format';

const route = useRoute();
const state = ref<'loading' | 'ready' | 'not-found' | 'error'>('loading');
const user = ref<AdminUser | null>(null);
const feedback = ref('');
const errorMessage = ref('');
const pendingAction = ref<'toggle-status' | 'reset-passkey' | null>(null);
const activeDialog = ref<'toggle-status' | 'reset-passkey' | null>(null);

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
      ? `禁用后，用户 ${user.value.displayName} 将无法继续登录和下载。`
      : `启用后，用户 ${user.value.displayName} 将恢复正常访问权限。`,
    tone: isDisabling ? ('danger' as const) : ('primary' as const),
  };
});

const trackerFacts = computed(() => {
  if (!user.value?.xbtUser) return [];

  return [
    {
      label: '可下载',
      value: user.value.xbtUser.canLeech === null ? '-' : user.value.xbtUser.canLeech ? '是' : '否',
    },
    {
      label: '已下载',
      value: user.value.xbtUser.downloaded === null ? '-' : formatBytes(user.value.xbtUser.downloaded),
    },
    {
      label: '已上传',
      value: user.value.xbtUser.uploaded === null ? '-' : formatBytes(user.value.xbtUser.uploaded),
    },
    {
      label: '完成数',
      value: user.value.xbtUser.completed === null ? '-' : `${user.value.xbtUser.completed}`,
    },
  ];
});

async function loadUserDetail() {
  state.value = 'loading';
  user.value = null;
  feedback.value = '';
  errorMessage.value = '';

  try {
    user.value = await getUserDetail(Number(route.params.id));
    state.value = user.value ? 'ready' : 'not-found';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '用户详情加载失败';
    state.value = 'error';
  }
}

async function refreshUserDetailSilently() {
  const nextUser = await getUserDetail(Number(route.params.id));
  if (nextUser) {
    user.value = nextUser;
    state.value = 'ready';
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
    feedback.value = `用户状态已切换为 ${user.value.status}`;
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
    feedback.value = 'passkey 已重置，并应同步到 XBT。';
    activeDialog.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置 passkey 失败';
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
    <AppPageHeader :title="user.displayName" description="用户详情页聚合角色、状态、passkey 与运维操作。" />
    <AppAlert v-if="feedback" variant="info" :title="feedback" />
    <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />
    <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <AppCard title="基础信息">
        <dl class="grid gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm text-slate-500">用户名</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ user.username }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">邮箱</dt>
            <dd class="mt-1 font-medium text-slate-900">{{ user.email }}</dd>
          </div>
          <div>
            <dt class="text-sm text-slate-500">角色</dt>
            <dd class="mt-1"><AppStatusBadge type="role" :value="user.role" /></dd>
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
        </dl>
      </AppCard>

      <div class="space-y-6">
        <AppCard title="passkey">
          <p class="break-all rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {{ user.passkey }}
          </p>
        </AppCard>
        <AppCard title="XBT 状态" description="这里展示用户在 Tracker 侧的最近同步结果与镜像状态。">
          <div class="space-y-4">
            <div>
              <p class="mb-2 text-sm text-slate-500">最近同步</p>
              <div v-if="user.trackerSync" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex items-center justify-between gap-3">
                  <AppStatusBadge type="sync-status" :value="user.trackerSync.status" />
                  <span class="text-xs text-slate-500">{{ formatDateTime(user.trackerSync.updatedAt) }}</span>
                </div>
                <p class="mt-3 text-sm leading-6 text-slate-600">{{ user.trackerSync.message }}</p>
              </div>
              <p v-else class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                暂无同步记录。
              </p>
            </div>

            <div>
              <div class="mb-2 flex items-center justify-between gap-3">
                <p class="text-sm text-slate-500">XBT 镜像状态</p>
                <AppStatusBadge
                  v-if="user.xbtUser"
                  type="xbt-user-state"
                  :value="user.xbtUser.state"
                />
              </div>
              <div v-if="user.xbtUser" class="grid gap-3 sm:grid-cols-2">
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
          </div>
        </AppCard>
        <AppCard title="管理动作" description="危险操作统一使用强调按钮或二次确认。">
          <div class="flex flex-wrap gap-2">
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
      <p>管理员动作会立即写入用户状态，并影响前台权限与后续 XBT 同步。</p>
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
