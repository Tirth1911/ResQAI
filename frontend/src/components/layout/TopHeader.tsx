'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ConnectionStatus, WebSocketStatus } from '../common/ConnectionStatus';
import { useAuth } from '@/context/AuthContext';
import { useWebSocketContext } from '@/context/WebSocketContext';
import { getApiBaseUrl } from '@/lib/constants';
import { notificationService } from '@/services/notificationService';
import { AlertNotification, UserRole } from '@/types';
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
  Layers,
  Loader2,
  CheckCheck,
  AlertTriangle,
  AlertOctagon,
  Info,
  X,
  ExternalLink,
  RefreshCw,
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
  onSimulate?: () => void;
  isSimulating?: boolean;
}

function formatTimeAgo(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diffSec < 60) return 'Just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return dateStr;
  }
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
  onSimulate,
  isSimulating = false,
}: TopHeaderProps) {
  const pathname = usePathname();
  const { user, switchRole, logout } = useAuth();
  const { status: ctxStatus, isConnected: ctxConnected, lastEvent: ctxLastEvent } = useWebSocketContext();
  const [showRoleDropdown, setShowRoleDropdown] = React.useState(false);
  const [showNotifications, setShowNotifications] = React.useState(false);
  const [notificationsList, setNotificationsList] = React.useState<AlertNotification[]>([]);
  const [loadingNotifications, setLoadingNotifications] = React.useState(false);
  const [filterUnreadOnly, setFilterUnreadOnly] = React.useState(false);
  const notifDropdownRef = React.useRef<HTMLDivElement>(null);
  const [isTriggeringSim, setIsTriggeringSim] = React.useState(false);

  const loadNotifications = React.useCallback(async () => {
    try {
      setLoadingNotifications(true);
      const data = await notificationService.getNotifications({ limit: 50 });
      setNotificationsList(data || []);
    } catch (e) {
      console.error('Error fetching notifications for header bar:', e);
    } finally {
      setLoadingNotifications(false);
    }
  }, []);

  React.useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  // Synchronize with real-time websocket events
  React.useEffect(() => {
    if (ctxLastEvent) {
      loadNotifications();
    }
  }, [ctxLastEvent, loadNotifications]);

  // Click outside to close notification dropdown
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        notifDropdownRef.current &&
        !notifDropdownRef.current.contains(e.target as Node)
      ) {
        setShowNotifications(false);
      }
    };
    if (showNotifications) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotifications]);

  const unreadCount = React.useMemo(() => {
    const fromList = notificationsList.filter((n) => !n.read).length;
    return Math.max(fromList, unreadAlertsCount || 0);
  }, [notificationsList, unreadAlertsCount]);

  const handleMarkAsRead = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notificationService.markAsRead(id);
      setNotificationsList((prev) =>
        prev.map((n) =>
          n.alert_id === id || n.id === id || (n as any)._id === id
            ? { ...n, read: true }
            : n
        )
      );
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotificationsList((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const filteredNotifications = React.useMemo(() => {
    if (filterUnreadOnly) {
      return notificationsList.filter((n) => !n.read);
    }
    return notificationsList;
  }, [notificationsList, filterUnreadOnly]);

  const effectiveStatus: WebSocketStatus = wsStatus || ctxStatus || (wsConnected ?? ctxConnected ? 'CONNECTED' : 'DISCONNECTED');
  const currentRole: UserRole = user?.role || 'DISPATCHER';

  const handleSimulateAction = async () => {
    if (onSimulate) {
      onSimulate();
    }
    try {
      setIsTriggeringSim(true);
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/simulation/simulate-critical`, {
        method: 'POST',
      });
      if (!res.ok) {
        // Fallback to /api/v1 prefix if needed
        await fetch(`${apiBase}/v1/simulation/simulate-critical`, { method: 'POST' });
      }
    } catch (err) {
      console.warn('[TopHeader] Simulation trigger notice:', err);
    } finally {
      setIsTriggeringSim(false);
    }
  };

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
              {effectiveStatus === 'CONNECTED' ? (
                <span className="flex items-center gap-1 font-bold text-emerald-600">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  ● LIVE
                </span>
              ) : effectiveStatus === 'RECONNECTING' ? (
                <span className="flex items-center gap-1 font-bold text-amber-600">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
                  ● RECONNECTING
                </span>
              ) : (
                <span className="flex items-center gap-1 font-bold text-slate-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                  ● OFFLINE
                </span>
              )}
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

        {/* Simulate Button (Triggers authentic Server Pipeline) */}
        <button
          type="button"
          onClick={handleSimulateAction}
          disabled={isTriggeringSim}
          className={`hidden sm:flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-bold shadow-2xs transition-all cursor-pointer disabled:opacity-60 ${
            isSimulating || isTriggeringSim
              ? 'bg-red-50 text-red-700 border-red-300 ring-2 ring-red-400/50 animate-pulse'
              : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
          }`}
          title="Simulate New Critical Incident via Server Pipeline"
        >
          {isTriggeringSim ? (
            <Loader2 className="h-3.5 w-3.5 text-red-600 animate-spin" />
          ) : (
            <Play className={`h-3.5 w-3.5 ${isSimulating ? 'text-red-600 fill-red-600' : 'text-slate-600 fill-slate-600'}`} />
          )}
          <span>{isTriggeringSim ? 'Injecting...' : isSimulating ? 'Simulating...' : 'Simulate'}</span>
        </button>

        {/* Notifications Bar & Dropdown */}
        <div className="relative" ref={notifDropdownRef}>
          <button
            type="button"
            onClick={() => {
              setShowNotifications((prev) => !prev);
              setShowRoleDropdown(false);
            }}
            className={`relative p-2 rounded-xl border transition-all cursor-pointer ${
              showNotifications
                ? 'border-red-300 bg-red-50 text-red-700 shadow-sm'
                : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-600 shadow-2xs'
            }`}
            title="Operational Notifications Bar"
            aria-label="Open notifications bar"
          >
            <Bell className={`h-4 w-4 ${unreadCount > 0 ? 'text-slate-800' : ''}`} />
            {unreadCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 flex h-4 min-w-4 px-1 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white shadow-sm ring-2 ring-white">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2.5 w-[380px] sm:w-[420px] rounded-2xl border border-slate-200 bg-white shadow-2xl z-50 overflow-hidden text-xs flex flex-col max-h-[540px] animate-in fade-in slide-in-from-top-2 duration-150">
              {/* Header */}
              <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-red-100 text-red-600">
                    <Bell className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Notifications Bar</h4>
                    <span className="text-[11px] text-slate-500 font-medium">
                      {unreadCount} unread alert{unreadCount === 1 ? '' : 's'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      onClick={handleMarkAllRead}
                      className="px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-white rounded-lg border border-slate-200 bg-white/80 transition-colors flex items-center gap-1 cursor-pointer"
                      title="Mark all as read"
                    >
                      <CheckCheck className="h-3.5 w-3.5 text-emerald-600" />
                      <span>Mark all read</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowNotifications(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Filter Tabs */}
              <div className="px-3.5 py-2 border-b border-slate-100 bg-white flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg font-medium">
                  <button
                    type="button"
                    onClick={() => setFilterUnreadOnly(false)}
                    className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                      !filterUnreadOnly
                        ? 'bg-white text-slate-900 font-bold shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    All ({notificationsList.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setFilterUnreadOnly(true)}
                    className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                      filterUnreadOnly
                        ? 'bg-white text-slate-900 font-bold shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Unread Only ({notificationsList.filter((n) => !n.read).length})
                  </button>
                </div>

                <button
                  type="button"
                  onClick={loadNotifications}
                  className="text-slate-400 hover:text-slate-600 p-1 rounded transition-colors cursor-pointer"
                  title="Refresh notifications"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${loadingNotifications ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {/* Notification List Body */}
              <div className="overflow-y-auto flex-1 divide-y divide-slate-100 max-h-[380px]">
                {filteredNotifications.length === 0 ? (
                  <div className="py-12 px-4 text-center">
                    <div className="mx-auto w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-2">
                      <Bell className="h-5 w-5 opacity-40" />
                    </div>
                    <p className="text-slate-700 font-bold text-xs">No Notifications</p>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      {filterUnreadOnly ? 'All notifications have been read.' : 'No operational alerts logged yet.'}
                    </p>
                  </div>
                ) : (
                  filteredNotifications.map((notif) => {
                    const id = notif.alert_id || notif.id || (notif as any)._id;
                    const sev = (notif.severity || 'INFO').toUpperCase();
                    const isUnread = !notif.read;

                    let icon = <Info className="h-4 w-4 text-blue-500 shrink-0" />;
                    let badgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
                    if (sev === 'CRITICAL') {
                      icon = <AlertOctagon className="h-4 w-4 text-red-500 shrink-0" />;
                      badgeClass = 'bg-red-50 text-red-700 border-red-200';
                    } else if (sev === 'WARNING' || notif.type?.includes('SHORTAGE')) {
                      icon = <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />;
                      badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
                    } else if (notif.type?.includes('DISPATCH') || notif.message?.includes('dispatched')) {
                      icon = <Truck className="h-4 w-4 text-emerald-500 shrink-0" />;
                      badgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                    }

                    return (
                      <div
                        key={id || Math.random()}
                        className={`p-3 transition-colors flex items-start gap-2.5 ${
                          isUnread ? 'bg-slate-50/90 hover:bg-slate-100/80' : 'bg-white hover:bg-slate-50/60'
                        }`}
                      >
                        <div className="mt-0.5 shrink-0">{icon}</div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1.5 mb-1">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${badgeClass}`}>
                              {notif.type || (notif as any).subject || notif.severity || 'ALERT'}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {formatTimeAgo(notif.created_at)}
                            </span>
                          </div>

                          <p className={`text-xs leading-snug ${isUnread ? 'font-semibold text-slate-800' : 'text-slate-600'}`}>
                            {(notif as any).message || (notif as any).body || (notif as any).description || (notif as any).details || (notif as any).subject || 'Operational status update'}
                          </p>

                          <div className="mt-2 flex items-center justify-between pt-1">
                            {notif.incident_id ? (
                              <Link
                                href={`/map?incident=${notif.incident_id}`}
                                onClick={() => setShowNotifications(false)}
                                className="text-[11px] font-bold text-red-600 hover:text-red-700 flex items-center gap-1"
                              >
                                <span>View Incident ({notif.incident_id})</span>
                                <ExternalLink className="h-3 w-3" />
                              </Link>
                            ) : (
                              <span />
                            )}

                            {isUnread && (
                              <button
                                type="button"
                                onClick={(e) => handleMarkAsRead(id, e)}
                                className="text-[10px] font-semibold text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 px-1.5 py-0.5 rounded transition-colors cursor-pointer"
                              >
                                Mark read
                              </button>
                            )}
                          </div>
                        </div>

                        {isUnread && (
                          <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0 mt-1.5" />
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* Footer */}
              <div className="p-2.5 border-t border-slate-100 bg-slate-50 text-center">
                <Link
                  href="/alerts"
                  onClick={() => setShowNotifications(false)}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-red-600 transition-colors"
                >
                  <span>View All Alerts & Operational Logs</span>
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </div>
            </div>
          )}
        </div>

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
