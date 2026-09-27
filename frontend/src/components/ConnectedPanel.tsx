import { useState } from 'react'
import { logout, type AuthType } from '../services/api'

interface ConnectedPanelProps {
  instanceUrl: string
  authType?: AuthType
  onDisconnected: () => void
}

const AUTH_TYPE_LABEL: Record<AuthType, string> = {
  oauth: 'OAuth',
  basic: 'Basic auth',
}

function ConnectedPanel({
  instanceUrl,
  authType,
  onDisconnected,
}: ConnectedPanelProps) {
  const [isDisconnecting, setIsDisconnecting] = useState(false)

  async function handleDisconnect() {
    setIsDisconnecting(true)
    try {
      await logout()
      onDisconnected()
    } finally {
      setIsDisconnecting(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3 rounded-md border border-border bg-background px-3 py-2.5">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-primary" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">
            Connected{authType ? ` via ${AUTH_TYPE_LABEL[authType]}` : ''}
          </p>
          <p className="truncate text-sm text-muted-foreground">
            {instanceUrl}
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={handleDisconnect}
        disabled={isDisconnecting}
        className="w-full rounded-md border border-border px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isDisconnecting ? 'Disconnecting…' : 'Disconnect'}
      </button>
    </div>
  )
}

export default ConnectedPanel
