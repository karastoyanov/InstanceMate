import { useEffect, useState } from 'react'
import { ApiError, listLlmProfiles, type LlmProfile } from '../services/api'
import AddLlmProfileForm from './AddLlmProfileForm'
import LlmProfileList from './LlmProfileList'

function LlmSettingsSection() {
  const [profiles, setProfiles] = useState<LlmProfile[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isAdding, setIsAdding] = useState(false)

  function refreshProfiles() {
    return listLlmProfiles()
      .then((res) => {
        setLoadError(null)
        setProfiles(res.profiles)
      })
      .catch((err) => {
        setLoadError(
          err instanceof ApiError
            ? err.message
            : 'Could not load your AI provider profiles. Try again.',
        )
      })
  }

  useEffect(() => {
    refreshProfiles()
  }, [])

  return (
    <section className="rounded-2xl border border-border bg-surface p-6 shadow-xl shadow-black/5 sm:p-8">
      <h2 className="text-lg font-semibold text-foreground">AI providers</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        BYOK profiles you can pick from when starting a new chat.
      </p>

      <div className="mt-5">
        {loadError ? (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <p className="text-sm text-destructive">{loadError}</p>
            <button
              type="button"
              onClick={() => void refreshProfiles()}
              className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-background"
            >
              Retry
            </button>
          </div>
        ) : profiles === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="flex flex-col gap-5">
            {profiles.length > 0 && (
              <LlmProfileList profiles={profiles} onDeleted={refreshProfiles} />
            )}

            {isAdding ? (
              <AddLlmProfileForm
                onCreated={() => {
                  setIsAdding(false)
                  refreshProfiles()
                }}
                onCancel={() => setIsAdding(false)}
              />
            ) : profiles.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-4 text-center">
                <p className="text-sm text-muted-foreground">
                  No AI provider profiles yet.
                </p>
                <button
                  type="button"
                  onClick={() => setIsAdding(true)}
                  className="rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover"
                >
                  Add a provider
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAdding(true)}
                className="w-full rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-background"
              >
                Add another provider
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  )
}

export default LlmSettingsSection
