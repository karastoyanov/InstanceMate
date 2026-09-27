const INSTANCE_URL_PATTERN =
  /^https:\/\/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.service-now\.com$/i

/** Trim/normalize a user-entered instance URL, or return null if invalid. */
export function normalizeInstanceUrl(rawUrl: string): string | null {
  const trimmed = rawUrl.trim().replace(/\/+$/, '')
  return INSTANCE_URL_PATTERN.test(trimmed) ? trimmed : null
}
