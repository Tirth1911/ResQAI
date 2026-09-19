'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Incident } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Search,
  Flame,
  AlertTriangle,
  Car,
  Droplets,
  HeartPulse,
  Factory,
  Wind,
  Landmark,
  Layers,
  Truck,
  Clock,
  Filter,
  CheckCircle2,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';

interface IncidentQueueProps {
  incidents: Incident[];
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident) => void;
  onOpenReportModal?: () => void;
  className?: string;
}

// Helper to format live time-ago
function formatTimeAgo(dateStr?: string): string {
  if (!dateStr) return 'Just now';
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 15) return 'Just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

// Lucide icon helper for incident type
export function getIncidentTypeIcon(type?: string) {
  const t = (type || '').toLowerCase();
  if (t.includes('fire')) return <Flame className="h-4 w-4 text-red-500" />;
  if (t.includes('road') || t.includes('accident') || t.includes('traffic'))
    return <Car className="h-4 w-4 text-amber-500" />;
  if (t.includes('flood') || t.includes('water'))
    return <Droplets className="h-4 w-4 text-cyan-500" />;
  if (t.includes('medical') || t.includes('health'))
    return <HeartPulse className="h-4 w-4 text-rose-500" />;
  if (t.includes('industrial') || t.includes('hazard'))
    return <Factory className="h-4 w-4 text-orange-500" />;
  if (t.includes('gas') || t.includes('leak'))
    return <Wind className="h-4 w-4 text-purple-500" />;
  if (t.includes('collapse') || t.includes('building') || t.includes('earthquake'))
    return <Landmark className="h-4 w-4 text-yellow-600" />;
  return <AlertTriangle className="h-4 w-4 text-slate-400" />;
}

const PRIORITY_ORDER: Record<string, number> = {
  P1: 1,
  P2: 2,
  P3: 3,
  P4: 4,
};

const SEVERITY_ORDER: Record<string, number> = {
  CRITICAL: 1,
  HIGH: 2,
  MEDIUM: 3,
  LOW: 4,
};

