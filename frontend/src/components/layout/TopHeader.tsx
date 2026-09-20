'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ConnectionStatus, WebSocketStatus } from '../common/ConnectionStatus';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types';
import {
  Shield,
  Truck,
  UserCheck,
  ChevronDown,
  LogOut,
  Lock,
  MapPin,
  Flame,
  Activity,
  Sparkles,
  BarChart3,
  Play,
  Bell,
  Layers
} from 'lucide-react';

interface TopHeaderProps {
  wsConnected?: boolean;
  wsStatus?: WebSocketStatus;
  systemStatus?: string;
  activeIncidentsCount?: number;
  criticalIncidentsCount?: number;
  availableResourcesCount?: number;
  unreadAlertsCount?: number;
  onOpenNewIncidentModal?: () => void;
}

const ROLE_BADGES: Record<UserRole, string> = {
  ADMIN: 'border-red-200 bg-red-50 text-red-700',
  DISPATCHER: 'border-blue-200 bg-blue-50 text-blue-700',
  FIELD_TEAM: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  HOSPITAL: 'border-purple-200 bg-purple-50 text-purple-700',
  VIEWER: 'border-slate-200 bg-slate-100 text-slate-700',
};

export function TopHeader({
  wsConnected,
  wsStatus,
  systemStatus = 'OPERATIONAL',
  activeIncidentsCount = 5,
  criticalIncidentsCount = 1,
  availableResourcesCount = 1,
  unreadAlertsCount = 2,
  onOpenNewIncidentModal,
}: TopHeaderProps) {
  const pathname = usePathname();
  const { user, switchRole, logout } = useAuth();
  const [showRoleDropdown, setShowRoleDropdown] = React.useState(false);

  const currentRole: UserRole = user?.role || 'DISPATCHER';

  const navLinks = [
    { name: 'Tactical Map', href: '/map', icon: MapPin },
    { name: 'Incidents', href: '/incidents', icon: Activity, badge: criticalIncidentsCount > 0 ? criticalIncidentsCount : null },
    { name: 'Fleet', href: '/resources', icon: Truck },
    { name: 'AI Triage', href: '/simulation', icon: Sparkles },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 backdrop-blur-md px-4 sm:px-6 shadow-xs select-none">
      {/* LEFT: ResQAI Brand & Operational Sector Badge */}
      <div className="flex items-center gap-3 shrink-0">
        <Link href="/map" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-600 text-white shadow-sm">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-black tracking-tight text-slate-900 leading-none">
                RESQ<span className="text-red-600">AI</span>
              </span>
              <span className="text-xs font-medium text-slate-500 hidden xl:inline border-l border-slate-200 pl-2">
                Emergency Intelligence Platform
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-semibold text-slate-500 mt-0.5">
              <span>SECTOR: Ahmedabad - Gandhinagar</span>
              <span className="flex items-center gap-1 font-bold text-emerald-600">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                SYSTEM OPERATIONAL
              </span>
            </div>
          </div>
        </Link>
      </div>

      {/* CENTER: Capsule Navigation Pills */}
      <nav className="hidden md:flex items-center gap-1 p-1 bg-slate-100/90 rounded-xl border border-slate-200">
        {navLinks.map((link) => {
          const isActive =
            pathname === link.href ||
            (link.href === '/map' && (pathname === '/' || pathname === '/dashboard' || pathname === '/map'));
          const Icon = link.icon;

          return (
            <Link
              key={link.name}
              href={link.href}
              className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all ${
                isActive
                  ? 'bg-red-50 text-red-700 border border-red-200 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-red-600' : 'text-slate-500'}`} />
              <span>{link.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* RIGHT: Metric Cards & Controls */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Active Incidents Badge */}
        <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs">
          <Flame className="h-4 w-4 text-red-500" />
          <span>Active Incidents:</span>
          <span className="font-extrabold text-slate-900">{activeIncidentsCount}</span>
        </div>

        {/* Available Fleet Badge */}
        <div className="flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-1.5 text-xs font-bold text-emerald-900 shadow-2xs">
          <Truck className="h-4 w-4 text-emerald-600" />
          <span>Available Fleet:</span>
          <span className="font-extrabold text-emerald-700">{availableResourcesCount}</span>
        </div>

        {/* Simulate Link */}
        <Link
          href="/simulation"
          className="hidden sm:flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition-colors"
        >
          <Play className="h-3.5 w-3.5 text-slate-600 fill-slate-600" />
          <span>Simulate</span>
        </Link>

        {/* Notifications Bell */}
        <button
          type="button"
          className="relative p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 shadow-2xs transition-colors"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unreadAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white shadow-xs">
              {unreadAlertsCount}
            </span>
          )}
        </button>

        {/* User Role Switcher Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowRoleDropdown(!showRoleDropdown)}
            className={`flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-semibold transition-all ${ROLE_BADGES[currentRole] || ROLE_BADGES.DISPATCHER} hover:bg-opacity-80 cursor-pointer shadow-xs`}
            title="Switch Operator Role"
          >
            <UserCheck className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{currentRole}</span>
            <ChevronDown className="h-3 w-3 opacity-60" />
          </button>

          {showRoleDropdown && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl z-50 text-xs space-y-1">
              <div className="px-2.5 py-1.5 border-b border-slate-100 text-[11px] text-slate-500 flex justify-between items-center font-medium">
                <span>OPERATOR ROLE</span>
                <span className="text-slate-900 font-bold">{user?.full_name?.split(' ')[0] || 'Dispatcher'}</span>
              </div>

              {(['ADMIN', 'DISPATCHER', 'FIELD_TEAM', 'HOSPITAL', 'VIEWER'] as UserRole[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => {
                    switchRole(r);
                    setShowRoleDropdown(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between transition-colors ${
                    currentRole === r
                      ? 'bg-red-50 text-red-700 font-bold border border-red-200'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <span>{r}</span>
                  {currentRole === r && <span className="text-[10px] text-emerald-600 font-bold">• Active</span>}
                </button>
              ))}

              <div className="border-t border-slate-100 pt-1 flex items-center justify-between">
                <Link
                  href="/login"
                  onClick={() => setShowRoleDropdown(false)}
                  className="px-2 py-1 text-[11px] text-slate-600 hover:text-red-600 flex items-center gap-1"
                >
                  <Lock className="h-3 w-3" />
                  <span>Login Screen</span>
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setShowRoleDropdown(false);
                  }}
                  className="px-2 py-1 text-[11px] text-red-600 hover:underline flex items-center gap-1 font-semibold"
                >
                  <LogOut className="h-3 w-3" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default TopHeader;
