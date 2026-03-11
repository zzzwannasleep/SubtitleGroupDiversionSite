<script setup lang="ts">
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

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
  <div class="flex min-h-screen items-center justify-center bg-slate-100 px-4">
    <div class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">PT Platform</p>
      <h1 class="mt-3 text-3xl font-semibold text-slate-900">Create account</h1>
      <p class="mt-2 text-sm text-slate-500">The first registered user becomes the initial admin.</p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Username</span>
          <input v-model="form.username" class="w-full rounded-xl border border-slate-300 px-4 py-3" required />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Email</span>
          <input v-model="form.email" type="email" class="w-full rounded-xl border border-slate-300 px-4 py-3" required />
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

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">Confirm password</span>
          <input
            v-model="form.confirmPassword"
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
          {{ authStore.loading ? "Creating..." : "Create account" }}
        </button>
      </form>

      <p class="mt-6 text-sm text-slate-500">
        Already registered?
        <RouterLink to="/login" class="font-semibold text-blue-700 hover:text-blue-800">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>

