import type { Category } from "@/types";

import { apiRequest } from "./http";


export function listCategories(): Promise<Category[]> {
  return apiRequest<Category[]>("/categories", { auth: false });
}

