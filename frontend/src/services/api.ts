const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.error || 'Request failed')
  }

  return response.json() as Promise<T>
}

export interface ServiceNowLoginPayload {
  instanceUrl: string
  clientId: string
  clientSecret: string
}

export function startServiceNowLogin(payload: ServiceNowLoginPayload) {
  return request<{ authorization_url: string }>('/auth/servicenow/login', {
    method: 'POST',
    body: JSON.stringify({
      instance_url: payload.instanceUrl,
      client_id: payload.clientId,
      client_secret: payload.clientSecret,
    }),
  })
}

export interface BasicLoginPayload {
  instanceUrl: string
  username: string
  password: string
}

export function startBasicLogin(payload: BasicLoginPayload) {
  return request<AuthStatus>('/auth/servicenow/basic-login', {
    method: 'POST',
    body: JSON.stringify({
      instance_url: payload.instanceUrl,
      username: payload.username,
      password: payload.password,
    }),
  })
}

export type AuthType = 'oauth' | 'basic'

export interface AuthStatus {
  connected: boolean
  instance_url?: string
  auth_type?: AuthType
}

export function getAuthStatus() {
  return request<AuthStatus>('/auth/servicenow/status')
}

export function logout() {
  return request<AuthStatus>('/auth/servicenow/logout', { method: 'POST' })
}

export interface Account {
  id: number
  email: string
  username: string
}

export interface AccountStatus {
  user: Account | null
}

export function registerAccount(
  email: string,
  username: string,
  password: string,
) {
  return request<AccountStatus>('/account/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  })
}

export function loginAccount(email: string, password: string) {
  return request<AccountStatus>('/account/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function logoutAccount() {
  return request<AccountStatus>('/account/logout', { method: 'POST' })
}

export function getAccountStatus() {
  return request<AccountStatus>('/account/me')
}
