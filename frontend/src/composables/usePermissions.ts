import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from '@/stores/auth';
import { canManageAdmin, hasRole } from '@/utils/permissions';
import type { UserRole } from '@/types/auth';

export function usePermissions() {
  const authStore = useAuthStore();
  const { currentUser } = storeToRefs(authStore);

  const canAccess = (roles?: UserRole[]) => hasRole(currentUser.value, roles);

  return {
    currentUser,
    canAccess,
    isAdmin: computed(() => currentUser.value?.role === 'admin'),
    isUploader: computed(() => currentUser.value?.role === 'uploader' || currentUser.value?.role === 'admin'),
    canManageAdmin: computed(() => canManageAdmin(currentUser.value)),
  };
}

