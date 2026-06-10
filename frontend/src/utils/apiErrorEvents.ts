type ApiErrorListener = (message: string) => void;

const listeners = new Set<ApiErrorListener>();

export function subscribeApiErrors(listener: ApiErrorListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function notifyApiError(message: string): void {
  listeners.forEach((listener) => listener(message));
}
