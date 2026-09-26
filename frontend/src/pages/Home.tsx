function Home() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Home</h1>
      <p className="text-muted-foreground">
        Placeholder page — login, chat, and settings will live here.
      </p>
      <button
        type="button"
        className="w-fit rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover"
      >
        Primary action
      </button>
    </div>
  )
}

export default Home
