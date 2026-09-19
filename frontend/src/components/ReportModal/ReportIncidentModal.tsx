'use client';

import React, { useState } from 'react';
import { incidentService, CreateIncidentPayload } from '@/services/incidentService';
import { IncidentType, IncidentSeverity, IncidentPriority, Incident, AIAnalysis } from '@/types';
import { SeverityBadge } from '@/components/common/SeverityBadge';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import {
  X,
  Send,
  Sparkles,
  AlertTriangle,
  Flame,
  Radio,
  MapPin,
  Layers,
  CheckCircle2,
  Cpu,
  Loader2,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';

interface ReportIncidentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIncidentCreated?: () => void;
  onCreated?: (incident: Incident) => void;
}

const PRESET_SCENARIOS = [
  {
    title: 'Chemical Factory Toxic Smoke & Fire',
    description: 'Thick black fumes and spreading fire in chemical plant storage wing. 4 staff members unaccounted for.',
    type: 'industrial_hazard',
    severity: 'CRITICAL',
    priority: 'P1',
    latitude: 28.5355,
    longitude: 77.2690,
    address: 'Okhla Industrial Area Phase-III, New Delhi',
    source: 'call_center',
  },
  {
    title: 'Multi-Vehicle Pileup with Fuel Spill',
    description: 'Oil tanker collided with passenger bus on expressway. Multiple severe casualties trapped inside vehicle.',
    type: 'road_accident',
    severity: 'CRITICAL',
    priority: 'P1',
    latitude: 28.5700,
    longitude: 77.3200,
    address: 'Delhi-Noida Direct Flyway, Kilometer 8',
    source: 'citizen',
  },
  {
    title: 'Commercial Complex 7th Floor Structural Fire',
    description: 'Electrical short circuit caused intense smoke. Over 50 workers trapped on upper terrace floor.',
    type: 'fire',
    severity: 'HIGH',
    priority: 'P1',
    latitude: 28.4900,
    longitude: 77.0900,
    address: 'Cyber City Sector 24, Gurugram',
    source: 'iot',
  },
  {
    title: 'Underground Metro Gas Inundation',
    description: 'Strong gas odor escaping from sewer line near transit hub. Commuters coughing and evacuating.',
    type: 'gas_leak',
    severity: 'HIGH',
    priority: 'P2',
    latitude: 28.6328,
    longitude: 77.2197,
    address: 'Connaught Place Underground Subway, New Delhi',
    source: 'field_team',
  },
];

