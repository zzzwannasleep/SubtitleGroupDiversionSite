import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { CurrentUser, LoginPayload, RegisterPayload } from '@/types/auth';
import * as authService from '@/services/auth';
import { useThemeStore } from './theme';

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<CurrentUser | null>(null);
  const isBootstrapped = ref(false);
  const isLoading = ref(false);
  const errorMessage = ref('');
  let bootstrapPromise: Promise<void> | null = null;

  const isAuthenticated = computed(() => !!currentUser.value);
  const role = computed(() => currentUser.value?.role ?? null);

  async function syncCurrentUser(user: CurrentUser | null) {
    currentUser.value = user;
    const themeStore = useThemeStore();

    if (user) {
      await themeStore.loadTheme();
      return;
    }

    themeStore.resetTheme();
  }

  async function bootstrap() {
    if (isBootstrapped.value) return;
    if (bootstrapPromise) return bootstrapPromise;

    isLoading.value = true;
    errorMessage.value = '';

    bootstrapPromise = (async () => {
      try {
        await syncCurrentUser(await authService.fetchMe());
      } catch (error) {
        await syncCurrentUser(null);
        errorMessage.value = error instanceof Error ? error.message : '登录状态初始化失败，请稍后重试。';
        console.error('Auth bootstrap failed:', error);
      } finally {
        isLoading.value = false;
        isBootstrapped.value = true;
        bootstrapPromise = null;
      }
    })();

    return bootstrapPromise;
  }

  async function fetchMe() {
    await syncCurrentUser(await authService.fetchMe());
    return currentUser.value;
  }

  async function login(payload: LoginPayload) {
    errorMessage.value = '';
    isLoading.value = true;

    try {
      currentUser.value = await authService.login(payload);
      await useThemeStore().loadTheme();
      return currentUser.value;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '登录失败';
      throw error;
    } finally {
      isLoading.value = false;
      isBootstrapped.value = true;
    }
  }

  async function register(payload: RegisterPayload) {
    errorMessage.value = '';
    isLoading.value = true;

    try {
      currentUser.value = await authService.register(payload);
      await useThemeStore().loadTheme();
      return currentUser.value;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '注册失败';
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
      useThemeStore().resetTheme();
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
    register,
    logout,
    resetPasskey,
    changePassword,
  };
});
