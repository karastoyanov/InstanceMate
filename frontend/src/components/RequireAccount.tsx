import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { getAccountStatus } from '../services/api'

function RequireAccount() {
  const [isChecking, setIsChecking] = useState(true)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    getAccountStatus()
      .then((status) => setIsLoggedIn(status.user !== null))
      .finally(() => setIsChecking(false))
  }, [])

  if (isChecking) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    )
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default RequireAccount
