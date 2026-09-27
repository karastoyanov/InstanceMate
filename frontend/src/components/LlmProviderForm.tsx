import { useState, type FormEvent } from 'react'
import { ApiError, setLlmProvider, type LlmProvider } from '../services/api'
import { formInputClass } from './formStyles'

const PROVIDER_OPTIONS: { value: LlmProvider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google' },
]

interface LlmProviderFormProps {
  onSaved: (provider: LlmProvider) => void
}

function LlmProviderForm({ onSaved }: LlmProviderFormProps) {
  const [provider, setProvider] = useState<LlmProvider>('openai')
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }

    setIsSubmitting(true)
    try {
      const status = await setLlmProvider(provider, apiKey.trim())
      if (status.provider) {
        onSaved(status.provider)
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong. Try again.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="llmProvider"
          className="text-sm font-medium text-foreground"
        >
          Provider
        </label>
        <select
          id="llmProvider"
          value={provider}
          onChange={(event) => setProvider(event.target.value as LlmProvider)}
          className={formInputClass}
        >
          {PROVIDER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="llmApiKey"
          className="text-sm font-medium text-foreground"
        >
          API key
        </label>
        <input
          id="llmApiKey"
          type="password"
          autoComplete="off"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          className={formInputClass}
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 w-full rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Saving…' : 'Save'}
      </button>
    </form>
  )
}

export default LlmProviderForm
