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

export type AuthType = 'oauth' | 'basic'

export interface ServiceNowProfile {
  id: number
  label: string
  instance_url: string
  auth_type: AuthType
}

export function listServiceNowProfiles() {
  return request<{ profiles: ServiceNowProfile[] }>('/profiles/servicenow')
}

export function deleteServiceNowProfile(profileId: number) {
  return request<{ ok: true }>(`/profiles/servicenow/${profileId}`, {
    method: 'DELETE',
  })
}

export interface StartOAuthProfilePayload {
  label: string
  instanceUrl: string
  clientId: string
  clientSecret: string
}

export function startServiceNowOAuthProfile(payload: StartOAuthProfilePayload) {
  return request<{ authorization_url: string }>(
    '/profiles/servicenow/oauth/start',
    {
      method: 'POST',
      body: JSON.stringify({
        label: payload.label,
        instance_url: payload.instanceUrl,
        client_id: payload.clientId,
        client_secret: payload.clientSecret,
      }),
    },
  )
}

export interface CreateBasicProfilePayload {
  label: string
  instanceUrl: string
  username: string
  password: string
}

export function createServiceNowBasicProfile(
  payload: CreateBasicProfilePayload,
) {
  return request<{ profile: ServiceNowProfile }>('/profiles/servicenow/basic', {
    method: 'POST',
    body: JSON.stringify({
      label: payload.label,
      instance_url: payload.instanceUrl,
      username: payload.username,
      password: payload.password,
    }),
  })
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
