<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import AppStatusBadge from '@/components/app/AppStatusBadge.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { createUser, listUsers } from '@/services/admin';
import type { AdminUser } from '@/types/admin';

const users = ref<AdminUser[]>([]);
const search = ref('');
const feedback = ref('');
const form = reactive({
  username: '',
  displayName: '',
  email: '',
  role: 'user',
});

async function loadUsers() {
  users.value = await listUsers(search.value);
}

async function handleCreateUser() {
  const user = await createUser({
    username: form.username,
    displayName: form.displayName,
    email: form.email,
    role: form.role as 'admin' | 'uploader' | 'user',
  });
  feedback.value = `已创建用户：${user.username}`;
  form.username = '';
  form.displayName = '';
  form.email = '';
  form.role = 'user';
  await loadUsers();
}

onMounted(loadUsers);
</script>

<template>
  <AppPageHeader title="用户管理" description="后台列表页采用搜索工具条 + 表格卡片模式。">
    <template #actions>
      <UiButton to="/admin/settings" variant="secondary">系统设置</UiButton>
    </template>
  </AppPageHeader>

  <div v-if="feedback" class="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
    {{ feedback }}
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="用户列表" description="支持搜索、状态显示和详情入口。">
      <div class="mb-4 flex gap-3">
        <UiInput v-model="search" placeholder="搜索用户名 / 显示名 / 邮箱 / 角色" />
        <UiButton variant="primary" @click="loadUsers">搜索</UiButton>
      </div>
      <UiTable>
        <thead>
          <tr>
            <th>用户</th>
            <th>角色</th>
            <th>状态</th>
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

    <AppCard title="创建用户" description="延续“管理员建号”的站点模式。">
      <div class="space-y-4">
        <div>
          <label class="app-field-label">用户名</label>
          <UiInput v-model="form.username" />
        </div>
        <div>
          <label class="app-field-label">显示名</label>
          <UiInput v-model="form.displayName" />
        </div>
        <div>
          <label class="app-field-label">邮箱</label>
          <UiInput v-model="form.email" />
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
        <UiButton variant="primary" @click="handleCreateUser">创建用户</UiButton>
      </template>
    </AppCard>
  </div>
</template>

