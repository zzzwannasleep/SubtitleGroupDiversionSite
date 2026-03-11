import type { UserProfile } from "@/types";

import { apiRequest } from "./http";


export function getProfile(): Promise<UserProfile> {
  return apiRequest<UserProfile>("/users/profile");
}


export function updateProfile(email: string): Promise<UserProfile> {
  return apiRequest<UserProfile>("/users/profile", {
    method: "PATCH",
    body: { email },
  });
}

