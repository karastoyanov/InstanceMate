import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import BasicAuthLoginForm from '../components/BasicAuthLoginForm'
import ConnectedPanel from '../components/ConnectedPanel'
import OAuthLoginForm from '../components/OAuthLoginForm'
import { getAuthStatus, type AuthType } from '../services/api'

const ERROR_MESSAGES: Record<string, string> = {
  sn_denied: 'ServiceNow declined the authorization request.',
  invalid_state:
    'Your login attempt expired or was tampered with. Please try again.',
  missing_code:
    'ServiceNow did not return an authorization code. Please try again.',
  token_exchange_failed:
    'ServiceNow rejected the token exchange. Check your Client ID/Secret.',
}

const FOOTER_TEXT: Record<AuthType, string> = {
  oauth:
    'Your credentials are exchanged directly with your ServiceNow instance via OAuth — InstanceMate never sees your password.',
  basic:
    'Your username and password are kept only for your active session and are never stored beyond it.',
}

function Home() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [connection, setConnection] = useState<{
    instanceUrl: string
    authType?: AuthType
  } | null>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(true)
  const [method, setMethod] = useState<AuthType>('oauth')

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
        setConnection(
          status.connected && status.instance_url
            ? { instanceUrl: status.instance_url, authType: status.auth_type }
            : null,
        ),
      )
      .finally(() => setIsLoadingStatus(false))
  }, [])

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        Connect your ServiceNow instance
      </h1>

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
          <p className="text-sm text-muted-foreground">Checking connection…</p>
        ) : connection ? (
          <ConnectedPanel
            instanceUrl={connection.instanceUrl}
            authType={connection.authType}
            onDisconnected={() => setConnection(null)}
          />
        ) : (
          <div className="flex flex-col gap-5">
            <div className="flex rounded-lg border border-border bg-background p-1 text-sm font-medium">
              <button
                type="button"
                onClick={() => setMethod('oauth')}
                className={`flex-1 rounded-md px-3 py-1.5 transition ${
                  method === 'oauth'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                OAuth
              </button>
              <button
                type="button"
                onClick={() => setMethod('basic')}
                className={`flex-1 rounded-md px-3 py-1.5 transition ${
                  method === 'basic'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Basic auth
              </button>
            </div>

            {method === 'oauth' ? (
              <OAuthLoginForm />
            ) : (
              <BasicAuthLoginForm
                onConnected={(instanceUrl) =>
                  setConnection({ instanceUrl, authType: 'basic' })
                }
              />
            )}
          </div>
        )}
      </div>

      <p className="text-center text-xs text-muted-foreground">
        {FOOTER_TEXT[connection?.authType ?? method]}
      </p>
    </div>
  )
}

export default Home
