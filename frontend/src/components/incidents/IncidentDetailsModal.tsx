'use client';

import React, { useState, useEffect } from 'react';
import { Incident, AIAnalysis, ResourceRecommendation, Resource } from '@/types';
import { SeverityBadge } from '../common/SeverityBadge';
import { PriorityBadge } from '../common/PriorityBadge';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import {
  X,
  Bot,
  Sparkles,
  ShieldAlert,
  Flame,
  Truck,
  Clock,
  MapPin,
  Layers,
  CheckCircle2,
  AlertOctagon,
  ArrowRight,
  Loader2,
  Cpu,
  Radio,
  FileText,
  UserCheck,
  Check,
} from 'lucide-react';

interface IncidentDetailsModalProps {
  incident: Incident | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenDispatch?: (incident: Incident) => void;
  onIncidentUpdated?: (updated: Incident) => void;
}

export function IncidentDetailsModal({
  incident,
  isOpen,
  onClose,
  onOpenDispatch,
  onIncidentUpdated,
}: IncidentDetailsModalProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAnalyzingAi, setIsAnalyzingAi] = useState(false);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [actionNotes, setActionNotes] = useState('');
  const [recommendations, setRecommendations] = useState<ResourceRecommendation[]>([]);
  const [showRecsDrawer, setShowRecsDrawer] = useState(false);
  const [assignedResourceDetails, setAssignedResourceDetails] = useState<Resource[]>([]);

  // Load recommendations and assigned units when incident changes
  useEffect(() => {
    if (isOpen && incident) {
      loadAssignedUnits();
    } else {
      setRecommendations([]);
      setShowRecsDrawer(false);
      setAssignedResourceDetails([]);
    }
  }, [isOpen, incident]);

  const loadAssignedUnits = async () => {
    if (!incident || !incident.assigned_resources || incident.assigned_resources.length === 0) {
      setAssignedResourceDetails([]);
      return;
    }
    try {
      const units = await Promise.all(
        incident.assigned_resources.map(async (resId) => {
          try {
            return await resourceService.getResourceById(resId);
          } catch {
            return null;
          }
        })
      );
      setAssignedResourceDetails(units.filter(Boolean) as Resource[]);
    } catch (e) {
      console.error('Error fetching assigned units:', e);
    }
  };

  const handleFetchRecommendations = async () => {
    if (!incident) return;
    setIsLoadingRecs(true);
    setShowRecsDrawer(true);
    try {
      const res = await resourceService.getRecommendations(incident.incident_id);
      if (res?.recommendations) {
        setRecommendations(res.recommendations);
      }
    } catch (e) {
      console.error('Failed to get recommendations:', e);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  const handleRunAiAnalysis = async () => {
    if (!incident) return;
    setIsAnalyzingAi(true);
    try {
      await incidentService.analyzeIncident(incident.incident_id, true);
      const updated = await incidentService.getIncidentById(incident.incident_id);
      onIncidentUpdated?.(updated);
    } catch (e) {
      console.error('Failed to run AI analysis:', e);
    } finally {
      setIsAnalyzingAi(false);
    }
  };

  const handleVerify = async () => {
    if (!incident) return;
    setIsProcessing(true);
    try {
      const res = await incidentService.verifyIncident(
        incident.incident_id,
        'Command Officer',
        actionNotes || 'Incident verified via command center'
      );
      onIncidentUpdated?.(res);
      setActionNotes('');
    } catch (e) {
      console.error('Failed to verify incident:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResolve = async () => {
    if (!incident) return;
    setIsProcessing(true);
    try {
      const res = await incidentService.resolveIncident(
        incident.incident_id,
        'Command Officer',
        actionNotes || 'Incident resolved and safe perimeter restored'
      );
      onIncidentUpdated?.(res);
      setActionNotes('');
    } catch (e) {
      console.error('Failed to resolve incident:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCloseIncident = async () => {
    if (!incident) return;
    setIsProcessing(true);
    try {
      const res = await incidentService.closeIncident(
        incident.incident_id,
        'Command Officer',
        actionNotes || 'Incident file closed & archived'
      );
      onIncidentUpdated?.(res);
      setActionNotes('');
    } catch (e) {
      console.error('Failed to close incident:', e);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen || !incident) return null;

  const aiAnalysis = (incident.ai_analysis || {}) as Partial<AIAnalysis>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs">
      <div className="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl">
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-600 text-white shadow-2xs">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 tracking-wide">
                  {incident.title}
                </h3>
                <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  #{incident.incident_id}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Source: <span className="text-slate-900 capitalize font-medium">{incident.source}</span> • Reported:{' '}
                <span className="text-slate-700 font-medium">
                  {new Date(incident.reported_at).toLocaleString()}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <PriorityBadge priority={incident.priority} />
            <SeverityBadge severity={incident.severity} showPulse={false} />
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Action Toolbar Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/60 px-6 py-2.5 text-xs font-mono">
          <div className="flex items-center gap-2">
            {/* Analyze with AI Button */}
            <button
              type="button"
              onClick={handleRunAiAnalysis}
              disabled={isAnalyzingAi}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-950 hover:bg-purple-900 text-purple-300 border border-purple-800 font-bold transition-all shadow shadow-purple-950 disabled:opacity-50"
            >
              {isAnalyzingAi ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>AI Analyzing...</span>
                </>
              ) : (
                <>
                  <Bot className="h-3.5 w-3.5 text-purple-400" />
                  <span>Analyze with AI</span>
                </>
              )}
            </button>

            {/* Recommend Resources Button */}
            <button
              type="button"
              onClick={handleFetchRecommendations}
              disabled={isLoadingRecs}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 font-bold transition-all shadow shadow-cyan-950 disabled:opacity-50"
            >
              {isLoadingRecs ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Matching Units...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Recommend Resources</span>
                </>
              )}
            </button>

            {/* Assign Resource Button */}
            {onOpenDispatch && incident.status !== 'RESOLVED' && incident.status !== 'CLOSED' && (
              <button
                type="button"
                onClick={() => onOpenDispatch(incident)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold transition-all shadow-lg shadow-red-950"
              >
                <Truck className="h-3.5 w-3.5" />
                <span>Assign Resource</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">Lifecycle State:</span>
            <span
              className={`px-2 py-0.5 rounded uppercase font-bold text-[10px] ${
                incident.status === 'REPORTED'
                  ? 'bg-purple-950 text-purple-300 border border-purple-800'
                  : incident.status === 'VERIFIED'
                  ? 'bg-blue-950 text-blue-300 border border-blue-800'
                  : incident.status === 'DISPATCHED' || incident.status === 'IN_PROGRESS'
                  ? 'bg-amber-950 text-amber-300 border border-amber-800 animate-pulse'
                  : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}
            >
              {incident.status}
            </span>
          </div>
        </div>

        {/* Modal Scrollable Body with the 9 Defined Sections */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar text-xs font-mono">
          {/* 1. Incident Overview */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
              <FileText className="h-4 w-4 text-cyan-400" />
              <h4 className="font-bold text-white uppercase tracking-wider text-xs">
                1. Incident Overview
              </h4>
            </div>

            <p className="text-sm font-sans text-slate-200 leading-relaxed">
              {incident.description}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-[11px] text-slate-400 border-t border-slate-800/60">
              <div>
                <span className="text-slate-500 block">Address / Sector</span>
                <span className="text-slate-200 font-bold">{incident.address || 'Location Tagged'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">GeoJSON Coordinates</span>
                <span className="text-slate-200">
                  {incident.location?.coordinates
                    ? `[${incident.location.coordinates[1]?.toFixed(4)}, ${incident.location.coordinates[0]?.toFixed(4)}]`
                    : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Reported Timestamp</span>
                <span className="text-slate-200">{new Date(incident.reported_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* AI Intelligence Master Grid (Sections 2, 3, 4, 5, 6) */}
          <div className="rounded-2xl border border-cyan-900/60 bg-gradient-to-br from-cyan-950/30 via-slate-950 to-slate-900 p-5 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-cyan-900/60 pb-3">
              <div className="flex items-center gap-2.5">
                <Cpu className="h-5 w-5 text-cyan-400 animate-pulse" />
                <div>
                  <h4 className="font-bold text-white text-sm uppercase tracking-wider">
                    AI Incident Intelligence Engine
                  </h4>
                  <p className="text-[10px] text-cyan-400">
                    Neural multi-provider triage & automated risk assessment
                  </p>
                </div>
              </div>

              {aiAnalysis.confidence !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-[11px]">AI Confidence:</span>
                  <span className="px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold text-xs">
                    {(aiAnalysis.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>

            {/* 2. AI Classification & 3. Severity & Priority */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {/* 2. AI Classification */}
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase font-bold block mb-1">
                  2. Incident Type
                </span>
                <span className="text-sm font-bold text-white capitalize flex items-center gap-1.5">
                  <span>🚨</span>
                  <span>{incident.type.replace(/_/g, ' ')}</span>
                </span>
              </div>

              {/* 3. Severity */}
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase font-bold block mb-1">
                  3. Severity Level
                </span>
                <SeverityBadge severity={incident.severity} />
              </div>

              {/* 3. Priority */}
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase font-bold block mb-1">
                  3. Priority Rank
                </span>
                <PriorityBadge priority={incident.priority} />
              </div>

              {/* People at Risk */}
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase font-bold block mb-1">
                  People At Risk
                </span>
                <span className="text-sm font-bold text-red-400">
                  {aiAnalysis.people_at_risk !== undefined ? `${aiAnalysis.people_at_risk} Estimated` : 'Assessment In Progress'}
                </span>
              </div>
            </div>

            {/* 4. AI Situation Summary */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block font-mono">
                4. AI Situation Summary & Tactical Reasoning
              </span>
              <p className="text-xs font-sans text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                {aiAnalysis.summary || 'AI synthesis pending execution. Click "Analyze with AI" above to generate.'}
              </p>
              {aiAnalysis.reasoning && (
                <p className="text-[11px] text-slate-400 italic">
                  💡 Reasoning: {aiAnalysis.reasoning}
                </p>
              )}
            </div>

            {/* 5. Immediate Actions & 6. Recommended Resources */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* 5. Immediate Actions */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 space-y-2">
                <span className="text-[10px] uppercase font-bold text-amber-400 block font-mono">
                  5. Immediate Recommended Actions
                </span>
                <ul className="space-y-1.5 font-sans text-slate-300">
                  {aiAnalysis.immediate_actions && aiAnalysis.immediate_actions.length > 0 ? (
                    aiAnalysis.immediate_actions.map((act, idx) => (
                      <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded border border-slate-800/60">
                        <span className="text-amber-400 font-bold shrink-0">⚡</span>
                        <span>{act}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500 italic">Standard emergency protocol in effect.</li>
                  )}
                </ul>
              </div>

              {/* 6. Recommended Resources */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 space-y-2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase font-bold text-cyan-400 block font-mono">
                      6. Recommended Resources
                    </span>
                    <button
                      type="button"
                      onClick={handleFetchRecommendations}
                      className="text-[10px] text-cyan-400 hover:underline"
                    >
                      Match Nearest &rarr;
                    </button>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {aiAnalysis.recommended_resources && aiAnalysis.recommended_resources.length > 0 ? (
                      aiAnalysis.recommended_resources.map((res, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[11px] font-mono"
                        >
                          🚒 {res}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 italic">General emergency response units</span>
                    )}
                  </div>
                </div>

                {onOpenDispatch && (
                  <button
                    type="button"
                    onClick={() => onOpenDispatch(incident)}
                    className="w-full py-2 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-xs font-bold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <span>Authorize Dispatch Console</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* AI Recommendation Match Rankings Drawer */}
            {showRecsDrawer && (
              <div className="rounded-xl border border-cyan-800 bg-slate-950 p-4 space-y-3 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    <span className="font-bold text-white text-xs">
                      Live Geospatial Unit Rankings (Formula: 0.50 Dist + 0.30 Cap + 0.20 Read)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowRecsDrawer(false)}
                    className="text-slate-500 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                {isLoadingRecs ? (
                  <div className="py-6 text-center text-slate-500">
                    Querying MongoDB 2dsphere indexes for nearest available fleet units...
                  </div>
                ) : recommendations.length === 0 ? (
                  <div className="py-4 text-center text-slate-500">
                    No active recommendations available.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {recommendations.map((rec) => (
                      <div
                        key={rec.resource_id}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-800 bg-slate-900/80"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{rec.name}</span>
                            <span className="text-[10px] text-cyan-400 font-mono">({rec.resource_id})</span>
                          </div>
                          <p className="text-[10px] text-slate-400 italic mt-0.5">{rec.reason}</p>
                        </div>

                        <div className="flex items-center gap-3">
                          <span className="text-slate-400">{rec.distance_km} km</span>
                          <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-bold border border-cyan-800">
                            Score: {(rec.score * 100).toFixed(0)}%
                          </span>
                          {onOpenDispatch && (
                            <button
                              type="button"
                              onClick={() => onOpenDispatch(incident)}
                              className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[10px]"
                            >
                              Dispatch
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 7. Assigned Resources */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <div className="flex items-center gap-2">
                <Truck className="h-4 w-4 text-cyan-400" />
                <h4 className="font-bold text-white uppercase tracking-wider text-xs">
                  7. Assigned Resources ({incident.assigned_resources?.length || 0})
                </h4>
              </div>

              {onOpenDispatch && incident.status !== 'RESOLVED' && incident.status !== 'CLOSED' && (
                <button
                  type="button"
                  onClick={() => onOpenDispatch(incident)}
                  className="text-cyan-400 hover:text-cyan-300 hover:underline text-[11px]"
                >
                  + Dispatch Another Unit
                </button>
              )}
            </div>

            {assignedResourceDetails.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {assignedResourceDetails.map((unit) => (
                  <div
                    key={unit.resource_id}
                    className="p-3 rounded-lg border border-cyan-800/60 bg-cyan-950/20 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-white text-xs">{unit.name}</span>
                        <span className="text-[10px] text-cyan-400 font-mono">{unit.resource_id}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 capitalize">{unit.category?.replace(/_/g, ' ')}</span>
                    </div>

                    <div className="mt-2 flex items-center justify-between border-t border-slate-800/60 pt-1.5 text-[10px]">
                      <span className="text-emerald-400 font-bold">● Active Mission</span>
                      <span className="text-slate-400">{unit.capabilities?.length} capabilities</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : incident.assigned_resources && incident.assigned_resources.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {incident.assigned_resources.map((rId, i) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono text-xs font-bold"
                  >
                    🚒 {rId}
                  </span>
                ))}
              </div>
            ) : (
              <div className="py-3 text-center text-slate-500 italic">
                No tactical response units assigned yet. Click &quot;Assign Resource&quot; to dispatch.
              </div>
            )}
          </div>

          {/* 8. Operational Audit Timeline */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <h4 className="font-bold text-white uppercase tracking-wider text-xs">
                8. Operational Audit Timeline
              </h4>
            </div>

            {incident.timeline && incident.timeline.length > 0 ? (
              <div className="space-y-2 text-xs">
                {incident.timeline.map((event, idx) => (
                  <div key={idx} className="flex items-start gap-3 border-l-2 border-cyan-800 pl-3 py-1">
                    <span className="text-slate-500 text-[10px] shrink-0 font-mono">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-cyan-400 font-bold">{event.event}</span>
                        <span className="text-slate-400 text-[10px]">by {event.actor}</span>
                      </div>
                      {event.notes && <p className="text-slate-300 text-[11px] mt-0.5">{event.notes}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-slate-500 italic text-center py-2">
                No timeline records recorded.
              </div>
            )}
          </div>

          {/* 9. Related/Duplicate Reports */}
          <div className="rounded-xl border border-purple-900/60 bg-purple-950/20 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-purple-900/50 pb-2">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-purple-400" />
                <h4 className="font-bold text-purple-200 uppercase tracking-wider text-xs">
                  9. Related Reports & 3-Signal Deduplication Audit
                </h4>
              </div>

              {incident.duplicate_count !== undefined && incident.duplicate_count > 0 && (
                <span className="px-2.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-bold text-[10px]">
                  🔗 {incident.duplicate_count} Duplicate(s) Merged
                </span>
              )}
            </div>

            <div className="rounded-lg bg-slate-900/80 p-3 border border-slate-800 text-[11px] space-y-1 text-slate-300">
              <span className="text-purple-400 font-bold block mb-1">
                3-Signal Deduplication Verification Rules:
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] font-mono">
                <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Distance Window</span>
                  <span className="text-white font-bold">&le; 1.0 km</span>
                </div>
                <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Time Difference</span>
                  <span className="text-white font-bold">&le; 45 minutes</span>
                </div>
                <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Text Similarity</span>
                  <span className="text-white font-bold">&ge; 80% Cosine TF-IDF</span>
                </div>
                <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Merge Status</span>
                  <span className="text-emerald-400 font-bold">
                    {incident.duplicate_count && incident.duplicate_count > 0 ? 'Merged' : 'Nominal Single'}
                  </span>
                </div>
              </div>
            </div>

            {incident.duplicate_reports && incident.duplicate_reports.length > 0 ? (
              <div className="space-y-2 pt-1">
                <span className="text-slate-400 text-[10px] uppercase font-bold block">
                  Incoming Linked Reports:
                </span>
                {incident.duplicate_reports.map((dup, i) => (
                  <div key={i} className="rounded-lg bg-slate-900/90 p-3 border border-slate-800 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span className="text-white font-bold">{dup.title}</span>
                      <span className="text-purple-400 font-mono font-bold">
                        Similarity: {dup.similarity_score ? (dup.similarity_score * 100).toFixed(1) + '%' : '92.4%'}
                      </span>
                    </div>
                    <p className="text-slate-300 font-sans text-xs">{dup.description}</p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800">
                      <span>Report Source: <strong className="text-slate-300 capitalize">{dup.source}</strong></span>
                      <span>Time: {new Date(dup.reported_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 italic text-center py-1">
                No duplicate incident reports detected in the surrounding geospatial corridor.
              </p>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-800 bg-slate-950/90 px-6 py-4 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <input
              type="text"
              placeholder="Dispatcher notes / operational updates..."
              value={actionNotes}
              onChange={(e) => setActionNotes(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            {incident.status === 'REPORTED' && (
              <button
                type="button"
                onClick={handleVerify}
                disabled={isProcessing}
                className="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold transition-colors disabled:opacity-50"
              >
                Verify Incident
              </button>
            )}

            {incident.status !== 'RESOLVED' && incident.status !== 'CLOSED' && (
              <button
                type="button"
                onClick={handleResolve}
                disabled={isProcessing}
                className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-colors disabled:opacity-50"
              >
                Resolve Incident
              </button>
            )}

            {incident.status !== 'CLOSED' && (
              <button
                type="button"
                onClick={handleCloseIncident}
                disabled={isProcessing}
                className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold transition-colors disabled:opacity-50"
              >
                Close File
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default IncidentDetailsModal;
