<script setup lang="ts">
import { reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppCard from '@/components/app/AppCard.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const form = reactive({
  username: '',
  password: '',
});

async function handleSubmit() {
  try {
    await authStore.login(form);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    await router.push(redirect);
  } catch {
    // 错误信息由 store 统一维护并展示
  }
}
</script>

<template>
  <AppCard title="登录系统" description="使用管理员预先创建的账号进入站点。">
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <div>
        <label class="app-field-label">用户名</label>
        <UiInput v-model="form.username" placeholder="请输入用户名" />
      </div>
      <div>
        <label class="app-field-label">密码</label>
        <UiInput v-model="form.password" type="password" placeholder="请输入密码" />
        <p class="app-field-help">登录成功后会自动跳回你刚才尝试访问的页面。</p>
      </div>
      <div v-if="authStore.errorMessage" class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
        {{ authStore.errorMessage }}
      </div>
      <UiButton type="submit" block variant="primary" :disabled="authStore.isLoading">
        {{ authStore.isLoading ? '登录中...' : '登录' }}
      </UiButton>
    </form>
  </AppCard>
</template>
