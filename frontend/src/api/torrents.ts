import type { PaginatedResponse, TorrentDetail, TorrentListItem } from "@/types";

import { apiRequest } from "./http";


export interface ListTorrentParams {
  page?: number;
  page_size?: number;
  category?: string;
  keyword?: string;
  sort?: string;
}


export function listTorrents(params: ListTorrentParams): Promise<PaginatedResponse<TorrentListItem>> {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const suffix = search.toString();
  return apiRequest<PaginatedResponse<TorrentListItem>>(`/torrents${suffix ? `?${suffix}` : ""}`, { auth: false });
}


export function getTorrentDetail(id: number): Promise<TorrentDetail> {
  return apiRequest<TorrentDetail>(`/torrents/${id}`, { auth: false });
}


export function uploadTorrent(formData: FormData): Promise<{ id?: number; info_hash?: string; message: string }> {
  return apiRequest(`/torrents/upload`, {
    method: "POST",
    body: formData,
  });
}


export async function downloadTorrentFile(id: number): Promise<Blob> {
  const token = localStorage.getItem("pt-platform.token");
  const response = await fetch(`/api/torrents/${id}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    let message = "Download failed";
    try {
      const payload = await response.json();
      message = payload.detail ?? payload.message ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.blob();
}
