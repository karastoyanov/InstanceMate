import { useState } from 'react'
import type { AuthType } from '../services/api'
import AddServiceNowBasicForm from './AddServiceNowBasicForm'
import AddServiceNowOAuthForm from './AddServiceNowOAuthForm'

interface AddServiceNowProfileFormProps {
  onCreated: () => void
  onCancel: () => void
}

function AddServiceNowProfileForm({
  onCreated,
  onCancel,
}: AddServiceNowProfileFormProps) {
  const [method, setMethod] = useState<AuthType>('oauth')

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
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
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Cancel
        </button>
      </div>

      {method === 'oauth' ? (
        <AddServiceNowOAuthForm />
      ) : (
        <AddServiceNowBasicForm onCreated={onCreated} />
      )}
    </div>
  )
}

export default AddServiceNowProfileForm
