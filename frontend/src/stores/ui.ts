import { ref } from 'vue';
import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', () => {
  const isMobileMenuOpen = ref(false);
  const isAdminSidebarOpen = ref(false);
  const isGlobalLoading = ref(false);

  const toggleMobileMenu = () => {
    isMobileMenuOpen.value = !isMobileMenuOpen.value;
  };

  const closeMobileMenu = () => {
    isMobileMenuOpen.value = false;
  };

  const toggleAdminSidebar = () => {
    isAdminSidebarOpen.value = !isAdminSidebarOpen.value;
  };

  const closeAdminSidebar = () => {
    isAdminSidebarOpen.value = false;
  };

  return {
    isMobileMenuOpen,
    isAdminSidebarOpen,
    isGlobalLoading,
    toggleMobileMenu,
    closeMobileMenu,
    toggleAdminSidebar,
    closeAdminSidebar,
  };
});

