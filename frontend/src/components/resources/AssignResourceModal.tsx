'use client';

import React, { useEffect, useState } from 'react';
import { Incident, Resource, ResourceRecommendation } from '@/types';
import { resourceService } from '@/services/resourceService';
import { incidentService } from '@/services/incidentService';

interface AssignResourceModalProps {
  incident: Incident | null;
  isOpen: boolean;
  onClose: () => void;
  onAssigned?: (incident: Incident, resource: Resource) => void;
}

export function AssignResourceModal({
  incident,
  isOpen,
  onClose,
  onAssigned,
}: AssignResourceModalProps) {
  const [recommendations, setRecommendations] = useState<ResourceRecommendation[]>([]);
  const [allResources, setAllResources] = useState<Resource[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const [selectedResourceId, setSelectedResourceId] = useState<string>('');
  const [dispatcherNotes, setDispatcherNotes] = useState('');

  useEffect(() => {
    if (isOpen && incident) {
      loadRecommendationsAndResources();
    }
  }, [isOpen, incident]);

  const loadRecommendationsAndResources = async () => {
    if (!incident) return;
    setIsLoading(true);
    try {
      // 1. Fetch AI recommendations
      const recRes = await resourceService.getRecommendations(incident.incident_id);
      if (recRes?.recommendations) {
        setRecommendations(recRes.recommendations);
        if (recRes.recommendations.length > 0) {
          setSelectedResourceId(recRes.recommendations[0].resource_id);
        }
      }

      // 2. Fetch all available resources for manual pick
      const resList = await resourceService.getResources({ status: 'AVAILABLE' });
      setAllResources(resList);
    } catch (e) {
      console.error('Error loading recommendations:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!incident || !selectedResourceId) return;
    setIsAssigning(true);
    try {
      await incidentService.assignResource(
        incident.incident_id,
        selectedResourceId,
        'Command Dispatcher',
        dispatcherNotes || 'Emergency unit dispatched via tactical console'
      );

      // Fetch refreshed incident
      const updatedIncident = await incidentService.getIncidentById(incident.incident_id);
      const assignedRes = allResources.find((r) => r.resource_id === selectedResourceId);
      onAssigned?.(updatedIncident, assignedRes as Resource);
      onClose();
    } catch (e) {
      console.error('Failed to dispatch resource:', e);
    } finally {
      setIsAssigning(false);
    }
  };

  if (!isOpen || !incident) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs">
      <div className="relative w-full max-w-2xl flex flex-col rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-6 py-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🚒</span>
              <h3 className="text-base font-bold text-slate-900">
                Resource Dispatch Console
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Incident: <span className="text-red-700 font-mono font-bold">#{incident.incident_id}</span> • {incident.title}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white text-lg p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar text-sm">
          {/* Target Location Banner */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">Target Address:</span>
            <span className="text-slate-200 font-bold truncate max-w-sm">{incident.address}</span>
          </div>

          {/* AI Recommended Units */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <span>🤖</span>
                <span>AI Recommended Match Rankings</span>
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                Formula: (0.50 × Dist) + (0.30 × Cap) + (0.20 × Read)
              </span>
            </div>

            {isLoading ? (
              <div className="flex h-32 items-center justify-center text-xs text-slate-500 font-mono">
                Calculating optimal geospatial routing...
              </div>
            ) : recommendations.length === 0 ? (
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 text-center text-xs text-slate-500">
                No immediate matches. You may manually select an available unit below.
              </div>
            ) : (
              <div className="space-y-2">
                {recommendations.map((rec) => {
                  const isSelected = selectedResourceId === rec.resource_id;
                  return (
                    <div
                      key={rec.resource_id}
                      onClick={() => setSelectedResourceId(rec.resource_id)}
                      className={`cursor-pointer rounded-xl border p-3.5 transition-all duration-200 ${
                        isSelected
                          ? 'border-cyan-500 bg-cyan-950/30 ring-1 ring-cyan-500'
                          : 'border-slate-800 bg-slate-950/60 hover:border-slate-700 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <input
                            type="radio"
                            checked={isSelected}
                            onChange={() => setSelectedResourceId(rec.resource_id)}
                            className="text-cyan-500 focus:ring-cyan-400"
                          />
                          <div>
                            <h5 className="font-semibold text-white text-sm">{rec.name}</h5>
                            <span className="font-mono text-xs text-slate-400">{rec.resource_id}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                            {rec.distance_km} km away
                          </span>
                          <span className="text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded">
                            Score: {(rec.score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {rec.reason && (
                        <p className="mt-2 text-xs text-slate-400 italic">
                          💡 {rec.reason}
                        </p>
                      )}

                      {rec.capabilities && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {rec.capabilities.map((cap, i) => (
                            <span
                              key={i}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 font-mono"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Dispatch Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider font-mono mb-1.5">
              Mission Instructions / Notes
            </label>
            <textarea
              rows={2}
              value={dispatcherNotes}
              onChange={(e) => setDispatcherNotes(e.target.value)}
              placeholder="E.g., Proceed via north corridor, coordinate with Hazmat Unit on site..."
              className="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none font-mono"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-slate-800 bg-slate-950/90 px-6 py-4 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={handleAssign}
            disabled={!selectedResourceId || isAssigning}
            className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all shadow-lg shadow-cyan-950 disabled:opacity-50"
          >
            {isAssigning ? 'Authorizing Dispatch...' : 'Confirm & Authorize Dispatch'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AssignResourceModal;
