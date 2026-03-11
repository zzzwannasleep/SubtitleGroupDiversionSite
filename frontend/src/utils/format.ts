export function formatBytes(bytes: number): string {
  if (bytes === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  const value = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / 1024 ** value).toFixed(value > 1 ? 2 : 0)} ${units[value]}`;
}


export function formatDate(input: string): string {
  return new Date(input).toLocaleString();
}
