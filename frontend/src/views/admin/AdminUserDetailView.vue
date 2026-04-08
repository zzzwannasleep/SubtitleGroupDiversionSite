<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
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
import { formatDateTime } from '@/utils/format';

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

async function loadUserDetail() {
  state.value = 'loading';
  errorMessage.value = '';

  try {
    user.value = await getUserDetail(Number(route.params.id));
    state.value = user.value ? 'ready' : 'not-found';
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '用户详情加载失败';
    state.value = 'error';
  }
}

async function toggleStatus() {
  if (!user.value) return;

  feedback.value = '';
  errorMessage.value = '';
  pendingAction.value = 'toggle-status';

  try {
    user.value = await changeUserStatus({
      userId: user.value.id,
      nextStatus: user.value.status === 'active' ? 'disabled' : 'active',
    });
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
    user.value = await resetUserPasskey(user.value.id);
    feedback.value = 'passkey 已重置，并应同步到 XBT。';
    activeDialog.value = null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置 passkey 失败';
  } finally {
    pendingAction.value = null;
  }
}

onMounted(loadUserDetail);
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
