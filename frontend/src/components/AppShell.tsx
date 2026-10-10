import { NavLink, useLocation } from 'react-router-dom'
import { Activity, Boxes, FileText, Home, Library, Repeat, Swords } from 'lucide-react'
import { clsx } from './clsx'
import { QualitySelector } from './QualitySelector'

const NAV = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/dashboard', label: 'Dashboard', icon: Activity },
  { to: '/range', label: '3D Cyber Range', icon: Boxes },
  { to: '/replay', label: 'Counterfactual Replay', icon: Repeat },
  { to: '/arena', label: 'Red vs Blue', icon: Swords },
  { to: '/scenarios', label: 'Scenario Library', icon: Library },
  { to: '/reports', label: 'Reports', icon: FileText },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const loc = useLocation()
  const isLanding = loc.pathname === '/'

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-[var(--border-subtle)] bg-obsidian/70 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2.5">
            <Logo />
            <div className="leading-tight">
              <span className="block text-sm font-bold tracking-wide text-ink">
                SpecterRed <span className="text-cyan">X</span>
              </span>
              <span className="block text-[10px] uppercase tracking-[0.2em] text-muted">
                Cyber Defense Simulator
              </span>
            </div>
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Primary">
            {NAV.filter((n) => n.to !== '/').map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors duration-150',
                    isActive ? 'bg-cyan/10 text-cyan' : 'text-muted hover:text-ink',
                  )
                }
              >
                <n.icon size={15} aria-hidden />
                {n.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <QualitySelector />
          </div>
        </div>

        {/* mobile/tablet nav */}
        <nav
          className="flex gap-1 overflow-x-auto border-t border-[var(--border-subtle)] px-3 py-2 lg:hidden"
          aria-label="Primary mobile"
        >
          {NAV.filter((n) => n.to !== '/').map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                clsx(
                  'flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs',
                  isActive ? 'bg-cyan/10 text-cyan' : 'text-muted',
                )
              }
            >
              <n.icon size={14} aria-hidden />
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className={clsx(isLanding ? '' : 'mx-auto max-w-[1600px] px-4 py-6')}>{children}</main>
    </div>
  )
}

function Logo() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden>
      <path
        d="M16 3 L27 7 V16 C27 23 21.5 27.5 16 29.5 C10.5 27.5 5 23 5 16 V7 Z"
        fill="none"
        stroke="var(--brand-cyan)"
        strokeWidth="1.6"
      />
      <circle cx="16" cy="14.5" r="3.4" fill="var(--agent-red)" />
      <path d="M16 14.5 L22.5 20.5" stroke="var(--agent-blue)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}
