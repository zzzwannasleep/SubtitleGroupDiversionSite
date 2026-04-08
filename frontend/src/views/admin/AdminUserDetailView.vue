<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppNotFound from '@/components/app/AppNotFound.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import { changeUserStatus, getUserDetail, resetUserPasskey } from '@/services/admin';
import type { AdminUser } from '@/types/admin';
import { formatDateTime } from '@/utils/format';

const route = useRoute();
const loading = ref(true);
const user = ref<AdminUser | null>(null);
const feedback = ref('');

onMounted(async () => {
  user.value = await getUserDetail(Number(route.params.id));
  loading.value = false;
});

async function toggleStatus() {
  if (!user.value) return;
  user.value = await changeUserStatus({
    userId: user.value.id,
    nextStatus: user.value.status === 'active' ? 'disabled' : 'active',
  });
  feedback.value = `用户状态已切换为 ${user.value.status}`;
}

async function handleResetPasskey() {
  if (!user.value) return;
  user.value = await resetUserPasskey(user.value.id);
  feedback.value = 'passkey 已重置，并应同步到 XBT。';
}
</script>

<template>
  <AppLoading v-if="loading" />
  <AppNotFound v-else-if="!user" />
  <template v-else>
    <AppPageHeader :title="user.displayName" description="用户详情页聚合角色、状态、passkey 与运维操作。" />
    <AppAlert v-if="feedback" variant="info" :title="feedback" />
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
            <UiButton :variant="user.status === 'active' ? 'danger' : 'primary'" @click="toggleStatus">
              {{ user.status === 'active' ? '禁用用户' : '启用用户' }}
            </UiButton>
            <UiButton variant="secondary" @click="handleResetPasskey">重置 passkey</UiButton>
          </div>
        </AppCard>
      </div>
    </div>
  </template>
</template>
