<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AuthShell from "@/components/AuthShell.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";


const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n();

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
    errorMessage.value = error instanceof Error ? error.message : t("auth.login.errorFallback");
  }
}
</script>

<template>
  <AuthShell
    form-eyebrow=""
    :form-title="t('auth.login.title')"
    form-description=""
    :alternate-prompt="t('auth.login.altPrompt')"
    :alternate-label="t('auth.login.altLabel')"
    alternate-to="/register"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <label class="block">
        <span class="auth-field-label">{{ t("auth.login.usernameOrEmail") }}</span>
        <input v-model="form.username" class="auth-input mt-3" required />
      </label>

      <label class="block">
        <span class="auth-field-label">{{ t("auth.login.password") }}</span>
        <input v-model="form.password" type="password" class="auth-input mt-3" required />
      </label>

      <p v-if="errorMessage" class="auth-error-banner">{{ errorMessage }}</p>

      <button type="submit" class="auth-primary-btn" :disabled="authStore.loading">
        {{ authStore.loading ? t("auth.login.submitting") : t("auth.login.submit") }}
      </button>
    </form>
  </AuthShell>
</template>
