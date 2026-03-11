<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AuthShell from "@/components/AuthShell.vue";
import { useAuthStore } from "@/stores/auth";


const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const form = reactive({
  username: "",
  password: "",
});
const errorMessage = ref("");

async function submit(): Promise<void> {
  errorMessage.value = "";
  try {
    await authStore.loginAndFetchProfile(form);
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/torrents";
    await router.push(redirect);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Login failed";
  }
}
</script>

<template>
  <AuthShell
    form-eyebrow="Secure sign in"
    form-title="Connect to the tracker portal"
    form-description="Use your account identity to access torrent browsing, RSS feeds, and tracker-backed personal stats."
    alternate-prompt="Need an account?"
    alternate-label="Create one"
    alternate-to="/register"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="auth-field-label">Username or email</span>
        <input v-model="form.username" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">Password</span>
        <input v-model="form.password" type="password" class="auth-input mt-3" required />
      </label>

      <p v-if="errorMessage" class="auth-error-banner">{{ errorMessage }}</p>

      <button type="submit" class="auth-primary-btn" :disabled="authStore.loading">
        {{ authStore.loading ? "Signing in..." : "Sign in" }}
      </button>
    </form>
  </AuthShell>
</template>
