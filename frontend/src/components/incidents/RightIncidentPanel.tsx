'use client';

import React from 'react';
import { Incident, Resource } from '@/types';
import { SeverityBadge } from '@/components/common/SeverityBadge';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Flame,
  MapPin,
  Clock,
  Radio,
  Sparkles,
  Truck,
  Send,
  AlertCircle,
  CheckCircle2,
  FileText
} from 'lucide-react';

interface RightIncidentPanelProps {
  incident: Incident | null;
  resources: Resource[];
  onDispatch: (incident: Incident, resource?: Resource) => void;
  onSelectAnotherIncident?: () => void;
}

export function RightIncidentPanel({
  incident,
  resources,
  onDispatch,
  onSelectAnotherIncident,
}: RightIncidentPanelProps) {
  if (!incident) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center rounded-lg border border-slate-200 bg-white p-6 text-center shadow-xs">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600 mb-3">
          <Flame className="h-6 w-6" />
        </div>
        <h3 className="text-sm font-bold text-slate-900 mb-1">No Incident Selected</h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Select an emergency marker on the map or click an item from the incident list to view AI triage and unit recommendations.
        </p>
      </div>
    );
  }

  // Calculate matching resources
  const availableUnits = resources.filter((r) => r.status === 'AVAILABLE');

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-xs p-4 space-y-4">
      {/* Header: Title & Badges */}
      <div className="border-b border-slate-100 pb-3">
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
              INCIDENT #{incident.incident_id || incident.id || 'INC-001'}
            </span>
            <h2 className="text-base font-bold text-slate-900 leading-snug">
              {incident.title || incident.type?.replace('_', ' ').toUpperCase()}
            </h2>
          </div>
          <SeverityBadge severity={incident.severity} showPulse={false} />
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1.5 text-slate-600">
            <StatusBadge type="priority" value={incident.priority || 'P1'} />
            <StatusBadge type="status" value={incident.status || 'REPORTED'} />
          </div>
          <div className="flex items-center gap-1 text-slate-500 justify-end">
            <Radio className="h-3.5 w-3.5 text-slate-400" />
            <span className="capitalize">{incident.source || 'Citizen Call'}</span>
          </div>
        </div>
      </div>

      {/* Location & Time */}
      <div className="rounded-md bg-slate-50 p-2.5 border border-slate-100 space-y-1.5 text-xs">
        <div className="flex items-center gap-1.5 text-slate-700">
          <MapPin className="h-3.5 w-3.5 text-red-600 shrink-0" />
          <span className="font-medium text-slate-900 truncate">
            {incident.location?.address || incident.address || 'Ahmedabad Emergency Sector'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
          <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
          <span>Reported: {new Date(incident.reported_at || Date.now()).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Description */}
      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
          <FileText className="h-3.5 w-3.5 text-slate-400" />
          <span>Description</span>
        </h4>
        <p className="text-xs text-slate-700 leading-relaxed rounded-md bg-slate-50 p-2.5 border border-slate-100">
          {incident.description || 'Citizen reported active emergency requiring rapid responder deployment.'}
        </p>
      </div>

      {/* AI Triage & Recommended Actions */}
      <div className="rounded-md border border-red-100 bg-red-50/50 p-3 space-y-2">
        <div className="flex items-center gap-1.5 text-red-700 font-bold text-xs">
          <Sparkles className="h-4 w-4 text-red-600" />
          <span>AI Operational Decision Support</span>
        </div>

        {((incident as any).ai_triage?.summary || incident.ai_analysis?.summary) ? (
          <p className="text-xs text-slate-700 leading-normal">
            {(incident as any).ai_triage?.summary || incident.ai_analysis?.summary}
          </p>
        ) : (
          <p className="text-xs text-slate-700 leading-normal">
            High priority emergency flagged by AI triage engine. Immediate dispatch recommended.
          </p>
        )}

        {/* Recommended SOP Checklist */}
        {((incident as any).ai_triage?.recommended_actions || incident.ai_analysis?.immediate_actions)?.length > 0 && (
          <div className="pt-1.5 border-t border-red-100">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide block mb-1">
              Recommended SOP Checklist:
            </span>
            <ul className="space-y-1 text-xs text-slate-800">
              {((incident as any).ai_triage?.recommended_actions || incident.ai_analysis?.immediate_actions || []).slice(0, 3).map((act: string, idx: number) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-red-600 font-bold text-[10px] mt-0.5">•</span>
                  <span>{act}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Recommended Response Units */}
      <div className="space-y-2 pt-1">
        <div className="flex items-center justify-between">
          <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <Truck className="h-3.5 w-3.5 text-red-600" />
            <span>Recommended Response Units</span>
          </h4>
          <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
            {availableUnits.length} Ready
          </span>
        </div>

        <div className="space-y-2">
          {availableUnits.length === 0 ? (
            <div className="rounded-md bg-amber-50 p-2.5 text-center text-xs text-amber-800 border border-amber-200">
              No units currently available for instant dispatch.
            </div>
          ) : (
            availableUnits.slice(0, 3).map((unit) => (
              <div
                key={unit.resource_id || unit.id || unit._id}
                className="flex items-center justify-between rounded-md border border-slate-200 bg-white p-2.5 shadow-2xs hover:border-red-200 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">{unit.name}</span>
                    <StatusBadge type="resource" value={unit.status} />
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                    <span className="capitalize">{(unit.category || unit.type || '').replace('_', ' ')}</span>
                    <span>•</span>
                    <span className="text-slate-600">~1.5 km away</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onDispatch(incident, unit)}
                  className="flex items-center gap-1 rounded bg-red-600 hover:bg-red-700 px-3 py-1.5 text-xs font-bold text-white shadow-2xs transition-colors shrink-0"
                >
                  <Send className="h-3 w-3" />
                  <span>Dispatch</span>
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Action Button */}
      <div className="pt-2 border-t border-slate-100">
        <button
          type="button"
          onClick={() => onDispatch(incident)}
          className="w-full flex items-center justify-center gap-2 rounded-md bg-slate-900 hover:bg-slate-800 py-2 text-xs font-bold text-white shadow-xs transition-colors"
        >
          <Send className="h-3.5 w-3.5 text-red-500" />
          <span>Open Full Fleet Dispatch Matrix</span>
        </button>
      </div>
    </div>
  );
}

export default RightIncidentPanel;
