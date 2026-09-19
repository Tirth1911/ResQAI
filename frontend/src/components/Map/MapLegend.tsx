import React from 'react';

export function MapLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-[1000] rounded-lg border border-slate-200 bg-white/95 p-3 shadow-md text-xs space-y-2.5 pointer-events-auto max-w-[210px]">
      <div className="font-bold text-slate-900 text-[11px] uppercase tracking-wider border-b border-slate-100 pb-1 flex items-center justify-between">
        <span>Map Legend</span>
        <span className="text-[9px] text-slate-400 font-normal">Real-time</span>
      </div>

      {/* Incidents Severity */}
      <div className="space-y-1">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide block">
          Incident Severity
        </span>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-700 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
            <span className="font-medium text-slate-800">Critical</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500" />
            <span className="font-medium text-slate-800">High</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
            <span className="font-medium text-slate-800">Medium</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span className="font-medium text-slate-800">Low</span>
          </div>
        </div>
      </div>

      {/* Response Resources */}
      <div className="space-y-1 pt-1.5 border-t border-slate-100">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide block">
          Response Units
        </span>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-700 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="text-xs">🚑</span>
            <span className="text-slate-700">Ambulance</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs">🚒</span>
            <span className="text-slate-700">Fire Engine</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs">🚔</span>
            <span className="text-slate-700">Police Unit</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs">🛟</span>
            <span className="text-slate-700">Rescue Team</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapLegend;
