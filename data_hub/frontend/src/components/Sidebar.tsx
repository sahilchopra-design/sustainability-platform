import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  Database,
  Layers,
  GitMerge,
  Search,
  RefreshCw,
  Zap,
} from 'lucide-react'

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/sources', icon: Database, label: 'Data Sources' },
  { to: '/kpis', icon: Layers, label: 'KPI Directory' },
  { to: '/mappings', icon: GitMerge, label: 'Mapping Studio' },
  { to: '/query', icon: Search, label: 'Query Builder' },
  { to: '/sync', icon: RefreshCw, label: 'Sync Monitor' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-hub-surface border-r border-hub-border flex flex-col">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-hub-border">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-hub-primary to-hub-secondary flex items-center justify-center">
          <Zap size={14} className="text-white" strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-sm font-semibold text-hub-text-primary leading-none">A2 Data Hub</div>
          <div className="text-[10px] text-hub-text-muted leading-none mt-0.5">Reference Data Module</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-hub-primary/15 text-hub-primary'
                  : 'text-hub-text-secondary hover:bg-hub-muted hover:text-hub-text-primary',
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={16}
                  className={isActive ? 'text-hub-primary' : 'text-hub-text-muted'}
                  strokeWidth={isActive ? 2.5 : 1.75}
                />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-hub-border">
        <div className="text-[11px] text-hub-text-muted">
          <span className="font-mono">v1.0.0</span>
          {' · '}
          <a
            href="http://localhost:8002/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-hub-text-secondary transition-colors"
          >
            API Docs
          </a>
        </div>
      </div>
    </aside>
  )
}
