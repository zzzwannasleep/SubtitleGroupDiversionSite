import { storeToRefs } from 'pinia';
import { useAuthStore } from '@/stores/auth';

export function useAuth() {
  const authStore = useAuthStore();
  const refs = storeToRefs(authStore);

  return {
    ...refs,
    ...authStore,
  };
}

