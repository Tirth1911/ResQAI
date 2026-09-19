'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import Link from 'next/link';
import { TopHeader } from '@/components/layout/TopHeader';
import { SeverityBadge } from '@/components/common/SeverityBadge';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { StatusBadge } from '@/components/StatusBadge';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { simulationService } from '@/services/simulationService';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { notificationService } from '@/services/notificationService';
import {
  SimulationStatus,
  SimulationLog,
  SimulationScenario,
  Incident,
  Resource,
  AlertNotification,
} from '@/types';
import {
  Play,
  Square,
  RotateCcw,
  Zap,
  Flame,
  Car,
  Waves,
  HeartPulse,
  Biohazard,
  Layers,
  Terminal,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Radio,
  ArrowRight,
  Sparkles,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
  Sliders,
  Filter,
  Check,
  MapPin,
  FileText,
  Percent,
  GitMerge,
  Loader2
} from 'lucide-react';

const SCENARIOS = [
  {
    id: 'road_accident',
    title: 'Major Highway Collision & Pileup',
    type: 'road_accident',
    severity: 'CRITICAL',
    priority: 'P1',
    icon: Car,
    location: 'Outer Ring Road Junction, Bellandur, Bangalore',
    description:
      'Multi-vehicle highway pileup involving passenger bus and sedans. Overturned vehicle, 18 people at risk, fuel leak blocking lanes.',
    duplicatePreview:
      'Secondary citizen call 20s later at same flyover merged automatically via 3-Signal NLP & Geo engine.',
  },
  {
    id: 'building_fire',
    title: 'Commercial High-Rise Structural Fire',
    type: 'fire',
    severity: 'CRITICAL',
    priority: 'P1',
    icon: Flame,
    location: 'Tech Zone Tower B, Electronic City Phase 1, Bangalore',
    description:
      '5th floor electrical fire with vertical smoke funneling. 65 occupants trapped on terrace awaiting hydraulic ladder evacuation.',
    duplicatePreview:
      'IoT smoke detector followed by citizen video report merged with 98% spatial/temporal confidence.',
  },
  {
    id: 'urban_flood',
    title: 'Severe Flash Flood & Canal Breach',
    type: 'flood',
    severity: 'HIGH',
    priority: 'P2',
    icon: Waves,
    location: 'BTM Layout 2nd Stage Canal Sector, Bangalore',
    description:
      'Stormwater canal overflowed into residential quarter. 4.5ft water submerging ground floor residences, elderly citizens need rescue boats.',
    duplicatePreview:
      'Multiple citizen 911 calls within 100m corridor deduplicated and merged to prevent fleet over-dispatch.',
  },
  {
    id: 'medical_emergency',
    title: 'Mass Heat Exhaustion & Cardiac Crisis',
    type: 'medical_emergency',
    severity: 'CRITICAL',
    priority: 'P1',
    icon: HeartPulse,
    location: 'Cubbon Park Pavilion Sports Complex, Bangalore',
    description:
      'Massive heat stroke wave and cardiac distress at city marathon finish line. 4 runners unconscious requiring immediate ALS defibrillation.',
    duplicatePreview:
      'Call center hotline duplicate call merged into single incident with priority green corridor routing.',
  },
  {
    id: 'gas_leak',
    title: 'Industrial Ammonia Chemical Gas Leak',
    type: 'gas_leak',
    severity: 'CRITICAL',
    priority: 'P1',
    icon: Biohazard,
    location: 'Peenya Industrial Complex Block B, Bangalore',
    description:
      'High-pressure ammonia storage valve rupture releasing toxic yellow gas plume. Downwind mandatory evacuation and HAZMAT response required.',
    duplicatePreview:
      'Nearby plant manager emergency call linked and merged into parent hazard event.',
  },
];

