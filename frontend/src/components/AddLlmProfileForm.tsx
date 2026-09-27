import { useState, type FormEvent } from 'react'
import {
  ApiError,
  createLlmProfile,
  type LlmProviderName,
} from '../services/api'
import { formInputClass } from './formStyles'

const PROVIDER_OPTIONS: { value: LlmProviderName; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google' },
]

interface AddLlmProfileFormProps {
  onCreated: () => void
  onCancel: () => void
}

function AddLlmProfileForm({ onCreated, onCancel }: AddLlmProfileFormProps) {
  const [label, setLabel] = useState('')
  const [provider, setProvider] = useState<LlmProviderName>('openai')
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (!label.trim()) {
      setError('Give this profile a name')
      return
    }
    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }

    setIsSubmitting(true)
    try {
      await createLlmProfile({
        label: label.trim(),
        provider,
        apiKey: apiKey.trim(),
      })
      onCreated()
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
          htmlFor="llmLabel"
          className="text-sm font-medium text-foreground"
        >
          Name
        </label>
        <input
          id="llmLabel"
          type="text"
          autoComplete="off"
          placeholder="e.g. Personal OpenAI"
          value={label}
          onChange={(event) => setLabel(event.target.value)}
          className={formInputClass}
        />
      </div>

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
          onChange={(event) =>
            setProvider(event.target.value as LlmProviderName)
          }
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

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-background"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default AddLlmProfileForm
