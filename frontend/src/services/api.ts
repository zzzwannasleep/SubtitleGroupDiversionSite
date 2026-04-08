export async function mockRequest<T>(factory: () => T, delay = 220): Promise<T> {
  await new Promise((resolve) => window.setTimeout(resolve, delay));
  return structuredClone(factory());
}

