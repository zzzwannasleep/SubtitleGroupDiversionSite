export type UserRole = 'admin' | 'uploader' | 'user';
export type UserStatus = 'active' | 'disabled';

export interface UserSummary {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
}

export interface CurrentUser extends UserSummary {
  email: string;
  status: UserStatus;
  passkey: string;
  lastLoginAt: string;
  joinedAt: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  displayName: string;
  email: string;
  password: string;
  confirmPassword: string;
  inviteCode?: string;
}
