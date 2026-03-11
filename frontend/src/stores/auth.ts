import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { getCurrentUser, login, register, type LoginPayload, type RegisterPayload } from "@/api/auth";
import type { AuthUser } from "@/types";


const TOKEN_KEY = "pt-platform.token";


export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
  const user = ref<AuthUser | null>(null);
  const loading = ref(false);

  const isAuthenticated = computed(() => Boolean(token.value));

  function restoreSession(): void {
    token.value = localStorage.getItem(TOKEN_KEY);
  }

  function setToken(nextToken: string | null): void {
    token.value = nextToken;
    if (nextToken) {
      localStorage.setItem(TOKEN_KEY, nextToken);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  async function ensureUser(): Promise<AuthUser | null> {
    if (!token.value) {
      user.value = null;
      return null;
    }

    if (user.value) {
      return user.value;
    }

    loading.value = true;
    try {
      user.value = await getCurrentUser();
      return user.value;
    } catch {
      setToken(null);
      user.value = null;
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function loginAndFetchProfile(payload: LoginPayload): Promise<void> {
    loading.value = true;
    try {
      const response = await login(payload);
      setToken(response.access_token);
      user.value = await getCurrentUser();
    } finally {
      loading.value = false;
    }
  }

  async function registerAndLogin(payload: RegisterPayload): Promise<void> {
    await register(payload);
    await loginAndFetchProfile({ username: payload.username, password: payload.password });
  }

  function logout(): void {
    setToken(null);
    user.value = null;
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    restoreSession,
    ensureUser,
    loginAndFetchProfile,
    registerAndLogin,
    logout,
  };
});

