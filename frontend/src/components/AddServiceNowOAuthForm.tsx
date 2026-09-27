import { useState, type FormEvent } from 'react'
import { ApiError, startServiceNowOAuthProfile } from '../services/api'
import { normalizeInstanceUrl } from '../utils/serviceNowInstanceUrl'
import { formInputClass } from './formStyles'

function AddServiceNowOAuthForm() {
  const [label, setLabel] = useState('')
  const [instanceUrl, setInstanceUrl] = useState('')
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    const trimmedUrl = normalizeInstanceUrl(instanceUrl)
    if (!trimmedUrl) {
      setError(
        'Enter a valid instance URL, e.g. https://your-instance.service-now.com',
      )
      return
    }
    if (!label.trim()) {
      setError('Give this instance a name')
      return
    }
    if (!clientId.trim() || !clientSecret.trim()) {
      setError('Client ID and Client Secret are required')
      return
    }

    setIsSubmitting(true)
    try {
      const { authorization_url: authorizationUrl } =
        await startServiceNowOAuthProfile({
          label: label.trim(),
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
        <label htmlFor="label" className="text-sm font-medium text-foreground">
          Name
        </label>
        <input
          id="label"
          type="text"
          autoComplete="off"
          placeholder="e.g. Acme Prod"
          value={label}
          onChange={(event) => setLabel(event.target.value)}
          className={formInputClass}
        />
      </div>

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
          className={formInputClass}
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
          className={formInputClass}
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
        {isSubmitting ? 'Redirecting…' : 'Connect with ServiceNow'}
      </button>
    </form>
  )
}

export default AddServiceNowOAuthForm
