<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
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
const feedback = ref('');
const errorMessage = ref('');
const form = reactive({
  username: '',
  displayName: '',
  email: '',
  role: 'user',
});

async function loadUsers() {
  loading.value = true;
  errorMessage.value = '';

  try {
    users.value = await listUsers(search.value);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载用户列表失败';
  } finally {
    loading.value = false;
  }
}

async function handleCreateUser() {
  feedback.value = '';
  errorMessage.value = '';
  creating.value = true;

  try {
    const user = await createUser({
      username: form.username,
      displayName: form.displayName,
      email: form.email,
      role: form.role as 'admin' | 'uploader' | 'user',
    });
    feedback.value = user.initialPassword
      ? `已创建用户 ${user.username}，初始密码：${user.initialPassword}`
      : `已创建用户：${user.username}`;
    form.username = '';
    form.displayName = '';
    form.email = '';
    form.role = 'user';
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
  <AppPageHeader title="用户管理" description="支持搜索、建号、状态查看和详情入口。">
    <template #actions>
      <UiButton to="/admin/settings" variant="secondary">系统设置</UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="用户列表" description="管理员可以按账号、显示名、邮箱和角色搜索。">
      <div class="mb-4 flex gap-3">
        <UiInput v-model="search" placeholder="搜索用户名 / 显示名 / 邮箱 / 角色" />
        <UiButton variant="primary" :disabled="loading" @click="loadUsers">搜索</UiButton>
      </div>
      <AppLoading v-if="loading" />
      <AppEmpty v-else-if="!users.length" title="没有匹配的用户" description="请调整搜索词后重试。" />
      <UiTable v-else>
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

    <AppCard title="创建用户" description="创建成功后会返回一次性的初始密码，便于管理员分发。">
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
        <UiButton variant="primary" :disabled="creating" @click="handleCreateUser">
          {{ creating ? '创建中...' : '创建用户' }}
        </UiButton>
      </template>
    </AppCard>
  </div>
</template>
