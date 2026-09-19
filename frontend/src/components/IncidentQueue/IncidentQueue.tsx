'use client';

import React, { useState, useMemo } from 'react';
import { Incident } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Search,
  Flame,
  AlertTriangle,
  Clock,
  MapPin,
  Sparkles,
  Layers,
  CheckCircle,
  Truck,
  ArrowRight,
} from 'lucide-react';

interface IncidentQueueProps {
  incidents: Incident[];
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident) => void;
  onOpenReportModal: () => void;
}

export const IncidentQueue: React.FC<IncidentQueueProps> = ({
  incidents,
  selectedIncident,
  onSelectIncident,
  onOpenReportModal,
}) => {
  const [filterTab, setFilterTab] = useState<'all' | 'active' | 'critical' | 'resolved'>('active');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      // Filter by tab
      if (filterTab === 'active') {
        if (['RESOLVED', 'CLOSED'].includes(incident.status)) return false;
      } else if (filterTab === 'critical') {
        if (incident.severity !== 'CRITICAL' && incident.priority !== 'P1') return false;
      } else if (filterTab === 'resolved') {
        if (!['RESOLVED', 'CLOSED'].includes(incident.status)) return false;
      }

      // Filter by search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesId = incident.incident_id?.toLowerCase().includes(q);
        const matchesTitle = incident.title?.toLowerCase().includes(q);
        const matchesDesc = incident.description?.toLowerCase().includes(q);
        const matchesAddress = incident.address?.toLowerCase().includes(q);
        const matchesType = incident.type?.toLowerCase().includes(q);
        return matchesId || matchesTitle || matchesDesc || matchesAddress || matchesType;
      }

      return true;
    });
  }, [incidents, filterTab, searchQuery]);

  const activeCount = useMemo(
    () => incidents.filter((i) => !['RESOLVED', 'CLOSED'].includes(i.status)).length,
    [incidents]
  );
  const criticalCount = useMemo(
    () => incidents.filter((i) => i.severity === 'CRITICAL' || i.priority === 'P1').length,
    [incidents]
  );
  const resolvedCount = useMemo(
    () => incidents.filter((i) => ['RESOLVED', 'CLOSED'].includes(i.status)).length,
    [incidents]
  );

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header & Filter Bar */}
      <div className="p-4 border-b border-slate-800 space-y-3 bg-slate-900/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Flame className="h-5 w-5 text-red-500 animate-pulse" />
            <h2 className="font-bold text-white text-base">Emergency Queue</h2>
            <span className="text-xs font-mono bg-red-950 text-red-400 border border-red-800 px-2 py-0.5 rounded-full font-semibold">
              {incidents.length} Total
            </span>
          </div>

          <button
            onClick={onOpenReportModal}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-medium transition-all shadow-md shadow-red-600/20 active:scale-95 flex items-center space-x-1.5"
          >
            <span>+ New Report</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, keyword, address..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-colors"
          />
        </div>

        {/* Filter Tabs */}
        <div className="grid grid-cols-4 gap-1 p-1 bg-slate-950 rounded-lg border border-slate-800/80 text-xs font-medium">
          <button
            onClick={() => setFilterTab('active')}
            className={`py-1.5 rounded text-center transition-all ${
              filterTab === 'active'
                ? 'bg-red-600 text-white shadow font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Active ({activeCount})
          </button>
          <button
            onClick={() => setFilterTab('critical')}
            className={`py-1.5 rounded text-center transition-all ${
              filterTab === 'critical'
                ? 'bg-rose-900 text-rose-200 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Critical ({criticalCount})
          </button>
          <button
            onClick={() => setFilterTab('resolved')}
            className={`py-1.5 rounded text-center transition-all ${
              filterTab === 'resolved'
                ? 'bg-emerald-900 text-emerald-200 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Resolved ({resolvedCount})
          </button>
          <button
            onClick={() => setFilterTab('all')}
            className={`py-1.5 rounded text-center transition-all ${
              filterTab === 'all'
                ? 'bg-slate-800 text-white font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({incidents.length})
          </button>
        </div>
      </div>

      {/* Incident List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5 divide-y-0">
        {filteredIncidents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center p-4">
            <AlertTriangle className="h-8 w-8 text-slate-600 mb-2" />
            <p className="text-xs text-slate-400 font-medium">No incidents match the active filter.</p>
            <p className="text-[11px] text-slate-600 mt-1">Try changing tabs or clearing search criteria.</p>
          </div>
        ) : (
          filteredIncidents.map((incident) => {
            const isSelected = selectedIncident?.incident_id === incident.incident_id;
            const duplicateCount = incident.duplicate_count || 0;
            const assignedCount = incident.assigned_resources?.length || 0;

            return (
              <div
                key={incident.incident_id || incident._id}
                onClick={() => onSelectIncident(incident)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer space-y-2.5 relative ${
                  isSelected
                    ? 'bg-slate-900 border-red-500 shadow-lg shadow-red-950/30 ring-1 ring-red-500'
                    : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/40'
                }`}
              >
                {/* Top Row: ID, Badges, Status */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-red-400">
                      {incident.incident_id}
                    </span>
                    <StatusBadge type="status" value={incident.status} />
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <StatusBadge type="severity" value={incident.severity} />
                    <StatusBadge type="priority" value={incident.priority} />
                  </div>
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="font-semibold text-slate-100 text-xs sm:text-sm line-clamp-1 group-hover:text-white">
                    {incident.title}
                  </h3>
                  <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-relaxed">
                    {incident.description}
                  </p>
                </div>

                {/* Metadata Row: Address, Duplicate merges, Resources */}
                <div className="pt-2 border-t border-slate-900 flex flex-wrap items-center justify-between text-[11px] text-slate-500 font-mono gap-1">
                  <div className="flex items-center space-x-1 truncate max-w-[180px]">
                    <MapPin className="h-3 w-3 text-slate-500 shrink-0" />
                    <span className="truncate">{incident.address || 'GPS Coordinates Set'}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    {duplicateCount > 0 && (
                      <span className="inline-flex items-center space-x-1 text-purple-400 bg-purple-950/80 px-1.5 py-0.5 rounded border border-purple-800 text-[10px]">
                        <Layers className="h-2.5 w-2.5" />
                        <span>+{duplicateCount} merged</span>
                      </span>
                    )}

                    {assignedCount > 0 && (
                      <span className="inline-flex items-center space-x-1 text-emerald-400 bg-emerald-950/80 px-1.5 py-0.5 rounded border border-emerald-800 text-[10px]">
                        <Truck className="h-2.5 w-2.5" />
                        <span>{assignedCount} unit{assignedCount > 1 ? 's' : ''}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
