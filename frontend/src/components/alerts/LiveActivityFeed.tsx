import React, { useState } from 'react';
import { AlertNotification } from '@/types';
import { AlertCard } from './AlertCard';
import { Bell } from 'lucide-react';

interface LiveActivityFeedProps {
  alerts: AlertNotification[];
  onMarkRead?: (alert: AlertNotification) => void;
  onMarkAllRead?: () => void;
  onSelectIncident?: (incidentId: string) => void;
  isLoading?: boolean;
}

export function LiveActivityFeed({
  alerts,
  onMarkRead,
  onMarkAllRead,
  onSelectIncident,
  isLoading = false,
}: LiveActivityFeedProps) {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');

  const filteredAlerts = alerts.filter((alert) => {
    if (filterSeverity === 'ALL') return true;
    return alert.severity === filterSeverity;
  });

  const unreadCount = alerts.filter((a) => !a.read).length;
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL' && !a.read).length;

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 p-3">
        <div className="flex items-center gap-2">
          <div className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-600 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-600" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
            Live Alert Stream
          </h3>
          {unreadCount > 0 && (
            <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-red-600 text-white leading-none">
              {unreadCount}
            </span>
          )}
        </div>

        {unreadCount > 0 && onMarkAllRead && (
          <button
            type="button"
            onClick={onMarkAllRead}
            className="text-xs font-semibold text-red-600 hover:underline"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-100 bg-slate-50 p-1.5 text-xs">
        {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => {
          const isActive = filterSeverity === sev;
          return (
            <button
              key={sev}
              type="button"
              onClick={() => setFilterSeverity(sev)}
              className={`flex-1 rounded py-1 text-[11px] font-semibold transition-colors ${
                isActive
                  ? 'bg-white text-slate-900 shadow-2xs border border-slate-200'
                  : 'text-slate-500 hover:text-slate-900'
              } ${
                sev === 'CRITICAL' && criticalCount > 0 ? 'text-red-700 font-bold' : ''
              }`}
            >
              {sev}
              {sev === 'CRITICAL' && criticalCount > 0 && ` (${criticalCount})`}
            </button>
          );
        })}
      </div>

      {/* Feed List */}
      <div className="flex-1 space-y-2 overflow-y-auto p-2.5">
        {isLoading ? (
          <div className="flex h-32 items-center justify-center text-xs text-slate-400 font-medium">
            Scanning emergency telemetry...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center text-center text-xs text-slate-400">
            <Bell className="h-5 w-5 mb-1 text-slate-300" />
            <span>No {filterSeverity !== 'ALL' ? filterSeverity.toLowerCase() : ''} alerts active</span>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.alert_id || alert.id || alert._id}
              alert={alert}
              onMarkRead={onMarkRead}
              onSelectIncident={onSelectIncident}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default LiveActivityFeed;
