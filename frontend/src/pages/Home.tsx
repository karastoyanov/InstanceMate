import { Link } from 'react-router-dom'

function Home() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">Welcome back</h1>
      <p className="text-sm text-muted-foreground">
        Connect a ServiceNow instance and an AI provider in Settings to get
        started. Chat is coming soon.
      </p>
      <Link
        to="/settings"
        className="w-fit rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover"
      >
        Go to Settings
      </Link>
    </div>
  )
}

export default Home