export const ReportIncidentModal: React.FC<ReportIncidentModalProps> = ({
  isOpen,
  onClose,
  onIncidentCreated,
  onCreated,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState('call_center');
  const [type, setType] = useState<string>('');
  const [latitude, setLatitude] = useState<number | string>(28.6139);
  const [longitude, setLongitude] = useState<number | string>(77.2090);
  const [address, setAddress] = useState('New Delhi, NCR Central');
  const [autoDedup, setAutoDedup] = useState(true);

  // States
  const [loading, setLoading] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [createdIncident, setCreatedIncident] = useState<Incident | null>(null);
  const [dedupWarning, setDedupWarning] = useState<any>(null);

  if (!isOpen) return null;

  const handleApplyPreset = (scenario: typeof PRESET_SCENARIOS[0]) => {
    setTitle(scenario.title);
    setDescription(scenario.description);
    setType(scenario.type);
    setLatitude(scenario.latitude);
    setLongitude(scenario.longitude);
    setAddress(scenario.address);
    setSource(scenario.source);
  };

  const handleReset = () => {
    setTitle('');
    setDescription('');
    setType('');
    setLatitude(28.6139);
    setLongitude(77.2090);
    setAddress('New Delhi, NCR Central');
    setCreatedIncident(null);
    setDedupWarning(null);
    setLoading(false);
    setAiAnalyzing(false);
  };

  const handleCloseModal = () => {
    handleReset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    try {
      setLoading(true);
      setAiAnalyzing(true);

      const payload: CreateIncidentPayload = {
        title,
        description,
        source,
        type: type || undefined, // Optional: AI will classify if omitted
        location: {
          latitude: Number(latitude),
          longitude: Number(longitude),
          address,
        },
        address,
      };

      // POST /api/incidents
      const newInc = await incidentService.createIncident(payload, autoDedup);
      setCreatedIncident(newInc);
      onIncidentCreated?.();
      onCreated?.(newInc);
    } catch (err: any) {
      console.error('Failed to create incident:', err);
      alert('Error creating incident: ' + (err.message || 'Please check network connection.'));
    } finally {
      setLoading(false);
      setAiAnalyzing(false);
    }
  };

  const aiAnalysis = (createdIncident?.ai_analysis || {}) as Partial<AIAnalysis>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl overflow-hidden my-auto">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-600 rounded-lg text-white shadow-2xs">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-wide">
                Log Emergency Incident
              </h3>
              <p className="text-xs text-slate-500">
                Command triage ingestion with 3-signal deduplication & AI classification
              </p>
            </div>
          </div>
          <button
            onClick={handleCloseModal}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5 custom-scrollbar text-xs font-mono">
          {/* Post-Creation AI Triage Display */}
          {createdIncident ? (
            <div className="space-y-4 animate-in fade-in zoom-in-95 duration-200">
              <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    <h4 className="text-sm font-bold text-emerald-300">
                      Incident Ingested: {createdIncident.incident_id}
                    </h4>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <PriorityBadge priority={createdIncident.priority} />
                    <SeverityBadge severity={createdIncident.severity} />
                  </div>
                </div>
                <p className="text-slate-300 font-sans">{createdIncident.title}</p>
              </div>

              {/* AI Analysis Card */}
              <div className="rounded-xl border border-cyan-800/70 bg-gradient-to-br from-cyan-950/40 to-slate-950 p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-cyan-900/60 pb-2">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-cyan-400 animate-pulse" />
                    <span className="font-bold text-cyan-300 uppercase tracking-wider">
                      AI Incident Intelligence Report
                    </span>
                  </div>
                  {aiAnalysis.confidence !== undefined && (
                    <span className="bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800 text-[10px]">
                      Confidence: {(aiAnalysis.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block">Classified Type</span>
                    <span className="font-bold text-white capitalize">{createdIncident.type}</span>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block">Severity Level</span>
                    <span className="font-bold text-red-400">{createdIncident.severity}</span>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block">Priority Rank</span>
                    <span className="font-bold text-amber-400">{createdIncident.priority}</span>
                  </div>
                </div>

                {aiAnalysis.summary && (
                  <div className="bg-slate-900/90 p-2.5 rounded border border-slate-800 text-slate-300 font-sans">
                    <p className="font-bold text-slate-400 text-[10px] uppercase mb-1 font-mono">
                      Executive Summary
                    </p>
                    <p className="text-xs leading-relaxed">{aiAnalysis.summary}</p>
                  </div>
                )}

                {/* Recommended Resources */}
                {aiAnalysis.recommended_resources && aiAnalysis.recommended_resources.length > 0 && (
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">
                      🚒 Recommended Units:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {aiAnalysis.recommended_resources.map((unit, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]"
                        >
                          {unit}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Immediate Actions */}
                {aiAnalysis.immediate_actions && aiAnalysis.immediate_actions.length > 0 && (
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">
                      ⚡ Immediate Tactical Actions:
                    </span>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-300 font-sans text-xs">
                      {aiAnalysis.immediate_actions.map((act, i) => (
                        <li key={i}>{act}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all shadow-lg shadow-cyan-950"
                >
                  Done & View in Console
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Scenario Quick Pre-fills */}
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 mb-1.5 block">
                  Quick Tactical Scenarios
                </span>
                <div className="grid grid-cols-2 gap-2">
                  {PRESET_SCENARIOS.map((sc, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleApplyPreset(sc)}
                      className="text-left p-2 rounded-lg border border-slate-800 bg-slate-950/60 hover:border-cyan-800 hover:bg-slate-900 transition-all group"
                    >
                      <span className="font-bold text-slate-200 group-hover:text-cyan-300 truncate block">
                        {sc.title}
                      </span>
                      <span className="text-[10px] text-slate-500 capitalize">{sc.type}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-slate-400 uppercase font-bold text-[10px] mb-1">
                  Incident Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="E.g., Structural collapse with trapped civilians"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-slate-400 uppercase font-bold text-[10px] mb-1">
                  Description & Caller Report *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detail the emergency situation, visible hazards, injuries, number of people at risk..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none font-sans"
                />
              </div>

              {/* Source & Incident Type (Optional) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 uppercase font-bold text-[10px] mb-1">
                    Ingestion Source
                  </label>
                  <select
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="call_center">Call Center (911 / 112)</option>
                    <option value="citizen">Citizen App Report</option>
                    <option value="field_team">Field Officer / Responder</option>
                    <option value="iot">IoT Sensor Trigger</option>
                    <option value="hospital">Hospital Trauma Center</option>
                    <option value="government">Government / Civil Agency</option>
                    <option value="simulation">Simulation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 uppercase font-bold text-[10px] mb-1">
                    Incident Type <span className="text-slate-500">(Optional - AI will classify)</span>
                  </label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="">Let AI Auto-Detect Type</option>
                    <option value="fire">Fire</option>
                    <option value="flood">Flood</option>
                    <option value="road_accident">Road Accident</option>
                    <option value="medical_emergency">Medical Emergency</option>
                    <option value="industrial_hazard">Industrial Hazard</option>
                    <option value="building_collapse">Building Collapse</option>
                    <option value="gas_leak">Gas Leak</option>
                    <option value="earthquake">Earthquake</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* Coordinates & Address */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-3">
                <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                  <MapPin className="h-3 w-3 text-cyan-400" />
                  <span>Geospatial Coordinates (MongoDB GeoJSON)</span>
                </span>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-500 text-[10px] mb-0.5">Latitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-white focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-500 text-[10px] mb-0.5">Longitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-white focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-500 text-[10px] mb-0.5">Address / Landmark</label>
                  <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-white focus:outline-none"
                  />
                </div>
              </div>

              {/* Deduplication Toggle */}
              <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 p-2.5 text-slate-400">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-purple-400" />
                  <span>Auto-detect and merge duplicates (1km, 45min, 80% similarity)</span>
                </div>
                <input
                  type="checkbox"
                  checked={autoDedup}
                  onChange={(e) => setAutoDedup(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
                />
              </div>

              {/* Submit / Loading Indicator */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-800">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-3 py-1.5 rounded text-slate-400 hover:text-white"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold transition-all shadow-lg shadow-red-950 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-white" />
                      <span>{aiAnalyzing ? 'AI analyzing incident...' : 'Submitting to dispatch...'}</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      <span>Ingest Emergency</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportIncidentModal;
