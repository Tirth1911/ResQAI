'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Incident, Resource, Hospital } from '@/types';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Sparkles,
  Truck,
  Building2,
  RefreshCw,
  MapPin,
  Send,
  Loader2,
  X,
  Navigation,
  Clock,
  Users,
  ChevronDown,
  Activity,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

interface RightCommandPanelProps {
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident | null) => void;
  resources: Resource[];
  hospitals: Hospital[];
  onIncidentUpdated: () => void;
  className?: string;
}

function getMatchColor(score: number): string {
  if (score >= 0.7) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (score >= 0.5) return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-red-700 bg-red-50 border-red-200';
}

function getSeverityColor(severity: string): string {
  const s = severity?.toUpperCase();
  if (s === 'CRITICAL') return 'text-red-600 bg-red-50 border-red-200';
  if (s === 'HIGH') return 'text-orange-600 bg-orange-50 border-orange-200';
  if (s === 'MEDIUM') return 'text-amber-600 bg-amber-50 border-amber-200';
  return 'text-sky-600 bg-sky-50 border-sky-200';
}

function getPriorityScore(priority: string): number {
  if (priority === 'P1') return 100;
  if (priority === 'P2') return 85;
  if (priority === 'P3') return 60;
  return 35;
}

export const RightCommandPanel: React.FC<RightCommandPanelProps> = ({
  selectedIncident,
  onSelectIncident,
  resources,
  hospitals,
  onIncidentUpdated,
  className = '',
}) => {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [dispatchingId, setDispatchingId] = useState<string | null>(null);
  const [dispatched, setDispatched] = useState<Set<string>>(new Set());

  // When incident is selected, fetch recommendations
  useEffect(() => {
    if (selectedIncident?.incident_id) {
      setDispatched(new Set(selectedIncident.assigned_resources || []));
      const loadRecs = async () => {
        try {
          setLoadingRecs(true);
          const res = await resourceService.getRecommendations(selectedIncident.incident_id, 6);
          setRecommendations(res.recommendations || []);
        } catch (e) {
          console.error('Error loading recommendations:', e);
          setRecommendations([]);
        } finally {
          setLoadingRecs(false);
        }
      };
      loadRecs();
    } else {
      setRecommendations([]);
    }
  }, [selectedIncident?.incident_id]);

  // Dispatch resource
  const handleDispatch = async (rec: any) => {
    if (!selectedIncident) return;
    try {
      setDispatchingId(rec.resource_id);
      await incidentService.assignResource(selectedIncident.incident_id, rec.resource_id);
      setDispatched((prev) => new Set([...prev, rec.resource_id]));
      onIncidentUpdated();
      // Refresh recommendations
      const res = await resourceService.getRecommendations(selectedIncident.incident_id, 6);
      setRecommendations(res.recommendations || []);
    } catch (err) {
      console.error('Dispatch error:', err);
    } finally {
      setDispatchingId(null);
    }
  };

  const priorityScore = selectedIncident ? getPriorityScore(selectedIncident.priority) : 0;
  const availableRecs = recommendations.filter((r) => !dispatched.has(r.resource_id));

  return (
    <div
      className={`flex flex-col h-full bg-white border-l border-slate-200 shadow-sm overflow-hidden ${className}`}
    >
      {/* ─── Panel Header ─────────────────────────────────── */}
      <div className="flex-none px-5 py-4 border-b border-slate-100 bg-white">
        {selectedIncident ? (
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-[11px] font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200 tracking-wider">
                {selectedIncident.incident_id?.toUpperCase()}
              </span>
              <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${getSeverityColor(selectedIncident.severity)}`}>
                {selectedIncident.severity === 'CRITICAL' ? 'Critical Priority' :
                 selectedIncident.severity === 'HIGH' ? 'High Priority' :
                 selectedIncident.severity === 'MEDIUM' ? 'Medium Priority' : 'Low Priority'}
              </span>
            </div>
            <button
              type="button"
              onClick={() => onSelectIncident(null)}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
              title="Close Panel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <span className="font-bold text-slate-800 text-sm">Command Intel</span>
          </div>
        )}
      </div>

      {/* ─── Main Scrollable Content ───────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {selectedIncident ? (
          <div className="p-5 space-y-4">
            {/* Incident Title */}
            <h2 className="text-[15px] font-bold text-slate-900 leading-snug">
              {selectedIncident.title}
            </h2>

            {/* LOCATION */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-1">
              <p className="text-[9px] uppercase font-black tracking-widest text-slate-400 mb-1.5">
                LOCATION
              </p>
              <div className="flex items-start gap-2 text-slate-700 font-semibold text-xs">
                <MapPin className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />
                <span>{selectedIncident.address || 'Ahmedabad, Gujarat'}</span>
              </div>
            </div>

            {/* AI TRIAGE ANALYSIS */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-3">
              <p className="text-[9px] uppercase font-black tracking-widest text-slate-400">
                AI TRIAGE ANALYSIS
              </p>
              <p className="text-xs text-slate-700 leading-relaxed">
                {selectedIncident.ai_analysis?.summary ||
                  selectedIncident.ai_analysis?.reasoning ||
                  selectedIncident.description}
              </p>

              {/* Priority Score Bar */}
              <div className="border-t border-slate-200/60 pt-3 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-500 font-medium">Priority Score</span>
                  <span className="font-mono text-red-600 font-black tabular-nums">
                    {priorityScore} / 100
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-red-500 to-red-600 transition-all duration-700 ease-out"
                    style={{ width: `${priorityScore}%` }}
                  />
                </div>
              </div>
            </div>

            {/* ─── RECOMMENDED RESPONSE UNITS ────────────────── */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-[10px] uppercase font-black tracking-widest text-slate-600">
                  RECOMMENDED RESPONSE UNITS
                </p>
                {availableRecs.length > 0 && (
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                    {availableRecs.length} available
                  </span>
                )}
              </div>

              {loadingRecs ? (
                <div className="flex flex-col items-center gap-3 py-10 text-slate-400">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-[11px] font-mono">Calculating nearest units...</span>
                </div>
              ) : availableRecs.length === 0 ? (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-center">
                  <CheckCircle className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
                  <p className="text-xs text-slate-500 font-medium">
                    {recommendations.length > 0
                      ? 'All recommended units have been dispatched.'
                      : 'No available response units matching criteria.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {availableRecs.map((rec) => {
                    const isDispatching = dispatchingId === rec.resource_id;
                    const matchScore = rec.score ?? 0.362;
                    const matchPct = (matchScore * 100).toFixed(1);
                    const matchColorClass = getMatchColor(matchScore);
                    const distKm = rec.distance_km ?? rec.distance ?? '—';
                    const etaMin = rec.eta_min ?? rec.eta ?? '—';
                    const capacity = rec.capacity ?? rec.max_capacity ?? 4;

                    return (
                      <div
                        key={rec.resource_id}
                        className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-150"
                      >
                        {/* Unit Name & Match Score */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-bold text-slate-900 text-sm leading-tight">
                              {rec.name || rec.resource_id}
                            </h4>
                            <p className="text-[11px] text-slate-400 mt-0.5 font-medium truncate">
                              {rec.location_name || rec.address || '—'}
                            </p>
                          </div>
                          <span
                            className={`text-[11px] font-black px-2.5 py-1 rounded-full border shrink-0 ${matchColorClass}`}
                          >
                            {matchPct}% MATCH
                          </span>
                        </div>

                        {/* Distance / ETA / Capacity Row */}
                        <div className="flex items-center justify-between text-[11px] font-medium text-slate-600 bg-slate-50 px-3 py-2.5 rounded-lg border border-slate-100">
                          <span className="flex items-center gap-1.5">
                            <MapPin className="h-3 w-3 text-red-400 shrink-0" />
                            <span className="tabular-nums">
                              {typeof distKm === 'number' ? `${distKm.toFixed(2)} km` : distKm} away
                            </span>
                          </span>
                          <span className="text-slate-300">|</span>
                          <span className="flex items-center gap-1.5">
                            <Clock className="h-3 w-3 text-slate-400 shrink-0" />
                            <span className="tabular-nums">
                              ETA {typeof etaMin === 'number' ? Math.round(etaMin) : etaMin} min
                            </span>
                          </span>
                          <span className="text-slate-300">|</span>
                          <span className="flex items-center gap-1.5">
                            <Users className="h-3 w-3 text-slate-400 shrink-0" />
                            <span>Capacity {capacity}</span>
                          </span>
                        </div>

                        {/* Reason + Dispatch Button */}
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-[11px] text-slate-400 font-medium flex-1 min-w-0 leading-relaxed line-clamp-2">
                            {rec.reason || rec.reason_short || 'General emergency response asset'}
                          </p>
                          <button
                            type="button"
                            onClick={() => handleDispatch(rec)}
                            disabled={isDispatching}
                            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#8B1E1E] hover:bg-[#721818] active:scale-95 text-white font-bold rounded-lg text-[11px] transition-all shadow-sm shrink-0 disabled:opacity-60"
                          >
                            {isDispatching ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Send className="h-3 w-3 rotate-45" />
                            )}
                            <span>Dispatch Unit</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Dispatched units count */}
            {dispatched.size > 0 && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 flex items-center gap-2 text-xs text-emerald-800 font-semibold">
                <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
                <span>{dispatched.size} unit{dispatched.size > 1 ? 's' : ''} dispatched to this incident</span>
              </div>
            )}
          </div>
        ) : (
          /* ─── No Incident Selected: Fleet Overview ─────── */
          <FleetOverview resources={resources} hospitals={hospitals} />
        )}
      </div>
    </div>
  );
};

// ─── Fleet Overview (shown when no incident selected) ─────────────────────────
function FleetOverview({ resources, hospitals }: { resources: Resource[]; hospitals: Hospital[] }) {
  const counts = useMemo(() => {
    const c = {
      ambulance: { available: 0, busy: 0, total: 0 },
      fire_truck: { available: 0, busy: 0, total: 0 },
      police: { available: 0, busy: 0, total: 0 },
      rescue: { available: 0, busy: 0, total: 0 },
      hazmat: { available: 0, busy: 0, total: 0 },
      drone: { available: 0, busy: 0, total: 0 },
      other: { available: 0, busy: 0, total: 0 },
    };
    resources.forEach((r) => {
      const k = (r.category || r.type || (r as any).kind || '').toLowerCase();
      let key: keyof typeof c = 'other';
      if (k.includes('amb') || k.includes('medic')) key = 'ambulance';
      else if (k.includes('fire')) key = 'fire_truck';
      else if (k.includes('police') || k.includes('patrol')) key = 'police';
      else if (k.includes('rescue') || k.includes('boat')) key = 'rescue';
      else if (k.includes('hazmat')) key = 'hazmat';
      else if (k.includes('drone')) key = 'drone';
      const isAvail = (r.status || '').toUpperCase() === 'AVAILABLE';
      c[key].total += 1;
      if (isAvail) c[key].available += 1;
      else c[key].busy += 1;
    });
    return c;
  }, [resources]);

  const totalAvail = resources.filter((r) => (r.status || '').toUpperCase() === 'AVAILABLE').length;

  const fleetRows = [
    { key: 'ambulance', emoji: '🚑', label: 'Ambulances' },
    { key: 'fire_truck', emoji: '🚒', label: 'Fire Trucks' },
    { key: 'police', emoji: '🚓', label: 'Police Patrols' },
    { key: 'rescue', emoji: '🚤', label: 'Rescue Teams' },
    { key: 'hazmat', emoji: '☣️', label: 'HAZMAT Units' },
    { key: 'drone', emoji: '🛸', label: 'Drone Recon' },
  ] as const;

  return (
    <div className="p-5 space-y-4">
      {/* Header stat */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Truck className="h-4 w-4 text-emerald-600" />
          <span className="font-bold text-slate-800 text-sm">Fleet Status</span>
        </div>
        <span className="text-xs font-bold font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
          {totalAvail} / {resources.length} Ready
        </span>
      </div>

      {/* Fleet grid */}
      <div className="grid grid-cols-2 gap-2.5">
        {fleetRows.map(({ key, emoji, label }) => {
          const stat = counts[key];
          if (stat.total === 0) return null;
          return (
            <div key={key} className="rounded-xl border border-slate-200 bg-white p-3 space-y-1.5 shadow-sm">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <span>{emoji}</span>
                  <span className="text-[11px]">{label}</span>
                </span>
                <span className={`text-[10px] font-bold ${stat.available > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {stat.available} avail
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{ width: stat.total > 0 ? `${(stat.available / stat.total) * 100}%` : '0%' }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>Busy: {stat.busy}</span>
                <span>Total: {stat.total}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Hospitals summary */}
      {hospitals.length > 0 && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-blue-800 font-bold text-xs">
              <Building2 className="h-3.5 w-3.5 text-blue-600" />
              <span>Trauma Centers</span>
            </div>
            <span className="text-[10px] font-bold text-blue-700">{hospitals.length} Open</span>
          </div>
          <div className="flex justify-between text-[10px] text-blue-700 font-mono font-medium">
            <span>
              Beds:{' '}
              <strong className="text-emerald-700">
                {hospitals.reduce((acc, h) => acc + ((h as any).emergency_beds_available || h.available_beds || 0), 0)}
              </strong>
            </span>
            <span>
              ICU:{' '}
              <strong className="text-blue-900">
                {hospitals.reduce((acc, h) => acc + ((h as any).icu_beds_available || h.icu_available || 0), 0)}
              </strong>
            </span>
          </div>
        </div>
      )}

      {/* Select incident hint */}
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-4 text-center space-y-1">
        <Activity className="h-5 w-5 text-slate-400 mx-auto" />
        <p className="text-[11px] text-slate-400 font-medium">
          Click any incident marker on the map to see AI-recommended response units
        </p>
      </div>
    </div>
  );
}

export default RightCommandPanel;
