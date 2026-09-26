import { NavLink } from 'react-router-dom'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'

function Header() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <span className="text-lg font-semibold text-foreground">
          InstanceMate
        </span>
        <nav className="flex gap-4 text-sm font-medium">
          <NavLink to="/" end className={navLinkClass}>
            Home
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default Header
