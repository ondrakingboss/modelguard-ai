/**
 * Centralized API configuration for ModelGuard AI.
 *
 * In development, API calls go through Next.js rewrites to localhost:8000.
 * In production, set NEXT_PUBLIC_API_BASE_URL to the deployed backend URL.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function apiUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
}