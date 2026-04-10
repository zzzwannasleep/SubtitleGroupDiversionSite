import type { CurrentUser, LoginPayload, RegisterPayload } from '@/types/auth';
import type { ApiTokenPayload } from '@/types/admin';
import { apiRequest, isApiError } from './api';
import {
  createUserRecord,
  getCurrentUserApiToken,
  getUserById,
  getUserByUsername,
  resetPasskey as resetMockPasskey,
  resetUserApiToken,
  siteSettings,
} from './mock-data';
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

export async function register(payload: RegisterPayload): Promise<CurrentUser> {
  if (useMockApi()) {
    return mockResolve(() => {
      if (!siteSettings.allowPublicRegistration) {
        throw new Error('当前站点未开放自由注册');
      }

      if (!payload.username.trim()) {
        throw new Error('请输入用户名');
      }

      if (!payload.displayName.trim()) {
        throw new Error('请输入显示名称');
      }

      if (!payload.email.trim()) {
        throw new Error('请输入邮箱地址');
      }

      if (!payload.password.trim()) {
        throw new Error('请输入密码');
      }

      if (payload.password !== payload.confirmPassword) {
        throw new Error('两次输入的密码不一致');
      }

      if (getUserByUsername(payload.username.trim())) {
        throw new Error('用户名已存在');
      }

      const user = createUserRecord({
        username: payload.username.trim(),
        displayName: payload.displayName.trim(),
        email: payload.email.trim(),
        role: 'user',
        password: payload.password,
      });

      window.localStorage.setItem(SESSION_KEY, String(user.id));
      return user;
    });
  }

  return apiRequest<CurrentUser>('/api/auth/register/', {
    method: 'POST',
    body: {
      username: payload.username.trim(),
      displayName: payload.displayName.trim(),
      email: payload.email.trim(),
      password: payload.password,
      confirmPassword: payload.confirmPassword,
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

export async function getMyApiToken(): Promise<ApiTokenPayload> {
  if (useMockApi()) {
    return mockResolve(() => {
      const sessionId = getStoredSessionId();
      if (!sessionId) {
        throw new Error('当前未登录');
      }

      return {
        apiToken: getCurrentUserApiToken(sessionId),
      };
    });
  }

  return apiRequest<ApiTokenPayload>('/api/me/api-token/');
}

export async function resetMyApiToken(): Promise<ApiTokenPayload> {
  if (useMockApi()) {
    return mockResolve(() => {
      const sessionId = getStoredSessionId();
      if (!sessionId) {
        throw new Error('当前未登录');
      }

      return {
        apiToken: resetUserApiToken(sessionId),
      };
    });
  }

  return apiRequest<ApiTokenPayload>('/api/me/api-token/', { method: 'POST' });
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
