import React from 'react';
import { AlertNotification } from '@/types';
import { ArrowRight, Check } from 'lucide-react';

interface AlertCardProps {
  alert: AlertNotification;
  onMarkRead?: (alert: AlertNotification) => void;
  onSelectIncident?: (incidentId: string) => void;
}

export function AlertCard({ alert, onMarkRead, onSelectIncident }: AlertCardProps) {
  const isCritical = alert.severity === 'CRITICAL';
  const isWarning = alert.severity === 'WARNING';

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div
      className={`relative rounded-lg border p-3.5 transition-all duration-200 ${
        !alert.read
          ? isCritical
            ? 'border-red-200 bg-red-50/60 shadow-2xs'
            : isWarning
            ? 'border-amber-200 bg-amber-50/60 shadow-2xs'
            : 'border-blue-200 bg-blue-50/60 shadow-2xs'
          : 'border-slate-200 bg-white opacity-80'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-base">
            {isCritical ? '🚨' : isWarning ? '⚠️' : 'ℹ️'}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                  isCritical
                    ? 'bg-red-100 text-red-700 border-red-200'
                    : isWarning
                    ? 'bg-amber-100 text-amber-700 border-amber-200'
                    : 'bg-blue-100 text-blue-700 border-blue-200'
                }`}
              >
                {alert.type.replace(/_/g, ' ')}
              </span>
              {!alert.read && (
                <span className="h-1.5 w-1.5 rounded-full bg-red-600 animate-pulse" />
              )}
            </div>
          </div>
        </div>

        <span className="text-[11px] font-semibold text-slate-400">
          {formatTime(alert.created_at)}
        </span>
      </div>

      <p className="mt-2 text-xs text-slate-800 font-medium leading-relaxed">
        {alert.message}
      </p>

      <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
        {alert.incident_id ? (
          <button
            type="button"
            onClick={() => onSelectIncident?.(alert.incident_id!)}
            className="font-bold text-red-600 hover:text-red-700 hover:underline flex items-center gap-1 text-xs"
          >
            <span>Target Incident: #{alert.incident_id}</span>
            <ArrowRight className="h-3 w-3" />
          </button>
        ) : (
          <span className="text-slate-400 font-mono text-[11px]">#{alert.alert_id}</span>
        )}

        {!alert.read && onMarkRead && (
          <button
            type="button"
            onClick={() => onMarkRead(alert)}
            className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 px-2 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-colors flex items-center gap-1"
          >
            <Check className="h-3 w-3 text-emerald-600" />
            <span>Mark Read</span>
          </button>
        )}
      </div>
    </div>
  );
}

export default AlertCard;
