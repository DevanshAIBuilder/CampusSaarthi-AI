'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  GraduationCap, PanelLeftClose, PanelLeftOpen,
  Settings, Home, HelpCircle, Zap,
} from 'lucide-react'
import { getHealth } from '@/lib/api'
import type { HealthStatus } from '@/types'
import { cn } from '@/lib/utils'

interface SidebarProps {
  className?: string
}

export default function Sidebar({ className }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [health, setHealth] = useState<HealthStatus | null>(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => null)
  }, [])

  return (
    <aside
      className={cn(
        'flex flex-col bg-slate-900/80 border-r border-slate-800/50 backdrop-blur-sm',
        'transition-all duration-300 shrink-0',
        collapsed ? 'w-16' : 'w-64',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-slate-800/50">
        <div className="w-8 h-8 rounded-lg bg-teal-500/20 border border-teal-500/30 
                        flex items-center justify-center shrink-0">
          <GraduationCap className="w-4 h-4 text-teal-400" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="font-bold text-slate-100 text-sm truncate">CampusSaarthi</p>
            <p className="text-xs text-slate-500 truncate">University AI</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-slate-500 hover:text-slate-300 transition-colors shrink-0"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        <NavItem href="/" icon={<Home className="w-4 h-4" />} label="Home" collapsed={collapsed} />
        <NavItem href="/chat" icon={<Zap className="w-4 h-4" />} label="Chat" collapsed={collapsed} active />
        <NavItem href="/admin" icon={<Settings className="w-4 h-4" />} label="Admin" collapsed={collapsed} />
      </nav>

      {/* Model status */}
      {health && (
        <div className={cn(
          'border-t border-slate-800/50 p-3',
          collapsed ? 'flex justify-center' : '',
        )}>
          {collapsed ? (
            <div className={cn(
              'w-2 h-2 rounded-full',
              health.model_available ? 'bg-emerald-400' : 'bg-amber-400',
            )} title={health.model_available ? 'Model available' : 'Model unavailable'} />
          ) : (
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className={cn(
                  'w-1.5 h-1.5 rounded-full',
                  health.model_available ? 'bg-emerald-400' : 'bg-amber-400',
                )} />
                <span className="text-xs text-slate-500">
                  {health.model_available ? 'Model online' : 'Model unavailable'}
                </span>
              </div>
              <p className="text-xs text-slate-600 truncate" title={health.model_id}>
                {health.model_id}
              </p>
              <p className="text-xs text-slate-600">
                {health.indexed_vectors} vectors indexed
              </p>
            </div>
          )}
        </div>
      )}
    </aside>
  )
}

function NavItem({
  href, icon, label, collapsed, active,
}: {
  href: string; icon: React.ReactNode; label: string; collapsed: boolean; active?: boolean
}) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-200 text-sm',
        active
          ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50',
        collapsed && 'justify-center',
      )}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </Link>
  )
}
