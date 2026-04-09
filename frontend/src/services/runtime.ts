export function getDataSourceMode() {
  const mode = String(import.meta.env.VITE_DATA_SOURCE ?? '').trim().toLowerCase();

  if (mode === 'api') return 'api';
  if (mode === 'mock') return 'mock';

  return 'api';
}

export function useMockApi() {
  return getDataSourceMode() === 'mock';
}

export async function mockResolve<T>(factory: () => T, delay = 160): Promise<T> {
  await new Promise((resolve) => window.setTimeout(resolve, delay));
  return structuredClone(factory());
}
