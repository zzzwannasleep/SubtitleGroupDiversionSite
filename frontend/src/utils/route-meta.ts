import 'vue-router';
import type { UserRole } from '@/types/auth';

declare module 'vue-router' {
  interface RouteMeta {
    title?: string;
    requiresAuth?: boolean;
    guestOnly?: boolean;
    roles?: UserRole[];
  }
}

export {};
