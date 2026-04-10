<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { createUser, listUsers } from '@/services/admin';
import type { AdminUser } from '@/types/admin';

const users = ref<AdminUser[]>([]);
const loading = ref(true);
const creating = ref(false);
const search = ref('');
const roleFilter = ref('');
const statusFilter = ref('');
const feedback = ref('');
const errorMessage = ref('');
const form = reactive({
  username: '',
  displayName: '',
  email: '',
  password: '',
  role: 'user',
});

const summaryCards = computed(() => [
  {
    label: '结果总数',
    value: users.value.length,
    hint: '当前筛选条件下返回的用户数',
  },
  {
    label: '正常账号',
    value: users.value.filter((item) => item.status === 'active').length,
    hint: '可正常登录和下载',
  },
  {
    label: '禁用账号',
    value: users.value.filter((item) => item.status === 'disabled').length,
    hint: '需要管理员进一步处理',
  },
  {
    label: '上传者',
    value: users.value.filter((item) => item.role === 'uploader').length,
    hint: '拥有前台上传与我的发布入口',
  },
]);

const canCreate = computed(
  () => Boolean(form.username.trim() && form.displayName.trim() && form.email.trim() && form.role),
);

async function loadUsers() {
  loading.value = true;
  errorMessage.value = '';

  try {
    users.value = await listUsers({
      keyword: search.value,
      role: roleFilter.value ? (roleFilter.value as 'admin' | 'uploader' | 'user') : undefined,
      status: statusFilter.value ? (statusFilter.value as 'active' | 'disabled') : undefined,
    });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载用户列表失败';
  } finally {
    loading.value = false;
  }
}

function resetCreateForm() {
  form.username = '';
  form.displayName = '';
  form.email = '';
  form.password = '';
  form.role = 'user';
}

async function resetFilters() {
  search.value = '';
  roleFilter.value = '';
  statusFilter.value = '';
  await loadUsers();
}

async function handleCreateUser() {
  if (!canCreate.value) {
    feedback.value = '';
    errorMessage.value = '请完整填写用户名、显示名、邮箱和角色。';
    return;
  }

  feedback.value = '';
  errorMessage.value = '';
  creating.value = true;

  try {
    const usesCustomPassword = Boolean(form.password);
    const user = await createUser({
      username: form.username,
      displayName: form.displayName,
      email: form.email,
      password: form.password || undefined,
      role: form.role as 'admin' | 'uploader' | 'user',
    });
    feedback.value = user.initialPassword
      ? `已创建用户 ${user.username}，初始密码：${user.initialPassword}`
      : usesCustomPassword
        ? `已创建用户 ${user.username}，已使用自定义密码。`
        : `已创建用户：${user.username}`;
    resetCreateForm();
    await loadUsers();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建用户失败';
  } finally {
    creating.value = false;
  }
}

onMounted(loadUsers);
</script>

<template>
  <AppPageHeader
    title="用户管理"
    description="支持搜索、角色与状态筛选、建号和详情入口，保持后台管理路径直观。"
  >
    <template #actions>
      <UiButton to="/admin/settings" variant="secondary">系统设置</UiButton>
      <UiButton variant="ghost" @click="loadUsers">刷新列表</UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div
      v-for="item in summaryCards"
      :key="item.label"
      class="app-surface p-4"
    >
      <p class="text-sm text-slate-500">{{ item.label }}</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
      <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="用户列表" description="按账号、显示名、邮箱、角色和状态筛选，再进入详情页处理。">
      <div class="mb-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_180px_180px_auto]">
        <UiInput v-model="search" placeholder="搜索用户名 / 显示名 / 邮箱 / 角色" />
        <UiSelect
          v-model="roleFilter"
          :options="[
            { label: '管理员', value: 'admin' },
            { label: '上传者', value: 'uploader' },
            { label: '普通用户', value: 'user' },
          ]"
          placeholder="全部角色"
        />
        <UiSelect
          v-model="statusFilter"
          :options="[
            { label: '正常', value: 'active' },
            { label: '已禁用', value: 'disabled' },
          ]"
          placeholder="全部状态"
        />
        <UiButton variant="primary" :disabled="loading" @click="loadUsers">搜索</UiButton>
      </div>

      <div class="mb-4 flex flex-wrap items-center gap-2">
        <UiButton variant="ghost" size="sm" @click="resetFilters">清空筛选</UiButton>
        <span class="text-sm text-slate-500">当前结果 {{ users.length }} 条</span>
      </div>

      <AppLoading v-if="loading" />
      <AppEmpty v-else-if="!users.length" title="没有匹配的用户" description="请调整搜索词后重试。">
        <template #actions>
          <UiButton variant="secondary" @click="resetFilters">重置筛选</UiButton>
        </template>
      </AppEmpty>
      <UiTable v-else>
        <thead>
          <tr>
            <th>用户</th>
            <th>角色</th>
            <th>状态</th>
            <th>最近登录</th>
            <th>发布数</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <div class="space-y-1">
                <p class="font-medium text-slate-900">{{ user.displayName }}</p>
                <p class="text-xs text-slate-500">{{ user.username }} / {{ user.email }}</p>
              </div>
            </td>
            <td><AppStatusBadge type="role" :value="user.role" /></td>
            <td><AppStatusBadge type="user-status" :value="user.status" /></td>
            <td class="whitespace-nowrap text-slate-500">{{ user.lastLoginAt.slice(0, 16).replace('T', ' ') }}</td>
            <td>{{ user.createdReleaseCount }}</td>
            <td>
              <RouterLink :to="`/admin/users/${user.id}`" class="text-sm font-medium text-blue-700">
                查看详情
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </UiTable>
    </AppCard>

    <AppCard
      title="创建用户"
      description="管理员现在可以在建号时直接指定密码；若留空，系统会继续自动生成一次性初始密码。"
    >
      <div class="space-y-4">
        <div>
          <label class="app-field-label">用户名</label>
          <UiInput v-model="form.username" placeholder="例如：new_member" />
        </div>
        <div>
          <label class="app-field-label">显示名</label>
          <UiInput v-model="form.displayName" placeholder="例如：资源整理组" />
        </div>
        <div>
          <label class="app-field-label">邮箱</label>
          <UiInput v-model="form.email" placeholder="例如：member@subtitle.local" />
        </div>
        <div>
          <label class="app-field-label">初始密码</label>
          <UiInput v-model="form.password" type="password" placeholder="留空则自动生成；填写则按该密码创建" />
          <p class="mt-2 text-xs leading-6 text-slate-500">如果填写，会按你输入的密码直接建号；不填写则由系统生成一次性密码并回显。</p>
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

        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-600">
          管理员拥有完整后台权限，上传者拥有前台上传与“我的发布”入口，普通用户保留浏览、下载和 RSS 能力。
        </div>
      </div>
      <template #footer>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <UiButton variant="ghost" :disabled="creating" @click="resetCreateForm">清空表单</UiButton>
          <UiButton variant="primary" :disabled="creating || !canCreate" @click="handleCreateUser">
            {{ creating ? '创建中...' : '创建用户' }}
          </UiButton>
        </div>
      </template>
    </AppCard>
  </div>
</template>
