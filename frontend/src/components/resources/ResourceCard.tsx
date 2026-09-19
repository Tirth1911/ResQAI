import React from 'react';
import { Resource } from '@/types';

interface ResourceCardProps {
  resource: Resource;
  onAssign?: (resource: Resource) => void;
  onRelease?: (resource: Resource) => void;
  onSelect?: (resource: Resource) => void;
  onStatusChange?: (status: any) => void | Promise<void>;
  isSelected?: boolean;
}

export function ResourceCard({
  resource,
  onAssign,
  onRelease,
  onSelect,
  isSelected = false,
}: ResourceCardProps) {
  const categoryIcons: Record<string, string> = {
    AMBULANCE: '🚑',
    FIRE_TRUCK: '🚒',
    POLICE: '🚓',
    RESCUE_BOAT: '🚤',
    HAZMAT: '☣️',
    HEAVY_RESCUE: '🏗️',
    DRONE: '🛸',
    HELICOPTER: '🚁',
    OTHER: '🚚',
  };

  const statusStyles: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    AVAILABLE: {
      bg: 'bg-emerald-950/40',
      text: 'text-emerald-400',
      border: 'border-emerald-800/60',
      dot: 'bg-emerald-400',
    },
    BUSY: {
      bg: 'bg-amber-950/40',
      text: 'text-amber-400',
      border: 'border-amber-800/60',
      dot: 'bg-amber-400',
    },
    EN_ROUTE: {
      bg: 'bg-cyan-950/40',
      text: 'text-cyan-400',
      border: 'border-cyan-800/60',
      dot: 'bg-cyan-400',
    },
    OFFLINE: {
      bg: 'bg-slate-900',
      text: 'text-slate-500',
      border: 'border-slate-800',
      dot: 'bg-slate-600',
    },
    MAINTENANCE: {
      bg: 'bg-rose-950/30',
      text: 'text-rose-400',
      border: 'border-rose-900/40',
      dot: 'bg-rose-500',
    },
  };

  const statusInfo = statusStyles[resource.status] || statusStyles.AVAILABLE;

  return (
    <div
      onClick={() => onSelect?.(resource)}
      className={`rounded-xl border p-3.5 transition-all duration-200 cursor-pointer ${
        isSelected
          ? 'border-cyan-500 bg-slate-800/90 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500'
          : 'border-slate-800 bg-slate-900/70 hover:border-slate-700 hover:bg-slate-800/60'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span className="text-xl" title={resource.category}>
            {categoryIcons[resource.category] || '🚚'}
          </span>
          <div>
            <h4 className="text-sm font-semibold text-white">{resource.name}</h4>
            <span className="font-mono text-[11px] text-slate-400">{resource.resource_id}</span>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono uppercase border font-medium ${statusInfo.bg} ${statusInfo.text} ${statusInfo.border}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${statusInfo.dot}`} />
          {resource.status}
        </span>
      </div>

      {/* Capabilities */}
      <div className="mt-2.5 flex flex-wrap gap-1">
        {resource.capabilities.map((cap, i) => (
          <span
            key={i}
            className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono"
          >
            {cap.replace(/_/g, ' ')}
          </span>
        ))}
      </div>

      {/* Footer / Assignment Info */}
      <div className="mt-3 flex items-center justify-between border-t border-slate-800/60 pt-2 text-xs">
        {resource.current_incident_id ? (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 text-[11px]">Assigned to:</span>
            <span className="font-mono text-cyan-400 text-[11px] font-medium">
              {resource.current_incident_id}
            </span>
          </div>
        ) : (
          <span className="text-[11px] text-emerald-400 font-medium">Ready for deployment</span>
        )}

        <div className="flex items-center gap-1.5">
          {resource.status === 'AVAILABLE' && onAssign && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onAssign(resource);
              }}
              className="text-[11px] font-semibold px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 hover:bg-cyan-900 border border-cyan-700/60 transition-colors"
            >
              Dispatch
            </button>
          )}

          {resource.status !== 'AVAILABLE' && resource.status !== 'OFFLINE' && onRelease && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRelease(resource);
              }}
              className="text-[11px] font-semibold px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors"
            >
              Release
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResourceCard;
