'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ConnectionStatus, WebSocketStatus } from '../common/ConnectionStatus';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types';
import {
  Shield,
  AlertOctagon,
  Truck,
  UserCheck,
  ChevronDown,
  LogOut,
  Lock,
  MapPin,
  Flame,
  Layers,
  BarChart3,
  Sparkles,
  PlusCircle,
  Activity,
  Bell
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
  systemStatus = 'ONLINE',
  activeIncidentsCount = 0,
  criticalIncidentsCount = 0,
  availableResourcesCount = 0,
  unreadAlertsCount = 0,
  onOpenNewIncidentModal,
}: TopHeaderProps) {
  const pathname = usePathname();
  const { user, switchRole, logout } = useAuth();
  const [showRoleDropdown, setShowRoleDropdown] = React.useState(false);

  const currentRole: UserRole = user?.role || 'DISPATCHER';

  const navLinks = [
    { name: 'Incident Map', href: '/dashboard', icon: MapPin },
    { name: 'Incidents', href: '/incidents', icon: Flame, badge: criticalIncidentsCount > 0 ? criticalIncidentsCount : null },
    { name: 'Resources', href: '/resources', icon: Truck },
    { name: 'Deduplication', href: '/simulation', icon: Layers },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Alerts', href: '/alerts', icon: Bell, badge: unreadAlertsCount > 0 ? unreadAlertsCount : null },
    { name: 'Demo Mode', href: '/demo', icon: Sparkles },
  ];

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-4 sm:px-6 shadow-xs backdrop-blur-md">
      {/* LEFT: ResQAI Brand & Subtitle */}
      <div className="flex items-center gap-4 shrink-0">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-600 text-white shadow-xs group-hover:bg-red-700 transition-colors">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-extrabold tracking-tight text-slate-900">
                ResQ<span className="text-red-600">AI</span>
              </span>
              <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-700 uppercase">
                Command
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-500 hidden xl:block leading-tight">
              Emergency Intelligence Platform
            </p>
          </div>
        </Link>
      </div>

      {/* CENTER: Top Navigation Links */}
      <nav className="hidden md:flex items-center gap-1 mx-2">
        {navLinks.map((link) => {
          const isActive =
            pathname === link.href ||
            (link.href === '/dashboard' && (pathname === '/' || pathname === '/map'));
          const Icon = link.icon;

          return (
            <Link
              key={link.name}
              href={link.href}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-red-50 text-red-700 border border-red-200 shadow-xs'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-red-600' : 'text-slate-400'}`} />
              <span>{link.name}</span>
              {link.badge !== null && link.badge !== undefined && (
                <span className="ml-0.5 rounded-full bg-red-600 px-1.5 py-0.2 text-[10px] font-bold text-white leading-none">
                  {link.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* RIGHT: Status Indicators & Operator Controls */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Active Alerts Pill */}
        <div className="hidden xl:flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700">
          <AlertOctagon className="h-3.5 w-3.5 text-red-600" />
          <span className="text-slate-500">Critical:</span>
          <span className="font-bold text-red-700">{criticalIncidentsCount}</span>
        </div>

        {/* Ready Resources Pill */}
        <div className="hidden xl:flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700">
          <Truck className="h-3.5 w-3.5 text-emerald-600" />
          <span className="text-slate-500">Ready:</span>
          <span className="font-bold text-emerald-700">{availableResourcesCount}</span>
        </div>

        {/* Connection Live Badge */}
        <ConnectionStatus status={wsStatus} isConnected={wsConnected} />

        {/* User Role Switcher Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowRoleDropdown(!showRoleDropdown)}
            className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-semibold transition-all ${ROLE_BADGES[currentRole] || ROLE_BADGES.DISPATCHER} hover:bg-opacity-80 cursor-pointer`}
            title="Switch Operator Role"
          >
            <UserCheck className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{currentRole}</span>
            <ChevronDown className="h-3 w-3 opacity-60" />
          </button>

          {showRoleDropdown && (
            <div className="absolute right-0 mt-2 w-56 rounded-lg border border-slate-200 bg-white p-2 shadow-lg z-50 text-xs space-y-1">
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
                  className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs flex items-center justify-between transition-colors ${
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

        {/* Action Button: File Incident */}
        {onOpenNewIncidentModal && (
          <button
            type="button"
            onClick={onOpenNewIncidentModal}
            className="flex items-center gap-1.5 rounded-md bg-red-600 hover:bg-red-700 px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition-colors"
          >
            <PlusCircle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">File Incident</span>
          </button>
        )}
      </div>
    </header>
  );
}

export default TopHeader;
