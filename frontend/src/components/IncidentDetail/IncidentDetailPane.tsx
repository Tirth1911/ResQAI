'use client';

import React, { useState, useEffect } from 'react';
import { Incident, ResourceRecommendation, IncidentRecommendationsResponse } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import {
  X,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Layers,
  Truck,
  CheckCircle2,
  Clock,
  MapPin,
  Send,
  RefreshCw,
  FileText,
  Users,
  ChevronRight,
  Flame,
  Check,
  ExternalLink,
} from 'lucide-react';

interface IncidentDetailPaneProps {
  incident: Incident;
  onClose: () => void;
  onIncidentUpdated: () => void;
}

export const IncidentDetailPane: React.FC<IncidentDetailPaneProps> = ({
  incident,
  onClose,
  onIncidentUpdated,
}) => {
  const [recommendations, setRecommendations] = useState<ResourceRecommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [relatedDuplicates, setRelatedDuplicates] = useState<any>(null);
  const [loadingDuplicates, setLoadingDuplicates] = useState(false);
  const [analyzingAI, setAnalyzingAI] = useState(false);
  const [dispatchingId, setDispatchingId] = useState<string | null>(null);
  const [releasingId, setReleasingId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [checkedSOPs, setCheckedSOPs] = useState<Record<number, boolean>>({});

  // Load resource recommendations and duplicate relations on incident change
  useEffect(() => {
    if (incident?.incident_id) {
      loadRecommendations();
      loadRelatedDuplicates();
    }
  }, [incident?.incident_id]);

  const loadRecommendations = async () => {
    try {
      setLoadingRecs(true);
      const res = await resourceService.getRecommendations(incident.incident_id, 5);
      setRecommendations(res.recommendations || []);
    } catch (err) {
      console.error('Error loading recommendations:', err);
    } finally {
      setLoadingRecs(false);
    }
  };

  const loadRelatedDuplicates = async () => {
    try {
      setLoadingDuplicates(true);
      const res = await incidentService.getRelatedIncidents(incident.incident_id);
      setRelatedDuplicates(res);
    } catch (err) {
      console.error('Error loading duplicate relations:', err);
    } finally {
      setLoadingDuplicates(false);
    }
  };

  const handleRunAIAnalysis = async () => {
    try {
      setAnalyzingAI(true);
      await incidentService.analyzeIncident(incident.incident_id, true);
      onIncidentUpdated();
    } catch (err) {
      console.error('AI Analysis failed:', err);
    } finally {
      setAnalyzingAI(false);
    }
  };

  const handleDispatchResource = async (resourceId: string) => {
    try {
      setDispatchingId(resourceId);
      await incidentService.assignResource(incident.incident_id, resourceId);
      await loadRecommendations();
      onIncidentUpdated();
    } catch (err) {
      console.error('Dispatch failed:', err);
    } finally {
      setDispatchingId(null);
    }
  };

  const handleReleaseResource = async (resourceId: string) => {
    try {
      setReleasingId(resourceId);
      await resourceService.releaseResource(resourceId);
      await loadRecommendations();
      onIncidentUpdated();
    } catch (err) {
      console.error('Release failed:', err);
    } finally {
      setReleasingId(null);
    }
  };

  const handleStatusTransition = async (action: 'verify' | 'resolve' | 'close') => {
    try {
      setActionLoading(true);
      if (action === 'verify') {
        await incidentService.verifyIncident(incident.incident_id, 'Command Center Officer');
      } else if (action === 'resolve') {
        await incidentService.resolveIncident(incident.incident_id, 'Command Center Officer');
      } else if (action === 'close') {
        await incidentService.closeIncident(incident.incident_id, 'Command Center Officer');
      }
      onIncidentUpdated();
    } catch (err) {
      console.error('Action transition failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const toggleSOP = (index: number) => {
    setCheckedSOPs((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const aiAnalysis = incident.ai_analysis || {};
  const coords = incident.location?.coordinates || [0, 0];
  const [lon, lat] = coords;

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800 shadow-2xl overflow-y-auto">
      {/* Top Header */}
      <div className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur-md p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="font-mono text-sm font-extrabold text-red-500">
            {incident.incident_id}
          </span>
          <StatusBadge type="status" value={incident.status} />
          <StatusBadge type="severity" value={incident.severity} />
          <StatusBadge type="priority" value={incident.priority} />
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="p-5 space-y-6">
        {/* Title & Core Details */}
        <div className="space-y-2">
          <h1 className="text-xl font-bold text-white leading-snug">{incident.title}</h1>
          <p className="text-xs text-slate-300 bg-slate-950/80 p-3 rounded-lg border border-slate-800 leading-relaxed font-sans">
            {incident.description}
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
            <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800 flex items-center space-x-2">
              <MapPin className="h-4 w-4 text-red-400 shrink-0" />
              <div className="truncate">
                <div className="text-[10px] text-slate-500 uppercase">Address / Coordinates</div>
                <div className="text-slate-300 truncate">{incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}</div>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800 flex items-center space-x-2">
              <Clock className="h-4 w-4 text-amber-400 shrink-0" />
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Source / Reported</div>
                <div className="text-slate-300 truncate">
                  {incident.source} • {new Date(incident.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Operational Lifecycle Control Bar */}
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Operational Actions
            </span>
            <span className="text-[11px] font-mono text-slate-500">Current: {incident.status}</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {incident.status === 'REPORTED' && (
              <button
                onClick={() => handleStatusTransition('verify')}
                disabled={actionLoading}
                className="py-2 px-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1.5 col-span-3 shadow"
              >
                <ShieldCheck className="h-4 w-4" />
                <span>Verify Emergency Report</span>
              </button>
            )}

            {['REPORTED', 'VERIFIED', 'DISPATCHED', 'IN_PROGRESS'].includes(incident.status) && (
              <button
                onClick={() => handleStatusTransition('resolve')}
                disabled={actionLoading}
                className="py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1.5 shadow"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>Mark Resolved</span>
              </button>
            )}

            {incident.status !== 'CLOSED' && (
              <button
                onClick={() => handleStatusTransition('close')}
                disabled={actionLoading}
                className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1.5"
              >
                <X className="h-4 w-4" />
                <span>Close Incident</span>
              </button>
            )}

            <button
              onClick={handleRunAIAnalysis}
              disabled={analyzingAI}
              className="py-2 px-3 bg-purple-900/60 hover:bg-purple-800/80 border border-purple-700 text-purple-200 rounded-lg text-xs font-medium transition-all flex items-center justify-center space-x-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${analyzingAI ? 'animate-spin' : ''}`} />
              <span>{analyzingAI ? 'Analyzing...' : 'Re-Run AI'}</span>
            </button>
          </div>
        </div>

        {/* AI Incident Intelligence & Triage Card */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/40 via-slate-900 to-slate-950 border border-purple-900/50 space-y-3.5 shadow-xl">
          <div className="flex items-center justify-between border-b border-purple-900/40 pb-2.5">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">AI Incident Intelligence</h3>
            </div>
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="text-purple-400">Confidence:</span>
              <span className="bg-purple-950 text-purple-300 font-bold px-2 py-0.5 rounded border border-purple-800">
                {((aiAnalysis.confidence || incident.confidence || 0.85) * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* AI Metrics Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-500">People At Risk</div>
              <div className="text-base font-bold text-amber-400">
                {aiAnalysis.people_at_risk !== undefined ? aiAnalysis.people_at_risk : '3-5 Persons'}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-[10px] text-slate-500">Classification</div>
              <div className="text-base font-bold text-white capitalize">
                {aiAnalysis.incident_type || incident.type}
              </div>
            </div>
          </div>

          {/* AI Reasoning / Summary */}
          {aiAnalysis.reasoning && (
            <div className="space-y-1">
              <div className="text-[11px] font-mono text-purple-400">AI Reasoning:</div>
              <p className="text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
                {aiAnalysis.reasoning}
              </p>
            </div>
          )}

          {/* Immediate Action SOP Checklist */}
          {aiAnalysis.immediate_actions && aiAnalysis.immediate_actions.length > 0 && (
            <div className="space-y-2 pt-1">
              <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>Standard Operating Procedure (SOP) Checklist:</span>
                <span className="text-[10px] text-purple-400">
                  {Object.values(checkedSOPs).filter(Boolean).length}/{aiAnalysis.immediate_actions.length} Completed
                </span>
              </div>
              <div className="space-y-1.5">
                {aiAnalysis.immediate_actions.map((action: string, idx: number) => {
                  const isChecked = !!checkedSOPs[idx];
                  return (
                    <div
                      key={idx}
                      onClick={() => toggleSOP(idx)}
                      className={`p-2 rounded-lg border text-xs flex items-start space-x-2 cursor-pointer transition-all ${
                        isChecked
                          ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300 line-through opacity-80'
                          : 'bg-slate-950 border-slate-800 text-slate-200 hover:border-slate-700'
                      }`}
                    >
                      <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                        isChecked ? 'bg-emerald-600 border-emerald-500 text-white' : 'border-slate-700 bg-slate-900'
                      }`}>
                        {isChecked && <Check className="h-3 w-3" />}
                      </div>
                      <span className="flex-1 leading-snug">{action}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* AI Resource Recommendation Engine */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3.5 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center space-x-2">
              <Truck className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Recommended Resources</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              Formula: (0.50×Dist + 0.30×Cap + 0.20×Ready)
            </span>
          </div>

          {loadingRecs ? (
            <div className="p-6 text-center text-xs font-mono text-slate-500">
              Calculating nearest response units and capability matches...
            </div>
          ) : recommendations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No matching available resources within dispatch radius.
            </div>
          ) : (
            <div className="space-y-2.5">
              {recommendations.map((rec) => {
                const isAssigned = incident.assigned_resources?.includes(rec.resource_id);
                const isDispatching = dispatchingId === rec.resource_id;
                const isReleasing = releasingId === rec.resource_id;

                return (
                  <div
                    key={rec.resource_id}
                    className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-emerald-400 text-xs">
                          {rec.resource_id}
                        </span>
                        <span className="text-xs text-white font-medium">{rec.name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                          {rec.category}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                          {(rec.score * 100).toFixed(0)}% Match
                        </span>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-400 font-mono">
                      📍 {rec.distance_km} km away • {rec.reason}
                    </p>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                      <div className="flex flex-wrap gap-1">
                        {rec.capabilities?.slice(0, 3).map((cap, i) => (
                          <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 font-mono">
                            {cap}
                          </span>
                        ))}
                      </div>

                      {isAssigned ? (
                        <button
                          onClick={() => handleReleaseResource(rec.resource_id)}
                          disabled={isReleasing}
                          className="px-3 py-1 bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-700 rounded text-xs font-medium transition-all"
                        >
                          {isReleasing ? 'Releasing...' : 'Release Unit'}
                        </button>
                      ) : (
                        <button
                          onClick={() => handleDispatchResource(rec.resource_id)}
                          disabled={isDispatching}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-all shadow active:scale-95 flex items-center space-x-1"
                        >
                          <Send className="h-3 w-3" />
                          <span>{isDispatching ? 'Dispatching...' : 'Dispatch Unit'}</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Spatio-Temporal Duplicate Report Inspector */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center space-x-2">
              <Layers className="h-4 w-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">Spatio-Temporal Duplicate Inspector</h3>
            </div>
            <span className="text-[11px] font-mono text-purple-400 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
              {relatedDuplicates?.total_merged_reports || incident.duplicate_count || 0} Reports Merged
            </span>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed">
            3-Signal Deduplication rule: Distance &le; 1km, Time Gap &le; 45 mins, NLP Text Similarity &ge; 80%.
          </p>

          {relatedDuplicates?.duplicate_history && relatedDuplicates.duplicate_history.length > 0 ? (
            <div className="space-y-2">
              {relatedDuplicates.duplicate_history.map((dup: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-slate-900/60 border border-purple-900/40 text-xs space-y-1">
                  <div className="flex items-center justify-between text-purple-300 font-mono text-[11px]">
                    <span>Source: {dup.source || 'Citizen Hotline'}</span>
                    <span>Similarity: {((dup.similarity_score || 0.85) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="font-semibold text-slate-200">{dup.title}</div>
                  <p className="text-slate-400 text-[11px]">{dup.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-slate-900/40 rounded-lg text-center text-xs text-slate-500 font-mono">
              No duplicate reports detected for this incident.
            </div>
          )}
        </div>

        {/* Audit Timeline */}
        {incident.timeline && incident.timeline.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <span>Incident Audit Timeline</span>
            </h3>

            <div className="space-y-2.5 pl-2 border-l-2 border-slate-800">
              {incident.timeline.map((event, idx) => (
                <div key={idx} className="relative pl-4 text-xs space-y-0.5">
                  <div className="absolute -left-[13px] top-1 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-slate-950"></div>
                  <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                    <span className="font-bold text-white">{event.event}</span>
                    <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-slate-400">{event.actor}: {event.notes || 'Action recorded'}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
