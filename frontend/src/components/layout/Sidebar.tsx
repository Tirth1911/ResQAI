'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Flame,
  Truck,
  MapPin,
  BarChart3,
  Bell,
  PlayCircle,
  Settings,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  unreadAlertsCount?: number;
  criticalIncidentsCount?: number;
}

export function Sidebar({
  unreadAlertsCount = 0,
  criticalIncidentsCount = 0,
}: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Judge Demo Mode',
      href: '/demo',
      icon: Sparkles,
      badge: '3-MIN',
      badgeColor: 'bg-emerald-500 text-slate-950 font-black',
    },
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      name: 'Incidents',
      href: '/incidents',
      icon: Flame,
      badge: criticalIncidentsCount > 0 ? `${criticalIncidentsCount}` : undefined,
      badgeColor: 'bg-red-500 text-white',
    },
    {
      name: 'Resources',
      href: '/resources',
      icon: Truck,
    },
    {
      name: 'Map',
      href: '/map',
      icon: MapPin,
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
    },
    {
      name: 'Alerts',
      href: '/alerts',
      icon: Bell,
      badge: unreadAlertsCount > 0 ? `${unreadAlertsCount}` : undefined,
      badgeColor: 'bg-cyan-500 text-slate-950 font-bold',
    },
    {
      name: 'Simulation',
      href: '/simulation',
      icon: PlayCircle,
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
    },
  ];

  return (
    <aside className="flex flex-col w-60 border-r border-slate-800 bg-slate-950/95 p-4 shrink-0 justify-between">
      <div className="space-y-6">
        {/* Navigation Category Label */}
        <div>
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono mb-2">
            Operations
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href === '/dashboard' && pathname === '/');
              const Icon = item.icon;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center justify-between rounded-xl px-3.5 py-2.5 text-xs font-mono font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/80 shadow-md shadow-cyan-950/40'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`h-4 w-4 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-cyan-400' : 'text-slate-500'
                      }`}
                    />
                    <span>{item.name}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono leading-none ${item.badgeColor}`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer System Pill */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-3 text-center text-[10px] font-mono text-slate-400">
        <div className="flex items-center justify-center gap-1.5 text-emerald-400 mb-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold">MongoDB Engine Active</span>
        </div>
        <p className="text-slate-500 text-[9px]">v2.4.0 • Geospatial 2dsphere</p>
      </div>
    </aside>
  );
}

export default Sidebar;
