import { useState, type FormEvent } from 'react'
import { ApiError, startServiceNowLogin } from '../services/api'

const INSTANCE_URL_PATTERN =
  /^https:\/\/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.service-now\.com$/i

const inputClass =
  'w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/40'

function ServiceNowLoginForm() {
  const [instanceUrl, setInstanceUrl] = useState('')
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    const trimmedUrl = instanceUrl.trim().replace(/\/+$/, '')
    if (!INSTANCE_URL_PATTERN.test(trimmedUrl)) {
      setError(
        'Enter a valid instance URL, e.g. https://your-instance.service-now.com',
      )
      return
    }
    if (!clientId.trim() || !clientSecret.trim()) {
      setError('Client ID and Client Secret are required')
      return
    }

    setIsSubmitting(true)
    try {
      const { authorization_url: authorizationUrl } =
        await startServiceNowLogin({
          instanceUrl: trimmedUrl,
          clientId: clientId.trim(),
          clientSecret: clientSecret.trim(),
        })
      window.location.href = authorizationUrl
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong. Try again.',
      )
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="instanceUrl"
          className="text-sm font-medium text-foreground"
        >
          Instance URL
        </label>
        <input
          id="instanceUrl"
          type="text"
          inputMode="url"
          autoComplete="off"
          placeholder="https://your-instance.service-now.com"
          value={instanceUrl}
          onChange={(event) => setInstanceUrl(event.target.value)}
          className={inputClass}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="clientId"
          className="text-sm font-medium text-foreground"
        >
          OAuth Client ID
        </label>
        <input
          id="clientId"
          type="text"
          autoComplete="off"
          value={clientId}
          onChange={(event) => setClientId(event.target.value)}
          className={inputClass}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="clientSecret"
          className="text-sm font-medium text-foreground"
        >
          OAuth Client Secret
        </label>
        <input
          id="clientSecret"
          type="password"
          autoComplete="off"
          value={clientSecret}
          onChange={(event) => setClientSecret(event.target.value)}
          className={inputClass}
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
        {isSubmitting ? 'Redirecting…' : 'Connect with ServiceNow'}
      </button>
    </form>
  )
}

export default ServiceNowLoginForm
