/**
 * Konfigurasi URL API Gateway — satu sumber untuk semua HTTP client.
 *
 * Development (microservices): http://localhost (gateway port 80)
 * Production: set VITE_GATEWAY_URL di Railway / .env.production
 */

function trimTrailingSlash(url: string): string {
  return url.replace(/\/$/, "");
}

export const GATEWAY_URL = trimTrailingSlash(
  import.meta.env.VITE_GATEWAY_URL || "http://localhost"
);

/** Base URL untuk procurement API via gateway: /api/v1/* */
export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || `${GATEWAY_URL}/api/v1`
);

/** Base URL untuk static uploads via gateway: /uploads/* */
export const UPLOADS_BASE_URL = GATEWAY_URL;

/** URL health check gateway */
export const GATEWAY_HEALTH_URL = `${GATEWAY_URL}/health`;

/** Bangun URL file upload yang di-serve gateway (/uploads/*). */
export function resolveUploadUrl(path: string | null | undefined): string {
  if (!path) return "#";
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalized = path.replace(/^\//, "");
  return `${UPLOADS_BASE_URL}/${normalized}`;
}
