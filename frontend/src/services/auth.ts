import type { CurrentUser, LoginPayload } from '@/types/auth';
import { mockRequest } from './api';
import { getUserById, getUserByUsername, resetPasskey as regeneratePasskey } from './mock-data';

const SESSION_KEY = 'sgds:session-user-id';

function getStoredSessionId(): number | null {
  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function fetchMe(): Promise<CurrentUser | null> {
  return mockRequest(() => {
    const sessionId = getStoredSessionId();
    if (!sessionId) return null;
    return getUserById(sessionId) ?? null;
  });
}

export async function login(payload: LoginPayload): Promise<CurrentUser> {
  const username = payload.username.trim();

  return mockRequest(() => {
    const user = getUserByUsername(username);

    if (!payload.password.trim()) {
      throw new Error('请输入密码');
    }

    if (!user) {
      throw new Error('用户名不存在，可使用 admin / uploader / user 体验不同角色');
    }

    if (user.status === 'disabled') {
      throw new Error('该账号已被禁用，请联系管理员处理');
    }

    window.localStorage.setItem(SESSION_KEY, String(user.id));
    return user;
  });
}

export async function logout(): Promise<void> {
  return mockRequest(() => {
    window.localStorage.removeItem(SESSION_KEY);
  });
}

export async function resetPasskey(userId: number): Promise<CurrentUser> {
  return mockRequest(() => regeneratePasskey(userId));
}

