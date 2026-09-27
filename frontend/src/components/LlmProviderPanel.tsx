import { useEffect, useState } from 'react'
import {
  clearLlmProvider,
  getLlmProviderStatus,
  type LlmProvider,
} from '../services/api'
import LlmProviderForm from './LlmProviderForm'

const PROVIDER_LABEL: Record<LlmProvider, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
}

function LlmProviderPanel() {
  const [provider, setProvider] = useState<LlmProvider | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isClearing, setIsClearing] = useState(false)

  useEffect(() => {
    getLlmProviderStatus()
      .then((status) => setProvider(status.provider))
      .finally(() => setIsLoading(false))
  }, [])

  async function handleClear() {
    setIsClearing(true)
    try {
      await clearLlmProvider()
      setProvider(null)
    } finally {
      setIsClearing(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-medium text-foreground">LLM provider</h2>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Checking provider…</p>
      ) : provider ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 rounded-md border border-border bg-background px-3 py-2.5">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-primary" />
            <p className="text-sm text-foreground">
              Using {PROVIDER_LABEL[provider]}
            </p>
          </div>
          <button
            type="button"
            onClick={handleClear}
            disabled={isClearing}
            className="w-full rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isClearing ? 'Removing…' : 'Remove key'}
          </button>
        </div>
      ) : (
        <LlmProviderForm onSaved={setProvider} />
      )}
    </div>
  )
}

export default LlmProviderPanel
