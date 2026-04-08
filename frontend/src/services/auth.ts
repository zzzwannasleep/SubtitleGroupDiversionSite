import type { CurrentUser, LoginPayload } from '@/types/auth';
import { apiRequest, isApiError } from './api';
import { getUserById, getUserByUsername, resetPasskey as resetMockPasskey } from './mock-data';
import { mockResolve, useMockApi } from './runtime';

const SESSION_KEY = 'sgds:session-user-id';

function getStoredSessionId(): number | null {
  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function fetchMe(): Promise<CurrentUser | null> {
  if (useMockApi()) {
    return mockResolve(() => {
      const sessionId = getStoredSessionId();
      if (!sessionId) return null;
      return getUserById(sessionId) ?? null;
    });
  }

  try {
    return await apiRequest<CurrentUser>('/api/auth/me/');
  } catch (error) {
    if (isApiError(error) && (error.status === 401 || error.status === 403 || error.status === 404)) {
      return null;
    }
    throw error;
  }
}

export async function login(payload: LoginPayload): Promise<CurrentUser> {
  if (useMockApi()) {
    return mockResolve(() => {
      const user = getUserByUsername(payload.username.trim());

      if (!payload.password.trim()) {
        throw new Error('请输入密码');
      }

      if (!user) {
        throw new Error('用户不存在，可使用 admin、uploader、user 体验不同角色');
      }

      if (user.status === 'disabled') {
        throw new Error('该账号已被禁用，请联系管理员处理');
      }

      window.localStorage.setItem(SESSION_KEY, String(user.id));
      return user;
    });
  }

  return apiRequest<CurrentUser>('/api/auth/login/', {
    method: 'POST',
    body: {
      username: payload.username.trim(),
      password: payload.password,
    },
  });
}

export async function logout(): Promise<void> {
  if (useMockApi()) {
    return mockResolve(() => {
      window.localStorage.removeItem(SESSION_KEY);
    });
  }

  await apiRequest('/api/auth/logout/', { method: 'POST' });
}

export async function resetPasskey(_userId?: number): Promise<CurrentUser> {
  if (useMockApi()) {
    return mockResolve(() => {
      const sessionId = getStoredSessionId();
      if (!sessionId) {
        throw new Error('当前未登录');
      }

      return resetMockPasskey(sessionId);
    });
  }

  return apiRequest<CurrentUser>('/api/me/reset-passkey/', { method: 'POST' });
}

export async function changePassword(currentPassword: string, nextPassword: string): Promise<void> {
  if (useMockApi()) {
    return mockResolve(() => {
      if (!currentPassword.trim() || !nextPassword.trim()) {
        throw new Error('请输入完整密码');
      }
    });
  }

  await apiRequest('/api/auth/change-password/', {
    method: 'POST',
    body: {
      currentPassword,
      nextPassword,
    },
  });
}
