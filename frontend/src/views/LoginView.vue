<script setup lang="ts">
import { reactive, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

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
  <div class="flex min-h-screen items-center justify-center bg-slate-100 px-4">
    <div class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">PT Platform</p>
      <h1 class="mt-3 text-3xl font-semibold text-slate-900">Sign in</h1>
      <p class="mt-2 text-sm text-slate-500">Use your username or email to access the site.</p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Username / Email</span>
          <input v-model="form.username" class="w-full rounded-xl border border-slate-300 px-4 py-3" required />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Password</span>
          <input
            v-model="form.password"
            type="password"
            class="w-full rounded-xl border border-slate-300 px-4 py-3"
            required
          />
        </label>

        <p v-if="errorMessage" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</p>

        <button
          type="submit"
          class="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          :disabled="authStore.loading"
        >
          {{ authStore.loading ? "Signing in..." : "Sign in" }}
        </button>
      </form>

      <p class="mt-6 text-sm text-slate-500">
        Need an account?
        <RouterLink to="/register" class="font-semibold text-blue-700 hover:text-blue-800">Create one</RouterLink>
      </p>
    </div>
  </div>
</template>

