import { NavLink, useNavigate } from 'react-router-dom'
import { logoutAccount } from '../services/api'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'

function Header() {
  const navigate = useNavigate()

  async function handleLogout() {
    await logoutAccount()
    navigate('/login')
  }

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <span className="text-lg font-semibold text-foreground">
          InstanceMate
        </span>
        <div className="flex items-center gap-4 text-sm font-medium">
          <nav className="flex gap-4">
            <NavLink to="/" end className={navLinkClass}>
              Home
            </NavLink>
            <NavLink to="/settings" className={navLinkClass}>
              Settings
            </NavLink>
          </nav>
          <button
            type="button"
            onClick={handleLogout}
            className="text-muted-foreground hover:text-foreground"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