export const IncidentQueue: React.FC<IncidentQueueProps> = ({
  incidents,
  selectedIncident,
  onSelectIncident,
  onOpenReportModal,
  className = '',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeOnly, setActiveOnly] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [showFilters, setShowFilters] = useState(false);

  // Live timer tick to update time-ago every 15 seconds
  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 15000);
    return () => clearInterval(timer);
  }, []);

  // Filter and sort incidents: priority first (P1 -> P4), then newest first
  const sortedAndFiltered = useMemo(() => {
    return incidents
      .filter((inc) => {
        // Active only toggle
        if (activeOnly && ['RESOLVED', 'CLOSED'].includes(inc.status?.toUpperCase())) {
          return false;
        }

        // Severity filter
        if (selectedSeverity !== 'ALL' && inc.severity?.toUpperCase() !== selectedSeverity) {
          return false;
        }

        // Type filter
        if (selectedType !== 'ALL' && inc.type?.toLowerCase() !== selectedType.toLowerCase()) {
          return false;
        }

        // Status filter
        if (selectedStatus !== 'ALL' && inc.status?.toUpperCase() !== selectedStatus) {
          return false;
        }

        // Text search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchId = inc.incident_id?.toLowerCase().includes(q);
          const matchTitle = inc.title?.toLowerCase().includes(q);
          const matchDesc = inc.description?.toLowerCase().includes(q);
          const matchAddr = inc.address?.toLowerCase().includes(q);
          const matchType = inc.type?.toLowerCase().includes(q);
          if (!matchId && !matchTitle && !matchDesc && !matchAddr && !matchType) {
            return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        const pA = PRIORITY_ORDER[a.priority?.toUpperCase()] || SEVERITY_ORDER[a.severity?.toUpperCase()] || 5;
        const pB = PRIORITY_ORDER[b.priority?.toUpperCase()] || SEVERITY_ORDER[b.severity?.toUpperCase()] || 5;
        if (pA !== pB) return pA - pB;

        const timeA = new Date(a.reported_at || a.updated_at || 0).getTime();
        const timeB = new Date(b.reported_at || b.updated_at || 0).getTime();
        return timeB - timeA;
      });
  }, [incidents, activeOnly, selectedSeverity, selectedType, selectedStatus, searchQuery]);

  const activeCount = incidents.filter(
    (i) => !['RESOLVED', 'CLOSED'].includes(i.status?.toUpperCase())
  ).length;

  const hasFilterActive =
    selectedSeverity !== 'ALL' || selectedType !== 'ALL' || selectedStatus !== 'ALL';

  return (
    <div
      className={`flex flex-col h-full w-full lg:w-[360px] lg:min-w-[360px] lg:max-w-[360px] bg-slate-900 border-r border-slate-800 shadow-xl overflow-hidden ${className}`}
    >
      {/* Top Header */}
      <div className="p-3.5 border-b border-slate-800 bg-slate-950/70 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Flame className="h-4 w-4 text-red-500 animate-pulse" />
            <h2 className="font-bold text-white text-sm tracking-tight">Incident Queue</h2>
            <span className="text-[10px] font-mono bg-red-950 text-red-400 border border-red-800 px-2 py-0.5 rounded-full font-bold">
              {sortedAndFiltered.length}
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`p-1.5 rounded text-xs transition-colors flex items-center gap-1 ${
                hasFilterActive || showFilters
                  ? 'bg-red-950 text-red-300 border border-red-800'
                  : 'text-slate-400 hover:text-white bg-slate-800/80'
              }`}
              title="Filter Incident Queue"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
            </button>

            {onOpenReportModal && (
              <button
                type="button"
                onClick={onOpenReportModal}
                className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-semibold shadow-xs transition-colors"
              >
                + Report
              </button>
            )}
          </div>
        </div>

        {/* Search & Active Only Toggle Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search incidents..."
              className="w-full pl-8 pr-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-md text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-red-500"
            />
          </div>

          {/* Active Only Toggle Switch */}
          <label className="flex items-center space-x-1.5 cursor-pointer text-[11px] font-medium text-slate-300 shrink-0 bg-slate-950 border border-slate-800 px-2 py-1.5 rounded-md">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-red-600 focus:ring-0 h-3.5 w-3.5"
            />
            <span>Active Only</span>
          </label>
        </div>

        {/* Expandable Advanced Filter Drawer */}
        {showFilters && (
          <div className="pt-2 border-t border-slate-800/80 space-y-2 text-[11px] font-mono">
            <div className="grid grid-cols-3 gap-1.5">
              {/* Severity */}
              <div>
                <label className="text-[9px] uppercase font-bold text-slate-400 block mb-0.5">
                  Severity
                </label>
                <select
                  value={selectedSeverity}
                  onChange={(e) => setSelectedSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-slate-300 text-[10px] focus:outline-none"
                >
                  <option value="ALL">All</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              {/* Type */}
              <div>
                <label className="text-[9px] uppercase font-bold text-slate-400 block mb-0.5">
                  Type
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-slate-300 text-[10px] focus:outline-none"
                >
                  <option value="ALL">All Types</option>
                  <option value="fire">Fire</option>
                  <option value="flood">Flood</option>
                  <option value="road_accident">Accident</option>
                  <option value="medical_emergency">Medical</option>
                  <option value="industrial_hazard">Industrial</option>
                  <option value="building_collapse">Collapse</option>
                  <option value="gas_leak">Gas Leak</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="text-[9px] uppercase font-bold text-slate-400 block mb-0.5">
                  Status
                </label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-slate-300 text-[10px] focus:outline-none"
                >
                  <option value="ALL">All Status</option>
                  <option value="REPORTED">Reported</option>
                  <option value="VERIFIED">Verified</option>
                  <option value="DISPATCHED">Dispatched</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>
            </div>

            {hasFilterActive && (
              <button
                type="button"
                onClick={() => {
                  setSelectedSeverity('ALL');
                  setSelectedType('ALL');
                  setSelectedStatus('ALL');
                }}
                className="text-[10px] text-red-400 hover:underline flex items-center gap-1"
              >
                <span>Reset filters</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Incident Cards Scrollable List */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {sortedAndFiltered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center p-4">
            <AlertTriangle className="h-6 w-6 text-slate-600 mb-2" />
            <p className="text-xs text-slate-400 font-medium">No incidents match the active filter.</p>
            <p className="text-[11px] text-slate-600 mt-1">
              {activeOnly ? 'Turn off "Active Only" to view resolved cases.' : 'Try adjusting search terms.'}
            </p>
          </div>
        ) : (
          sortedAndFiltered.map((incident) => {
            const isSelected = selectedIncident?.incident_id === incident.incident_id;
            const reportCount =
              (incident as any).report_count ||
              incident.duplicate_count ||
              incident.duplicate_reports?.length ||
              1;
            const assignedCount = incident.assigned_resources?.length || 0;
            const timeAgo = formatTimeAgo(incident.reported_at || incident.updated_at);

            // Is incident newly created (less than 20 seconds ago)?
            const isBrandNew =
              Date.now() - new Date(incident.reported_at || incident.updated_at || 0).getTime() < 20000;

            return (
              <div
                key={incident.incident_id || incident._id}
                onClick={() => onSelectIncident(incident)}
                className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer space-y-2 relative ${
                  isBrandNew ? 'new-incident-anim' : ''
                } ${
                  isSelected
                    ? 'bg-slate-800/95 border-red-500 shadow-md shadow-red-950/40 ring-1 ring-red-500'
                    : 'bg-slate-950/80 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/60'
                }`}
              >
                {/* Header Row: Type Icon, Title & Severity */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="shrink-0">{getIncidentTypeIcon(incident.type)}</span>
                    <h3 className="font-semibold text-slate-100 text-xs truncate leading-snug">
                      {incident.title}
                    </h3>
                  </div>
                  <div className="shrink-0">
                    <StatusBadge type="severity" value={incident.severity} />
                  </div>
                </div>

                {/* Sub Row: ID, Priority, Status */}
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-red-400">{incident.incident_id}</span>
                    <StatusBadge type="priority" value={incident.priority} />
                  </div>
                  <StatusBadge type="status" value={incident.status} />
                </div>

                {/* Footer Metadata Row: Reports merged, Units, Time */}
                <div className="pt-1.5 border-t border-slate-900/90 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <div className="flex items-center gap-2">
                    {reportCount > 1 ? (
                      <span className="inline-flex items-center gap-1 text-purple-400 bg-purple-950/80 px-1.5 py-0.2 rounded border border-purple-900">
                        <Layers className="h-2.5 w-2.5" />
                        <span>{reportCount} reports merged</span>
                      </span>
                    ) : (
                      <span>1 report</span>
                    )}

                    {assignedCount > 0 ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-950/80 px-1.5 py-0.2 rounded border border-emerald-900">
                        <Truck className="h-2.5 w-2.5" />
                        <span>{assignedCount} unit{assignedCount > 1 ? 's' : ''}</span>
                      </span>
                    ) : (
                      <span className="text-slate-600">0 units</span>
                    )}
                  </div>

                  <div className="flex items-center gap-1 text-slate-400">
                    <Clock className="h-2.5 w-2.5 text-slate-500" />
                    <span>{timeAgo}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Queue Footer Status */}
      <div className="px-3.5 py-2 border-t border-slate-800/80 bg-slate-950 text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>Active Priority: {activeCount} Cases</span>
        <span className="text-emerald-500 flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Stream Live</span>
        </span>
      </div>
    </div>
  );
};

export default IncidentQueue;
