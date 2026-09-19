import React from 'react';
import { Incident } from '@/types';
import { SeverityBadge } from '../common/SeverityBadge';
import { PriorityBadge } from '../common/PriorityBadge';
import { StatusBadge } from '../StatusBadge';
import { MapPin, Clock, Send, Link as LinkIcon } from 'lucide-react';

interface IncidentCardProps {
  incident: Incident;
  isSelected?: boolean;
  onSelect?: (incident: Incident) => void;
  onQuickAssign?: (incident: Incident) => void;
}

export function IncidentCard({
  incident,
  isSelected = false,
  onSelect,
  onQuickAssign,
}: IncidentCardProps) {
  const isCritical = incident.severity === 'CRITICAL';
  const isHigh = incident.severity === 'HIGH';

  const typeIcons: Record<string, string> = {
    fire: '🔥',
    flood: '🌊',
    road_accident: '🚗',
    medical_emergency: '🚑',
    industrial_hazard: '☢️',
    building_collapse: '🏚️',
    gas_leak: '💨',
    earthquake: '🌋',
    other: '⚠️',
  };

  const icon = typeIcons[incident.type] || '🚨';

  const formatTimeAgo = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const diffMin = Math.floor((Date.now() - date.getTime()) / (1000 * 60));
      if (diffMin < 1) return 'Just now';
      if (diffMin < 60) return `${diffMin}m ago`;
      const diffHours = Math.floor(diffMin / 60);
      return `${diffHours}h ago`;
    } catch {
      return dateStr;
    }
  };

  return (
    <div
      onClick={() => onSelect?.(incident)}
      className={`group relative cursor-pointer rounded-lg border p-3.5 transition-all duration-200 ${
        isSelected
          ? 'border-red-600 bg-red-50/40 shadow-xs ring-1 ring-red-500'
          : isCritical
          ? 'border-red-200 bg-red-50/20 hover:border-red-300 hover:bg-red-50/40'
          : isHigh
          ? 'border-orange-200 bg-orange-50/20 hover:border-orange-300 hover:bg-orange-50/40'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50 shadow-2xs'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-base" title={incident.type}>
            {icon}
          </span>
          <div>
            <h4 className="text-xs font-bold text-slate-900 group-hover:text-red-700 transition-colors line-clamp-1">
              {incident.title}
            </h4>
            <span className="font-mono text-[10px] text-slate-400 font-semibold">{incident.incident_id}</span>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <PriorityBadge priority={incident.priority} />
          <SeverityBadge severity={incident.severity} showPulse={false} />
        </div>
      </div>

      <p className="mt-2 text-xs text-slate-600 line-clamp-2 leading-relaxed">
        {incident.description}
      </p>

      {/* Meta indicators */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-2 text-[11px] text-slate-500">
        <div className="flex items-center gap-1 max-w-[150px] truncate text-slate-700">
          <MapPin className="h-3 w-3 text-red-600 shrink-0" />
          <span className="truncate">{incident.address || 'Location Tagged'}</span>
        </div>

        <div className="flex items-center gap-2">
          {incident.duplicate_count !== undefined && incident.duplicate_count > 0 && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded bg-amber-50 text-amber-800 border border-amber-200 font-mono text-[10px] font-bold">
              <LinkIcon className="h-2.5 w-2.5" /> +{incident.duplicate_count} merged
            </span>
          )}

          <span className="font-medium text-slate-400">{formatTimeAgo(incident.reported_at)}</span>
        </div>
      </div>

      {/* Footer Status & Dispatch action */}
      <div className="mt-2.5 flex items-center justify-between pt-1 border-t border-slate-100">
        <StatusBadge type="status" value={incident.status} />

        {onQuickAssign && incident.status !== 'RESOLVED' && incident.status !== 'CLOSED' && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onQuickAssign(incident);
            }}
            className="text-[11px] font-bold px-2.5 py-1 rounded bg-red-600 text-white hover:bg-red-700 transition-colors flex items-center gap-1 shadow-2xs"
          >
            <Send className="h-3 w-3" />
            <span>Dispatch</span>
          </button>
        )}
      </div>
    </div>
  );
}

export default IncidentCard;
