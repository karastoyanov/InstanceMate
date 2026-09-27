import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ConnectedPanel from '../components/ConnectedPanel'
import ServiceNowLoginForm from '../components/ServiceNowLoginForm'
import { getAuthStatus } from '../services/api'

const ERROR_MESSAGES: Record<string, string> = {
  sn_denied: 'ServiceNow declined the authorization request.',
  invalid_state:
    'Your login attempt expired or was tampered with. Please try again.',
  missing_code:
    'ServiceNow did not return an authorization code. Please try again.',
  token_exchange_failed:
    'ServiceNow rejected the token exchange. Check your Client ID/Secret.',
}

function Login() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [instanceUrl, setInstanceUrl] = useState<string | null>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(true)

  // Lazy initializer: read the OAuth redirect's query params exactly once,
  // before they get cleared from the URL below.
  const [banner] = useState<{ kind: 'success' | 'error'; text: string } | null>(
    () => {
      const login = searchParams.get('login')
      if (login === 'success') {
        return {
          kind: 'success',
          text: 'Connected to your ServiceNow instance.',
        }
      }
      if (login === 'error') {
        const reason = searchParams.get('reason') ?? ''
        return {
          kind: 'error',
          text: ERROR_MESSAGES[reason] ?? 'Login failed. Please try again.',
        }
      }
      return null
    },
  )

  useEffect(() => {
    if (searchParams.get('login')) {
      setSearchParams({}, { replace: true })
    }
    // Only needs to run once, on the redirect back from the OAuth callback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    getAuthStatus()
      .then((status) =>
        setInstanceUrl(status.connected ? (status.instance_url ?? null) : null),
      )
      .finally(() => setIsLoadingStatus(false))
  }, [])

  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-hidden bg-background px-4 py-12">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 -left-32 h-72 w-72 rounded-full bg-primary/30 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 -bottom-32 h-80 w-80 rounded-full bg-primary/20 blur-3xl"
      />

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-lg font-bold text-primary-foreground">
            IM
          </span>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground">
            InstanceMate
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            AI troubleshooting for your ServiceNow instance
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-surface p-6 shadow-xl shadow-black/5 sm:p-8">
          {banner && (
            <p
              role="status"
              className={`mb-4 rounded-md border px-3 py-2 text-sm ${
                banner.kind === 'success'
                  ? 'border-primary/40 bg-primary/10 text-primary'
                  : 'border-destructive/40 bg-destructive/10 text-destructive'
              }`}
            >
              {banner.text}
            </p>
          )}

          {isLoadingStatus ? (
            <p className="text-sm text-muted-foreground">
              Checking connection…
            </p>
          ) : instanceUrl ? (
            <ConnectedPanel
              instanceUrl={instanceUrl}
              onDisconnected={() => setInstanceUrl(null)}
            />
          ) : (
            <ServiceNowLoginForm />
          )}
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          Your credentials are exchanged directly with your ServiceNow instance
          via OAuth — InstanceMate never sees your password.
        </p>
      </div>
    </div>
  )
}

export default Login
