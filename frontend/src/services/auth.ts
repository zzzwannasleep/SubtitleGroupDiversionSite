import type { CurrentUser, LoginPayload } from '@/types/auth';
import { apiRequest, isApiError } from './api';

export async function fetchMe(): Promise<CurrentUser | null> {
  try {
    return await apiRequest<CurrentUser>('/api/auth/me/');
  } catch (error) {
    if (isApiError(error) && (error.status === 401 || error.status === 403)) {
      return null;
    }
    throw error;
  }
}

export async function login(payload: LoginPayload): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/auth/login/', {
    method: 'POST',
    body: {
      username: payload.username.trim(),
      password: payload.password,
    },
  });
}

export async function logout(): Promise<void> {
  await apiRequest('/api/auth/logout/', { method: 'POST' });
}

export async function resetPasskey(_userId?: number): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/api/me/reset-passkey/', { method: 'POST' });
}

export async function changePassword(currentPassword: string, nextPassword: string): Promise<void> {
  await apiRequest('/api/auth/change-password/', {
    method: 'POST',
    body: {
      currentPassword,
      nextPassword,
    },
  });
}
