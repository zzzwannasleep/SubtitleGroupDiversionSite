import type { PaginatedResponse } from "@/types";

import { apiRequest } from "./http";


export interface AdminUserItem {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}


export function listAdminUsers(): Promise<PaginatedResponse<AdminUserItem>> {
  return apiRequest<PaginatedResponse<AdminUserItem>>("/admin/users");
}

