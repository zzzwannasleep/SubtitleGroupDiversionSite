export type UserRole = "admin" | "uploader" | "user";
export type UserStatus = "active" | "banned" | "pending";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  avatar_url: string | null;
  tracker_credential: string;
  rss_key: string;
  created_at: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  avatar_url: string | null;
  bio: string | null;
  role: UserRole;
  status: UserStatus;
  rss_key: string;
  created_at: string;
  tracker_credential: string;
  uploaded_bytes: number;
  downloaded_bytes: number;
  ratio: string | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface TorrentListItem {
  id: number;
  name: string;
  subtitle?: string | null;
  category: string;
  size_bytes: number;
  owner: string;
  seeders: number;
  leechers: number;
  snatches: number;
  created_at: string;
  is_free: boolean;
}

export interface TorrentStats {
  seeders: number;
  leechers: number;
  snatches: number;
  finished: number;
}

export interface TorrentFile {
  file_path: string;
  file_size_bytes: number;
}

export interface TorrentDetail {
  id: number;
  name: string;
  subtitle?: string | null;
  description?: string | null;
  info_hash: string;
  size_bytes: number;
  category: Category;
  owner: {
    id: number;
    username: string;
  };
  stats: TorrentStats;
  files: TorrentFile[];
  media_info?: string | null;
  nfo_text?: string | null;
  cover_image_url?: string | null;
  is_free: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
