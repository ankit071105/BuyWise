'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { LayoutDashboard, Package, MessageSquare, History, Bell, Settings, LogOut, TrendingUp, Zap } from 'lucide-react'
import { useAuthStore } from '@/lib/store'
import clsx from 'clsx'

const NAV = [
  { href: '/dashboard',       label: 'Dashboard',   icon: LayoutDashboard },
  { href: '/dashboard/track', label: 'Tracked',     icon: Package },
  { href: '/dashboard/chat',  label: 'AI Assistant',icon: MessageSquare },
  { href: '/dashboard/history', label: 'History',   icon: History },
  { href: '/dashboard/alerts', label: 'Alerts',     icon: Bell },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout, initFromStorage } = useAuthStore()

  useEffect(() => { initFromStorage() }, [])

  function handleLogout() {
    logout()
    router.push('/auth/login')
  }

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-cyan-100 flex flex-col shadow-card">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-cyan-100">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center shadow-score">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-display font-bold text-navy-700 text-lg leading-none">BuyWise</span>
            <p className="text-xs text-cyan-500 font-medium mt-0.5">Smart Shopping AI</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link key={href} href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                active
                  ? 'bg-cyan-50 text-cyan-600 border border-cyan-200 shadow-sm'
                  : 'text-navy-500 hover:bg-cyan-50 hover:text-cyan-600'
              )}>
              <Icon className={clsx('w-4.5 h-4.5', active ? 'text-cyan-500' : 'text-navy-400')} size={18} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-cyan-100 space-y-2">
        {user && (
          <div className="px-3 py-2.5 rounded-xl bg-cyan-50 border border-cyan-100">
            <p className="text-sm font-semibold text-navy-700 truncate">{user.name}</p>
            <p className="text-xs text-navy-400 truncate">{user.email}</p>
          </div>
        )}
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 transition-colors">
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  )
}
