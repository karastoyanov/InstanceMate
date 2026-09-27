import { useState } from 'react'
import { deleteLlmProfile, type LlmProfile } from '../services/api'

const PROVIDER_LABEL: Record<LlmProfile['provider'], string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
}

interface LlmProfileListProps {
  profiles: LlmProfile[]
  onDeleted: () => void
}

function LlmProfileList({ profiles, onDeleted }: LlmProfileListProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null)

  async function handleDelete(id: number) {
    setDeletingId(id)
    try {
      await deleteLlmProfile(id)
      onDeleted()
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <ul className="flex flex-col gap-2">
      {profiles.map((profile) => (
        <li
          key={profile.id}
          className="flex items-center gap-3 rounded-md border border-border bg-background px-3 py-2.5"
        >
          <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-primary" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground">
              {profile.label}
              <span className="ml-2 text-xs font-normal text-muted-foreground">
                {PROVIDER_LABEL[profile.provider]}
              </span>
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleDelete(profile.id)}
            disabled={deletingId === profile.id}
            className="shrink-0 text-sm font-medium text-muted-foreground hover:text-destructive disabled:cursor-not-allowed disabled:opacity-60"
          >
            {deletingId === profile.id ? 'Removing…' : 'Remove'}
          </button>
        </li>
      ))}
    </ul>
  )
}

export default LlmProfileList
