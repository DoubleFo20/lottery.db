import { Link } from 'react-router'
import { ROUTES } from '@/constants/routes'
import { useTheme } from '@/hooks/useTheme'

interface TopNavigationProps {
  onMenuToggle: () => void
}

const NAV_LINKS = [
  { to: ROUTES.home, label: 'Home' },
  { to: ROUTES.dashboard, label: 'Dashboard' },
  { to: ROUTES.history, label: 'History' },
  { to: ROUTES.prediction, label: 'Prediction' },
  { to: ROUTES.analytics, label: 'Analytics' },
  { to: ROUTES.settings, label: 'Settings' },
]

function TopNavigation({ onMenuToggle }: TopNavigationProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="topbar">
      <button type="button" className="topbar__menu-btn" onClick={onMenuToggle}>
        Menu
      </button>
      <Link to={ROUTES.home} className="topbar__brand">
        Lottery
      </Link>
      <nav className="topbar__links">
        {NAV_LINKS.map((link) => (
          <Link key={link.to} to={link.to}>
            {link.label}
          </Link>
        ))}
      </nav>
      <button
        type="button"
        className="topbar__theme-btn"
        aria-label="Toggle color theme"
        onClick={toggleTheme}
      >
        {theme === 'light' ? 'Dark' : 'Light'}
      </button>
    </header>
  )
}

export default TopNavigation
