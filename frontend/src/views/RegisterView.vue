<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import AuthShell from "@/components/AuthShell.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";


const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();

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
    errorMessage.value = t("auth.register.passwordMismatch");
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
    errorMessage.value = error instanceof Error ? error.message : t("auth.register.errorFallback");
  }
}
</script>

<template>
  <AuthShell
    form-eyebrow=""
    :form-title="t('auth.register.title')"
    form-description=""
    :alternate-prompt="t('auth.register.altPrompt')"
    :alternate-label="t('auth.register.altLabel')"
    alternate-to="/login"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="auth-field-label">{{ t("auth.register.username") }}</span>
        <input v-model="form.username" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">{{ t("auth.register.email") }}</span>
        <input v-model="form.email" type="email" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">{{ t("auth.register.password") }}</span>
        <input v-model="form.password" type="password" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">{{ t("auth.register.confirmPassword") }}</span>
        <input v-model="form.confirmPassword" type="password" class="auth-input mt-3" required />
      </label>

      <p v-if="errorMessage" class="auth-error-banner">{{ errorMessage }}</p>

      <button type="submit" class="auth-primary-btn" :disabled="authStore.loading">
        {{ authStore.loading ? t("auth.register.submitting") : t("auth.register.submit") }}
      </button>
    </form>
  </AuthShell>
</template>
