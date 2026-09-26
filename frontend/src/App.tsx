function App() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 bg-background text-foreground">
      <h1 className="text-2xl font-semibold">InstanceMate</h1>
      <p className="text-muted-foreground">
        Vite + React + Tailwind, themed for light and dark.
      </p>
      <button
        type="button"
        className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover"
      >
        Primary action
      </button>
    </div>
  )
}

export default App
