import { useState, type FormEvent } from 'react'
import { ApiError, startBasicLogin } from '../services/api'
import { normalizeInstanceUrl } from '../utils/serviceNowInstanceUrl'
import { formInputClass } from './formStyles'

interface BasicAuthLoginFormProps {
  onConnected: (instanceUrl: string) => void
}

function BasicAuthLoginForm({ onConnected }: BasicAuthLoginFormProps) {
  const [instanceUrl, setInstanceUrl] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
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
    if (!username.trim() || !password) {
      setError('Username and password are required')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await startBasicLogin({
        instanceUrl: trimmedUrl,
        username: username.trim(),
        password,
      })
      onConnected(result.instance_url ?? trimmedUrl)
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
      <p className="rounded-md border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
        OAuth is the preferred, more secure way to connect. Only use basic auth
        if your instance doesn't have an OAuth application registered.
      </p>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="basicInstanceUrl"
          className="text-sm font-medium text-foreground"
        >
          Instance URL
        </label>
        <input
          id="basicInstanceUrl"
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
          htmlFor="username"
          className="text-sm font-medium text-foreground"
        >
          Username
        </label>
        <input
          id="username"
          type="text"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className={formInputClass}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="password"
          className="text-sm font-medium text-foreground"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
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
        className="mt-2 w-full rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Signing in…' : 'Sign in with username & password'}
      </button>
    </form>
  )
}

export default BasicAuthLoginForm