const PIPELINE_STAGES = [
  { key: 'REPORT_INGESTION', label: '1. Ingest Report', icon: Radio },
  { key: 'AI_TRIAGE', label: '2. AI Triage & NLP', icon: Sparkles },
  { key: 'DUPLICATE_DETECTION', label: '3. 3-Signal Dedup', icon: Layers },
  { key: 'RESOURCE_RECOMMENDATION', label: '4. AI Matching', icon: Sliders },
  { key: 'RESOURCE_ASSIGNMENT', label: '5. Unit Dispatch', icon: ShieldAlert },
  { key: 'IN_PROGRESS', label: '6. Field On-Scene', icon: Clock },
  { key: 'RESOLUTION', label: '7. Crisis Resolved', icon: CheckCircle2 },
];

export default function SimulationPage() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('road_accident');
  const [autoPlayAll, setAutoPlayAll] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1.5);

  const [simStatus, setSimStatus] = useState<SimulationStatus | null>(null);
  const [logsFilter, setLogsFilter] = useState<string>('ALL');
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [isStopping, setIsStopping] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);

  // App metrics for TopHeader
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    refreshSimStatus();
    loadHeaderMetrics();
  });

  const logsEndRef = useRef<HTMLDivElement | null>(null);

  const refreshSimStatus = useCallback(async () => {
    try {
      const status = await simulationService.getSimulationStatus();
      setSimStatus(status);
    } catch (e) {
      console.error('Error fetching sim status:', e);
    }
  }, []);

  const loadHeaderMetrics = async () => {
    try {
      const [incList, resList, alertList] = await Promise.all([
        incidentService.getIncidents({ limit: 50 }),
        resourceService.getResources(),
        notificationService.getNotifications({ limit: 20 }),
      ]);
      setIncidents(incList.items || []);
      setResources(resList || []);
      setAlerts(alertList || []);
    } catch (e) {
      console.error('Error loading header metrics:', e);
    }
  };

  useEffect(() => {
    refreshSimStatus();
    loadHeaderMetrics();
  }, [refreshSimStatus]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [simStatus?.logs]);

  const handleStartSim = async () => {
    setIsStarting(true);
    try {
      const status = await simulationService.startSimulation({
        scenario_id: selectedScenarioId,
        auto_play_all: autoPlayAll,
        speed_multiplier: speedMultiplier,
        step_delay_seconds: 2.0,
      });
      setSimStatus(status);
    } catch (e) {
      console.error('Failed to start scenario:', e);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopSim = async () => {
    setIsStopping(true);
    try {
      const status = await simulationService.stopSimulation();
      setSimStatus(status);
    } catch (e) {
      console.error('Failed to stop scenario:', e);
    } finally {
      setIsStopping(false);
    }
  };

  const handleResetSim = async () => {
    setIsResetting(true);
    try {
      const status = await simulationService.resetSimulation();
      setSimStatus(status);
      await loadHeaderMetrics();
    } catch (e) {
      console.error('Failed to reset simulation:', e);
    } finally {
      setIsResetting(false);
    }
  };

  const currentScenarioObj = SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0];
  const isRunning = simStatus?.is_running ?? false;
  const logs = simStatus?.logs || simStatus?.events_log || [];
  const currentStep = simStatus?.current_step ?? simStatus?.current_step_index ?? 0;
  const totalSteps = simStatus?.total_steps || 7;

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
  const unreadAlerts = alerts.filter((a) => !a.read);

  // Filter logs by level
  const filteredLogs = logs.filter((log: any) => {
    if (logsFilter === 'ALL') return true;
    const level = (log.level || log.severity || 'INFO').toUpperCase();
    return level === logsFilter.toUpperCase();
  });

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length}
        criticalIncidentsCount={criticalIncidents.length}
        availableResourcesCount={availableCount}
        unreadAlertsCount={unreadAlerts.length}
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white">
                <GitMerge className="h-4 w-4" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Multi-Source AI Ingestion & Deduplication
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Real-time 3-signal deduplication matrix comparing spatio-temporal radius, NLP cosine text similarity, and incident classification
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isRunning ? (
              <button
                type="button"
                onClick={handleStartSim}
                disabled={isStarting}
                className="flex items-center gap-1.5 rounded-md bg-red-600 hover:bg-red-700 px-4 py-2 text-xs font-bold text-white shadow-xs transition-colors disabled:opacity-50"
              >
                {isStarting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                <span>Execute AI Ingestion Engine</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStopSim}
                disabled={isStopping}
                className="flex items-center gap-1.5 rounded-md bg-amber-600 hover:bg-amber-700 px-4 py-2 text-xs font-bold text-white shadow-xs transition-colors disabled:opacity-50"
              >
                {isStopping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
                <span>Pause Scenario Execution</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleResetSim}
              disabled={isResetting}
              className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition-colors disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4 text-slate-500" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* AI Deduplication Comparison Panel: Incoming Report vs Existing Incidents */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left: Incoming Ingested Report Card */}
          <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-red-600 animate-pulse" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Incoming Report (Report #2026-B)
                </h3>
              </div>
              <span className="text-[10px] font-bold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                INCOMING CALL
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Scenario Title:</span>
                <span className="font-bold text-slate-900">{currentScenarioObj.title}</span>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Location:</span>
                <div className="flex items-center gap-1 text-slate-700">
                  <MapPin className="h-3.5 w-3.5 text-red-600 shrink-0" />
                  <span>{currentScenarioObj.location}</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Citizen Description:</span>
                <p className="rounded-md bg-slate-50 p-2.5 text-slate-700 border border-slate-200 leading-relaxed">
                  "{currentScenarioObj.description}"
                </p>
              </div>

              <div className="flex items-center justify-between pt-1">
                <SeverityBadge severity={currentScenarioObj.severity} showPulse={false} />
                <PriorityBadge priority={currentScenarioObj.priority} />
              </div>
            </div>
          </div>

          {/* Center: 3-Signal AI Deduplication Matching Matrix */}
          <div className="lg:col-span-7 rounded-lg border border-red-200 bg-red-50/40 p-4 shadow-xs flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between border-b border-red-100 pb-2.5">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-red-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                    Adaptive 3-Signal Match Score
                  </h3>
                </div>
                <span className="text-xs font-extrabold text-red-700 bg-white px-2.5 py-0.5 rounded border border-red-200 shadow-2xs">
                  94.2% Similarity Confidence
                </span>
              </div>

              {/* 4 Factor Breakdown */}
              <div className="grid grid-cols-2 gap-3 mt-3">
                {/* Location Similarity */}
                <div className="rounded-md bg-white p-3 border border-slate-200 shadow-2xs space-y-1">
                  <div className="flex justify-between text-xs font-bold text-slate-700">
                    <span>1. Location Distance</span>
                    <span className="text-red-700 font-extrabold">98% Match</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-red-600 rounded-full" style={{ width: '98%' }} />
                  </div>
                  <span className="text-[10px] text-slate-500 block">Within 0.35 km radius</span>
                </div>

                {/* Time Window Similarity */}
                <div className="rounded-md bg-white p-3 border border-slate-200 shadow-2xs space-y-1">
                  <div className="flex justify-between text-xs font-bold text-slate-700">
                    <span>2. Time Window</span>
                    <span className="text-red-700 font-extrabold">95% Match</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-red-600 rounded-full" style={{ width: '95%' }} />
                  </div>
                  <span className="text-[10px] text-slate-500 block">Within 3.5 minutes window</span>
                </div>

                {/* Type & Severity Similarity */}
                <div className="rounded-md bg-white p-3 border border-slate-200 shadow-2xs space-y-1">
                  <div className="flex justify-between text-xs font-bold text-slate-700">
                    <span>3. Incident Type Match</span>
                    <span className="text-emerald-700 font-extrabold">100% Match</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-600 rounded-full" style={{ width: '100%' }} />
                  </div>
                  <span className="text-[10px] text-slate-500 block">Identical hazard category</span>
                </div>

                {/* NLP Cosine Text Similarity */}
                <div className="rounded-md bg-white p-3 border border-slate-200 shadow-2xs space-y-1">
                  <div className="flex justify-between text-xs font-bold text-slate-700">
                    <span>4. NLP Text Cosine</span>
                    <span className="text-red-700 font-extrabold">89.5% Match</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-red-600 rounded-full" style={{ width: '89.5%' }} />
                  </div>
                  <span className="text-[10px] text-slate-500 block">High semantic vocabulary correlation</span>
                </div>
              </div>
            </div>

            {/* Deduplication Verdict Box */}
            <div className="rounded-md bg-white p-3 border border-red-200 shadow-2xs flex items-center justify-between">
              <div>
                <div className="flex items-center gap-1.5">
                  <GitMerge className="h-4 w-4 text-red-600" />
                  <span className="text-xs font-bold text-slate-900">VERDICT: POTENTIAL DUPLICATE DETECTED</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {currentScenarioObj.duplicatePreview}
                </p>
              </div>

              <button
                type="button"
                onClick={handleStartSim}
                disabled={isRunning}
                className="rounded bg-red-600 hover:bg-red-700 px-3 py-1.5 text-xs font-bold text-white shadow-2xs transition-colors shrink-0 disabled:opacity-50"
              >
                Auto-Merge Duplicate
              </button>
            </div>
          </div>
        </div>

        {/* Disaster Scenarios Selector Grid */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
            Select Test Disaster Scenario:
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {SCENARIOS.map((scen) => {
              const isSelected = scen.id === selectedScenarioId;
              const Icon = scen.icon;
              return (
                <div
                  key={scen.id}
                  onClick={() => !isRunning && setSelectedScenarioId(scen.id)}
                  className={`cursor-pointer rounded-lg border p-3 transition-all ${
                    isSelected
                      ? 'border-red-600 bg-white ring-1 ring-red-500 shadow-xs'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/60 shadow-2xs'
                  } ${isRunning ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`h-4 w-4 ${isSelected ? 'text-red-600' : 'text-slate-500'}`} />
                    <span className="font-bold text-xs text-slate-900 line-clamp-1">{scen.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 line-clamp-2 leading-normal">
                    {scen.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* 7-Stage Pipeline Visualizer */}
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Live Emergency Lifecycle Pipeline Progression
            </h3>
            <span className="text-xs font-semibold text-slate-500">
              Step {currentStep} of {totalSteps} Completed
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {PIPELINE_STAGES.map((stg, idx) => {
              const stageNum = idx + 1;
              const isPast = stageNum < currentStep;
              const isCurrent = stageNum === currentStep;

              return (
                <div
                  key={stg.key}
                  className={`rounded-md border p-2.5 text-center text-xs font-semibold transition-all ${
                    isCurrent
                      ? 'border-red-600 bg-red-50 text-red-700 shadow-2xs font-bold'
                      : isPast
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 bg-slate-50 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <stg.icon className={`h-3.5 w-3.5 ${isCurrent ? 'text-red-600' : isPast ? 'text-emerald-600' : 'text-slate-400'}`} />
                    <span className="text-[10px] uppercase font-bold">{stg.key.replace('_', ' ')}</span>
                  </div>
                  <span className="text-[11px] block">{stg.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Simulation Real-time Terminal Log Console */}
        <div className="rounded-lg border border-slate-900 bg-slate-950 p-4 shadow-md text-xs font-mono space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-emerald-400" />
              <span className="font-bold text-white uppercase tracking-wider">
                Emergency Engine Telemetry & Log Stream
              </span>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={logsFilter}
                onChange={(e) => setLogsFilter(e.target.value)}
                className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Log Levels</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>

          <div className="h-56 overflow-y-auto space-y-1.5 pr-2 custom-scrollbar text-[11px] text-slate-300 leading-relaxed">
            {filteredLogs.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-600">
                Engine idle. Click "Execute AI Ingestion Engine" to run crisis simulation.
              </div>
            ) : (
              filteredLogs.map((log: any, idx: number) => {
                const level = (log.level || log.severity || 'INFO').toUpperCase();
                const message = log.message || log.details || log.title || 'Simulation event';
                return (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-slate-500 shrink-0 font-mono">
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>
                    <span
                      className={`font-bold uppercase text-[10px] px-1 rounded shrink-0 ${
                        level === 'CRITICAL'
                          ? 'bg-red-950 text-red-400 border border-red-800'
                          : level === 'SUCCESS'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : level === 'WARNING'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}
                    >
                      {level}
                    </span>
                    <span className="text-slate-200">{message}</span>
                  </div>
                );
              })
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </main>
    </div>
  );
}
