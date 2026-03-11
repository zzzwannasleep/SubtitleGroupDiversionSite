<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import AuthShell from "@/components/AuthShell.vue";
import { useAuthStore } from "@/stores/auth";


const authStore = useAuthStore();
const router = useRouter();

const form = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});
const errorMessage = ref("");

async function submit(): Promise<void> {
  errorMessage.value = "";

  if (form.password !== form.confirmPassword) {
    errorMessage.value = "Passwords do not match";
    return;
  }

  try {
    await authStore.registerAndLogin({
      username: form.username,
      email: form.email,
      password: form.password,
    });
    await router.push("/torrents");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Registration failed";
  }
}
</script>

<template>
  <AuthShell
    form-eyebrow="Provision account"
    form-title="Create a platform identity"
    form-description="Provision a local PT account with unique tracker credentials, RSS access, and role-based permissions."
    alternate-prompt="Already registered?"
    alternate-label="Sign in"
    alternate-to="/login"
    note="The first registered user becomes the initial admin."
  >
    <form class="space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="auth-field-label">Username</span>
        <input v-model="form.username" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">Email</span>
        <input v-model="form.email" type="email" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">Password</span>
        <input v-model="form.password" type="password" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">Confirm password</span>
        <input v-model="form.confirmPassword" type="password" class="auth-input mt-3" required />
      </label>

      <p v-if="errorMessage" class="auth-error-banner">{{ errorMessage }}</p>

      <button type="submit" class="auth-primary-btn" :disabled="authStore.loading">
        {{ authStore.loading ? "Creating..." : "Create account" }}
      </button>
    </form>
  </AuthShell>
</template>
