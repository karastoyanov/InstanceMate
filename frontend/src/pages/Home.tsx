import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import AddServiceNowProfileForm from '../components/AddServiceNowProfileForm'
import ServiceNowProfileList from '../components/ServiceNowProfileList'
import { listServiceNowProfiles, type ServiceNowProfile } from '../services/api'

const ERROR_MESSAGES: Record<string, string> = {
  sn_denied: 'ServiceNow declined the authorization request.',
  invalid_state:
    'Your login attempt expired or was tampered with. Please try again.',
  missing_code:
    'ServiceNow did not return an authorization code. Please try again.',
  token_exchange_failed:
    'ServiceNow rejected the token exchange. Check your Client ID/Secret.',
  not_logged_in: 'You were logged out before the connection completed.',
}

function Home() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [profiles, setProfiles] = useState<ServiceNowProfile[] | null>(null)
  const [isAdding, setIsAdding] = useState(false)

  // Lazy initializer: read the OAuth redirect's query params exactly once,
  // before they get cleared from the URL below.
  const [banner] = useState<{ kind: 'success' | 'error'; text: string } | null>(
    () => {
      const login = searchParams.get('login')
      if (login === 'success') {
        return { kind: 'success', text: 'ServiceNow instance connected.' }
      }
      if (login === 'error') {
        const reason = searchParams.get('reason') ?? ''
        return {
          kind: 'error',
          text:
            ERROR_MESSAGES[reason] ?? 'Connection failed. Please try again.',
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

  function refreshProfiles() {
    return listServiceNowProfiles().then((res) => setProfiles(res.profiles))
  }

  useEffect(() => {
    refreshProfiles()
  }, [])

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        ServiceNow instances
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

        {profiles === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="flex flex-col gap-5">
            {profiles.length > 0 && (
              <ServiceNowProfileList
                profiles={profiles}
                onDeleted={refreshProfiles}
              />
            )}

            {isAdding ? (
              <AddServiceNowProfileForm
                onCreated={() => {
                  setIsAdding(false)
                  refreshProfiles()
                }}
                onCancel={() => setIsAdding(false)}
              />
            ) : profiles.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-4 text-center">
                <p className="text-sm text-muted-foreground">
                  No ServiceNow instances connected yet.
                </p>
                <button
                  type="button"
                  onClick={() => setIsAdding(true)}
                  className="rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover"
                >
                  Connect an instance
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAdding(true)}
                className="w-full rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-background"
              >
                Add another instance
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Home
