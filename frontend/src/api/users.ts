import type { UserProfile } from "@/types";

import { apiRequest } from "./http";

export interface UpdateProfilePayload {
  email: string;
  avatar_url: string | null;
  bio: string | null;
}


export function getProfile(): Promise<UserProfile> {
  return apiRequest<UserProfile>("/users/profile");
}


export function updateProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  return apiRequest<UserProfile>("/users/profile", {
    method: "PATCH",
    body: payload,
  });
}
