'use client';

import React, { useState } from 'react';
import { Incident, Resource, IncidentSeverity, IncidentType } from '../types';
import { getDispatchRecommendations } from '../utils';
import { 
  Flame, 
  AlertTriangle, 
  Activity, 
  MapPin, 
  Clock, 
  Users, 
  Sparkles, 
  Truck, 
  CheckCircle2, 
  ChevronDown,
  ChevronUp,
  Filter,
  Search
} from 'lucide-react';

interface IncidentBoardProps {
  incidents: Incident[];
  resources: Resource[];
  onDispatchUnit: (incidentId: string, resourceId: string) => void;
  onSelectIncidentOnMap: (inc: Incident) => void;
}

export default function IncidentBoard({
  incidents,
  resources,
  onDispatchUnit,
  onSelectIncidentOnMap
}: IncidentBoardProps) {
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(incidents[0]?.id || null);

  const filteredIncidents = incidents.filter(inc => {
    if (severityFilter !== 'all' && inc.severity !== severityFilter) return false;
    if (typeFilter !== 'all' && inc.type !== typeFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        inc.title.toLowerCase().includes(q) ||
        inc.description.toLowerCase().includes(q) ||
        (inc.address || '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="max-w-[1700px] mx-auto p-6 space-y-6 text-[#1F2933] font-sans">
      
      {/* Top Filter & Command Search Bar */}
      <div className="bg-white border border-[#DED8CC] p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#667085]" />
            <input
              type="text"
              placeholder="Search by location, keyword, or incident title..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] placeholder-[#667085] focus:outline-none focus:ring-2 focus:ring-[#B42318]"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-[#667085] font-semibold">
            <Filter className="w-3.5 h-3.5 text-[#B42318]" />
            <span>SEVERITY:</span>
          </div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318]"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <div className="flex items-center gap-1.5 text-[#667085] font-semibold ml-2">
            <span>TYPE:</span>
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318]"
          >
            <option value="all">All Incident Types</option>
            <option value="fire">Fire</option>
            <option value="industrial">Industrial HAZMAT</option>
            <option value="accident">Traffic Accident</option>
            <option value="flood">Flood & Water</option>
            <option value="collapse">Structural Collapse</option>
            <option value="medical">Medical</option>
          </select>

          <span className="text-[#DED8CC]">|</span>
          <span className="text-[#667085] text-xs">
            Showing <strong className="text-[#1F2933]">{filteredIncidents.length}</strong> of {incidents.length}
          </span>
        </div>
      </div>

      {/* Incidents List Grid */}
      <div className="space-y-4">
        {filteredIncidents.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-xl border border-[#DED8CC] text-[#667085] text-sm">
            No active incidents matching the filter criteria.
          </div>
        ) : (
          filteredIncidents.map((incident) => {
            const isExpanded = expandedId === incident.id;
            const recommendations = getDispatchRecommendations(incident, resources);

            return (
              <div
                key={incident.id}
                className={`bg-white border transition-all rounded-xl overflow-hidden shadow-xs ${
                  incident.severity === 'critical' ? 'border-[#C62828]' :
                  incident.severity === 'high' ? 'border-[#C47A00]' : 'border-[#DED8CC]'
                }`}
              >
                {/* Header Banner Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : incident.id)}
                  className="p-5 flex flex-wrap items-center justify-between gap-4 cursor-pointer hover:bg-[#F5F1E8]/50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-[300px]">
                    <div className={`p-3 rounded-xl flex items-center justify-center ${
                      incident.severity === 'critical' ? 'bg-[#FEEFEF] text-[#C62828] border border-[#FCA5A5]' :
                      incident.severity === 'high' ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]' :
                      'bg-[#F5F1E8] text-[#1F2933]'
                    }`}>
                      <Flame className="w-5 h-5" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs text-[#1F2933] font-bold bg-[#F5F1E8] px-2 py-0.5 rounded border border-[#DED8CC]">
                          {incident.id}
                        </span>
                        <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full ${
                          incident.severity === 'critical' ? 'bg-[#FEEFEF] text-[#C62828] border border-[#FCA5A5]' :
                          incident.severity === 'high' ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]' :
                          'bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]'
                        }`}>
                          {incident.severity}
                        </span>
                        <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[#F5F1E8] text-[#667085]">
                          {incident.type}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#EAF6ED] text-[#16803C] border border-[#A7F3D0]">
                          {incident.status.toUpperCase()}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-[#1F2933] leading-tight">{incident.title}</h3>
                    </div>
                  </div>

                  {/* Summary Stats */}
                  <div className="flex items-center gap-6 text-xs text-[#667085]">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4 text-[#B42318]" />
                      <span>{incident.address?.split(',')[0]}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Users className="w-4 h-4 text-[#1F2933]" />
                      <span><strong className="text-[#1F2933]">{incident.report_count}</strong> Calls Merged</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-[#667085]" />
                      <span>{new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>

                    {isExpanded ? <ChevronUp className="w-5 h-5 text-[#667085]" /> : <ChevronDown className="w-5 h-5 text-[#667085]" />}
                  </div>
                </div>

                {/* Expanded Details Body */}
                {isExpanded && (
                  <div className="p-6 bg-[#F5F1E8]/60 border-t border-[#DED8CC] space-y-6 text-xs">
                    
                    {/* Description & AI Triage Analysis Box */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      
                      <div className="md:col-span-2 bg-white p-5 rounded-xl border border-[#DED8CC] space-y-3 shadow-xs">
                        <div className="font-bold text-[#1F2933] text-sm">Incident Description</div>
                        <p className="text-[#667085] leading-relaxed text-xs">{incident.description}</p>
                        <div className="text-[#667085] text-[11px] pt-2 border-t border-[#DED8CC]">
                          📍 Full Location: <span className="text-[#1F2933] font-medium">{incident.address}</span> (Lat: {incident.lat}, Lng: {incident.lng})
                        </div>
                      </div>

                      {/* AI Triage Card */}
                      <div className="bg-white p-5 rounded-xl border border-[#DED8CC] space-y-3 shadow-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[#1F2933] flex items-center gap-1.5">
                            <Sparkles className="w-4 h-4 text-[#B42318]" />
                            AI TRIAGE ANALYSIS
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#FDECEC] text-[#B42318]">
                            Confidence: {((incident.ai_confidence || 0.92) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-[#667085] text-xs leading-relaxed">
                          {incident.ai_reasoning}
                        </p>
                        <div className="flex items-center justify-between text-[11px] text-[#667085] pt-2 border-t border-[#DED8CC]">
                          <span>Priority Score: <strong className="text-[#1F2933] font-bold text-sm">{incident.priority}</strong>/100</span>
                          <span>Source: <strong className="text-[#1F2933] uppercase">{incident.source}</strong></span>
                        </div>
                      </div>

                    </div>

                    {/* Merged Citizen Reports Feed */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-[#667085] uppercase tracking-wider">
                        SPATIO-TEMPORAL MERGED CALLS ({incident.reports.length})
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {incident.reports.map((rep) => (
                          <div key={rep.id} className="bg-white border border-[#DED8CC] p-3.5 rounded-xl space-y-1.5 text-xs shadow-xs">
                            <div className="flex items-center justify-between text-[10px]">
                              <span className="text-[#B42318] font-bold">[{rep.source.toUpperCase()}]</span>
                              <span className="text-[#667085]">{new Date(rep.reported_at).toLocaleTimeString()}</span>
                            </div>
                            <p className="text-[#1F2933] italic text-xs">"{rep.raw_text}"</p>
                            <div className="text-[10px] text-[#667085]">Reporter: {rep.reporter || 'Anonymous'}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Assigned Units vs Recommended Dispatch Options */}
                    <div className="space-y-3 pt-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-[#1F2933] uppercase tracking-wider flex items-center gap-2">
                          <Truck className="w-4 h-4 text-[#16803C]" />
                          RECOMMENDED RESPONSE UNITS
                        </h4>
                        <button
                          onClick={() => onSelectIncidentOnMap(incident)}
                          className="text-xs text-[#B42318] hover:underline font-semibold"
                        >
                          Focus on Map →
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {recommendations.slice(0, 3).map((rec) => {
                          const isAssigned = (incident.assignments || []).some(a => a.resource_id === rec.resource.id);
                          return (
                            <div
                              key={rec.resource.id}
                              className={`p-4 rounded-xl border space-y-3 flex flex-col justify-between text-xs transition-all ${
                                isAssigned 
                                  ? 'bg-[#EAF6ED] border-[#16803C]' 
                                  : 'bg-white border-[#DED8CC] shadow-xs'
                              }`}
                            >
                              <div>
                                <div className="flex items-start justify-between gap-2">
                                  <div className="font-bold text-[#1F2933] text-sm">{rec.resource.name}</div>
                                  <span className="px-2.5 py-0.5 text-xs font-bold text-[#B42318] bg-[#FDECEC] rounded">
                                    {rec.score}% MATCH
                                  </span>
                                </div>
                                <div className="text-xs text-[#667085]">{rec.resource.station}</div>
                                
                                <div className="grid grid-cols-3 gap-2 text-[10px] text-[#667085] mt-2 bg-[#F5F1E8] p-2 rounded-lg">
                                  <div>📍 {rec.distance_km} km</div>
                                  <div>⏱️ ~{rec.eta_min} min</div>
                                  <div>👥 Cap: {rec.resource.capacity}</div>
                                </div>
                              </div>

                              <div className="pt-2 border-t border-[#DED8CC] flex items-center justify-between">
                                <div className="text-[10px] text-[#667085]">
                                  {rec.match_reasons[0]}
                                </div>

                                {isAssigned ? (
                                  <span className="px-3.5 py-1.5 bg-[#16803C] text-white font-bold text-xs rounded-lg flex items-center gap-1">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                                    <span>DISPATCHED ✓</span>
                                  </span>
                                ) : (
                                  <button
                                    onClick={() => onDispatchUnit(incident.id, rec.resource.id)}
                                    className="px-3.5 py-1.5 bg-[#B42318] hover:bg-[#911E14] text-white font-bold rounded-lg text-xs shadow-xs transition-colors flex items-center gap-1.5"
                                  >
                                    <Truck className="w-3.5 h-3.5" />
                                    <span>Dispatch</span>
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
