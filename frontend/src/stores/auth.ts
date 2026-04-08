import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { CurrentUser, LoginPayload } from '@/types/auth';
import * as authService from '@/services/auth';

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<CurrentUser | null>(null);
  const isBootstrapped = ref(false);
  const isLoading = ref(false);
  const errorMessage = ref('');

  const isAuthenticated = computed(() => !!currentUser.value);
  const role = computed(() => currentUser.value?.role ?? null);

  async function bootstrap() {
    if (isBootstrapped.value) return;
    isLoading.value = true;
    errorMessage.value = '';

    try {
      currentUser.value = await authService.fetchMe();
    } finally {
      isLoading.value = false;
      isBootstrapped.value = true;
    }
  }

  async function fetchMe() {
    currentUser.value = await authService.fetchMe();
    return currentUser.value;
  }

  async function login(payload: LoginPayload) {
    errorMessage.value = '';
    isLoading.value = true;

    try {
      currentUser.value = await authService.login(payload);
      return currentUser.value;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '登录失败';
      throw error;
    } finally {
      isLoading.value = false;
      isBootstrapped.value = true;
    }
  }

  async function logout() {
    isLoading.value = true;

    try {
      await authService.logout();
      currentUser.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  async function resetPasskey() {
    if (!currentUser.value) {
      throw new Error('当前未登录');
    }

    currentUser.value = await authService.resetPasskey(currentUser.value.id);
    return currentUser.value;
  }

  async function changePassword(currentPassword: string, nextPassword: string) {
    if (!currentUser.value) {
      throw new Error('当前未登录');
    }

    await authService.changePassword(currentPassword, nextPassword);
  }

  return {
    currentUser,
    isAuthenticated,
    isBootstrapped,
    isLoading,
    errorMessage,
    role,
    bootstrap,
    fetchMe,
    login,
    logout,
    resetPasskey,
    changePassword,
  };
});
