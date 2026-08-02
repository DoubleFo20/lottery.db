import { NavLink } from 'react-router'
import { ROUTES } from '@/constants/routes'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const NAV_ITEMS = [
  { to: ROUTES.home, label: 'Home', end: true },
  { to: ROUTES.dashboard, label: 'Dashboard' },
  { to: ROUTES.history, label: 'Lottery History' },
  { to: ROUTES.prediction, label: 'Prediction' },
  { to: ROUTES.analytics, label: 'Analytics' },
  { to: ROUTES.settings, label: 'Settings' },
]

function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && <div className="sidebar__backdrop" onClick={onClose} />}
      <aside className={`sidebar${open ? ' sidebar--open' : ''}`}>
        <nav aria-label="Sidebar">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                isActive ? 'sidebar__link sidebar__link--active' : 'sidebar__link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}

export default Sidebar
