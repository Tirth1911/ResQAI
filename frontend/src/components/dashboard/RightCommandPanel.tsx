'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Incident, Resource, Hospital } from '@/types';
import { incidentService } from '@/services/incidentService';
import { IncidentDetailPane } from '@/components/IncidentDetail/IncidentDetailPane';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Sparkles,
  Truck,
  Flame,
  Shield,
  Ambulance,
  Building2,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertOctagon,
  ChevronRight,
  Layers,
  Activity,
  X,
} from 'lucide-react';

interface BriefingData {
  timestamp: string;
  total_active_incidents: number;
  severity_counts: Record<string, number>;
  available_resources: number;
  top_priority_incidents: any[];
  briefing_narrative: string;
}

interface RightCommandPanelProps {
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident | null) => void;
  resources: Resource[];
  hospitals: Hospital[];
  onIncidentUpdated: () => void;
  className?: string;
}

export const RightCommandPanel: React.FC<RightCommandPanelProps> = ({
  selectedIncident,
  onSelectIncident,
  resources,
  hospitals,
  onIncidentUpdated,
  className = '',
}) => {
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [activeTab, setActiveTab] = useState<'briefing' | 'detail'>('briefing');

  // Fetch AI Situation Briefing
  const fetchBriefing = useCallback(async () => {
    try {
      setLoadingBriefing(true);
      const data = await incidentService.getBriefing();
      setBriefing(data);
    } catch (err) {
      console.error('Error fetching briefing:', err);
    } finally {
      setLoadingBriefing(false);
    }
  }, []);

  // Refresh briefing on mount and every 60 seconds
  useEffect(() => {
    fetchBriefing();
    const timer = setInterval(() => {
      fetchBriefing();
    }, 60000);
    return () => clearInterval(timer);
  }, [fetchBriefing]);

  // When selected incident changes, switch tab to detail if selected
  useEffect(() => {
    if (selectedIncident) {
      setActiveTab('detail');
    }
  }, [selectedIncident]);

  // Resource status counts by kind: available vs busy
  const resourceStats = useMemo(() => {
    const counts: Record<string, { available: number; busy: number; total: number }> = {
      ambulance: { available: 0, busy: 0, total: 0 },
      fire_truck: { available: 0, busy: 0, total: 0 },
      police: { available: 0, busy: 0, total: 0 },
      rescue: { available: 0, busy: 0, total: 0 },
      hazmat: { available: 0, busy: 0, total: 0 },
      other: { available: 0, busy: 0, total: 0 },
    };

    resources.forEach((r) => {
      const kindRaw = (r.category || r.type || (r as any).kind || '').toLowerCase();
      let key = 'other';
      if (kindRaw.includes('amb') || kindRaw.includes('medic')) key = 'ambulance';
      else if (kindRaw.includes('fire')) key = 'fire_truck';
      else if (kindRaw.includes('police') || kindRaw.includes('patrol')) key = 'police';
      else if (kindRaw.includes('rescue') || kindRaw.includes('boat')) key = 'rescue';
      else if (kindRaw.includes('hazmat')) key = 'hazmat';

      const isAvail = (r.status || '').toUpperCase() === 'AVAILABLE';
      counts[key].total += 1;
      if (isAvail) counts[key].available += 1;
      else counts[key].busy += 1;
    });

    return counts;
  }, [resources]);

  const totalAvailable = resources.filter((r) => (r.status || '').toUpperCase() === 'AVAILABLE').length;

  return (
    <div
      className={`flex flex-col h-full w-full lg:w-[400px] lg:min-w-[400px] lg:max-w-[400px] bg-slate-900 border-l border-slate-800 shadow-2xl overflow-hidden ${className}`}
    >
      {/* Top Tab Bar: Overview vs Incident Detail */}
      <div className="flex items-center justify-between p-2.5 bg-slate-950/80 border-b border-slate-800 shrink-0">
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 rounded-lg border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('briefing')}
            className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'briefing'
                ? 'bg-slate-800 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>Briefing & Fleet</span>
          </button>

          <button
            type="button"
            onClick={() => {
              if (selectedIncident) setActiveTab('detail');
            }}
            disabled={!selectedIncident}
            className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'detail' && selectedIncident
                ? 'bg-red-950 text-red-300 border border-red-800/80 shadow-xs'
                : selectedIncident
                ? 'text-slate-400 hover:text-slate-200'
                : 'text-slate-600 cursor-not-allowed opacity-50'
            }`}
          >
            <Activity className="h-3.5 w-3.5 text-red-500" />
            <span>
              {selectedIncident ? selectedIncident.incident_id : 'Select Incident'}
            </span>
          </button>
        </div>

        {activeTab === 'detail' && selectedIncident && (
          <button
            type="button"
            onClick={() => {
              onSelectIncident(null);
              setActiveTab('briefing');
            }}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Close Incident Detail Panel"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Main Container Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'detail' && selectedIncident ? (
          /* Incident Detail Panel */
          <IncidentDetailPane
            incident={selectedIncident}
            onClose={() => {
              onSelectIncident(null);
              setActiveTab('briefing');
            }}
            onIncidentUpdated={onIncidentUpdated}
          />
        ) : (
          /* Overview: AI Situation Briefing & Resource Status Summary */
          <div className="p-4 space-y-4">
            {/* 1. AI Situation Briefing Card */}
            <div className="rounded-xl border border-purple-900/40 bg-gradient-to-br from-purple-950/30 via-slate-900 to-slate-950 p-4 space-y-3 shadow-xl">
              <div className="flex items-center justify-between border-b border-purple-900/30 pb-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-purple-400" />
                  <h3 className="font-bold text-white text-xs uppercase tracking-wider">
                    AI Situation Briefing
                  </h3>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono text-purple-400">
                    {briefing?.timestamp
                      ? new Date(briefing.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : 'Live'}
                  </span>
                  <button
                    type="button"
                    onClick={fetchBriefing}
                    className="p-1 rounded hover:bg-purple-950 text-purple-400 transition-colors"
                    title="Refresh AI Briefing"
                  >
                    <RefreshCw className={`h-3 w-3 ${loadingBriefing ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>

              {/* Briefing Narrative */}
              <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-950/70 p-3 rounded-lg border border-purple-950">
                {briefing?.briefing_narrative ||
                  'Analyzing live emergency stream across all multi-agency sectors. Normalizing spatiotemporal signals...'}
              </p>

              {/* Severity Counts Badges */}
              <div className="grid grid-cols-4 gap-1.5 pt-1 text-center font-mono text-[11px]">
                <div className="bg-red-950/80 border border-red-800/80 p-1.5 rounded-lg">
                  <div className="text-red-400 font-bold text-sm">
                    {briefing?.severity_counts?.critical || 0}
                  </div>
                  <div className="text-[9px] text-red-500 uppercase">Critical</div>
                </div>
                <div className="bg-orange-950/80 border border-orange-800/80 p-1.5 rounded-lg">
                  <div className="text-orange-400 font-bold text-sm">
                    {briefing?.severity_counts?.high || 0}
                  </div>
                  <div className="text-[9px] text-orange-500 uppercase">High</div>
                </div>
                <div className="bg-amber-950/80 border border-amber-800/80 p-1.5 rounded-lg">
                  <div className="text-amber-400 font-bold text-sm">
                    {briefing?.severity_counts?.medium || 0}
                  </div>
                  <div className="text-[9px] text-amber-500 uppercase">Medium</div>
                </div>
                <div className="bg-sky-950/80 border border-sky-800/80 p-1.5 rounded-lg">
                  <div className="text-sky-400 font-bold text-sm">
                    {briefing?.severity_counts?.low || 0}
                  </div>
                  <div className="text-[9px] text-sky-500 uppercase">Low</div>
                </div>
              </div>

              {/* Top Priority Incidents */}
              {briefing?.top_priority_incidents && briefing.top_priority_incidents.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-purple-900/30">
                  <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wide">
                    Top Priority Incidents:
                  </div>
                  <div className="space-y-1">
                    {briefing.top_priority_incidents.map((topInc: any) => (
                      <div
                        key={topInc.incident_id}
                        onClick={() => {
                          onSelectIncident(topInc);
                          setActiveTab('detail');
                        }}
                        className="p-2 rounded bg-slate-950/80 border border-slate-800/90 hover:border-red-500/60 cursor-pointer flex items-center justify-between text-xs transition-colors"
                      >
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className="font-mono text-red-400 font-bold text-[11px]">
                            {topInc.incident_id}
                          </span>
                          <span className="text-slate-200 truncate">{topInc.title}</span>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 2. Resource Status Summary (counts by kind: available/busy) */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/90 p-4 space-y-3.5 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Truck className="h-4 w-4 text-emerald-400" />
                  <h3 className="font-bold text-white text-xs uppercase tracking-wider">
                    Resource Fleet Status
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                  {totalAvailable} / {resources.length} Ready
                </span>
              </div>

              {/* Fleet Categories Matrix */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {/* Ambulances */}
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span>🚑</span>
                      <span>Ambulances</span>
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {resourceStats.ambulance.available} Avail
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Busy: {resourceStats.ambulance.busy}</span>
                    <span>Total: {resourceStats.ambulance.total}</span>
                  </div>
                </div>

                {/* Fire Trucks */}
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span>🚒</span>
                      <span>Fire Trucks</span>
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {resourceStats.fire_truck.available} Avail
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Busy: {resourceStats.fire_truck.busy}</span>
                    <span>Total: {resourceStats.fire_truck.total}</span>
                  </div>
                </div>

                {/* Police Patrols */}
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span>🚓</span>
                      <span>Police Patrols</span>
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {resourceStats.police.available} Avail
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Busy: {resourceStats.police.busy}</span>
                    <span>Total: {resourceStats.police.total}</span>
                  </div>
                </div>

                {/* Rescue Teams */}
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span>🚤</span>
                      <span>Rescue Teams</span>
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {resourceStats.rescue.available} Avail
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Busy: {resourceStats.rescue.busy}</span>
                    <span>Total: {resourceStats.rescue.total}</span>
                  </div>
                </div>
              </div>

              {/* Emergency Medical Centers / Hospitals */}
              {hospitals.length > 0 && (
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono space-y-1">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-1.5">
                      <Building2 className="h-3.5 w-3.5 text-blue-400" />
                      <span>Trauma Centers & Hospitals</span>
                    </span>
                    <span className="text-blue-400 font-bold">{hospitals.length} Open</span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>
                      Available Beds:{' '}
                      <strong className="text-emerald-400">
                        {hospitals.reduce((acc, h) => acc + (h.available_beds || 0), 0)}
                      </strong>
                    </span>
                    <span>
                      ICU Units:{' '}
                      <strong className="text-cyan-400">
                        {hospitals.reduce((acc, h) => acc + (h.icu_available || 0), 0)}
                      </strong>
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RightCommandPanel;
