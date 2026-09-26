import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="text-muted-foreground">
        The page you're looking for doesn't exist.
      </p>
      <Link to="/" className="w-fit text-primary hover:underline">
        Back to home
      </Link>
    </div>
  )
}

export default NotFound
