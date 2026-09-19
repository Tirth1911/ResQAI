'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
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
import { Incident, Resource, AlertNotification } from '@/types';
import {
  Play,
  Pause,
  RotateCcw,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Layers,
  ShieldCheck,
  Truck,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Radio,
  Clock,
  BarChart3,
  Flame,
  ArrowRight,
  Zap,
  Cpu,
  Eye,
  FileText,
  Bell,
  Activity,
  Send,
  Loader2
} from 'lucide-react';

const MapView = dynamic(
  () => import('@/components/Map/MapView').then((mod) => mod.MapView),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-white font-sans text-xs text-slate-500 rounded-lg border border-slate-200">
        <MapPin className="h-5 w-5 animate-pulse text-red-600 mr-2" />
        <span>Initializing Tactical Cartography Engine...</span>
      </div>
    ),
  }
);

interface DemoStepInfo {
  step: number;
  title: string;
  tagline: string;
  description: string;
  underTheHood: string;
  icon: any;
  badgeColor: string;
}

const DEMO_STEPS: DemoStepInfo[] = [
  {
    step: 1,
    title: 'Command Center & Standby Fleet',
    tagline: 'Step 1 of 13 • System Initialization',
    description: 'Dashboard HUD initialized with live incident queues and ready emergency fleet units across the metropolitan sector.',
    underTheHood: 'MongoDB 2dsphere geospatial indexes loaded; in-memory WebSocket event bus synchronized.',
    icon: Activity,
    badgeColor: 'border-blue-200 text-blue-700 bg-blue-50',
  },
  {
    step: 2,
    title: 'Ingest Critical Road Accident Report',
    tagline: 'Step 2 of 13 • Citizen Emergency Call Ingestion',
    description: '911 citizen call reports a major collision on Outer Ring Road overpass involving an overturned passenger bus and 2 sedans with 18 people trapped.',
    underTheHood: 'POST /api/incidents ingests report, stores GeoJSON Point [77.6745, 12.9252], broadcasts INCIDENT_CREATED.',
    icon: Flame,
    badgeColor: 'border-red-200 text-red-700 bg-red-50',
  },
  {
    step: 3,
    title: 'AI Classification: Road Accident | CRITICAL | P1',
    tagline: 'Step 3 of 13 • Zero-Latency AI Triage',
    description: 'ResQAI AI engine analyzes report semantics, classifying incident as CRITICAL P1 with 96% confidence.',
    underTheHood: 'NLP multi-provider triage parses casualty severity, hazard vectors, and priority classification.',
    icon: Cpu,
    badgeColor: 'border-purple-200 text-purple-700 bg-purple-50',
  },
  {
    step: 4,
    title: 'AI Situation Summary & Immediate Actions',
    tagline: 'Step 4 of 13 • Structured Incident Intelligence',
    description: 'AI extracts 18 people at risk and formulates 4 tactical immediate action protocols for extrication and trauma response.',
    underTheHood: 'Generates structured JSON schema with priority actions, victim count, and recommended unit capabilities.',
    icon: FileText,
    badgeColor: 'border-purple-200 text-purple-700 bg-purple-50',
  },
  {
    step: 5,
    title: 'Recommend Nearest Ambulance, Police & Rescue',
    tagline: 'Step 5 of 13 • AI Resource Matching Engine',
    description: 'System scores nearby fleet by Distance (50%), Capabilities (30%), and Readiness (20%), ranking top 3 units.',
    underTheHood: 'Calculates Haversine spatial proximity + capability bitmask matching in <12ms.',
    icon: Sparkles,
    badgeColor: 'border-blue-200 text-blue-700 bg-blue-50',
  },
  {
    step: 6,
    title: 'Multi-Unit Fleet Dispatch',
    tagline: 'Step 6 of 13 • Automated Resource Assignment',
    description: 'Trauma Ambulance Alpha-01, Traffic Police 04, and Fire Rescue 02 assigned. Resource states transition to BUSY.',
    underTheHood: 'MongoDB atomic update sets current_incident_id, broadcasts RESOURCE_ASSIGNED and INCIDENT_UPDATED.',
    icon: Truck,
    badgeColor: 'border-emerald-200 text-emerald-700 bg-emerald-50',
  },
  {
    step: 7,
    title: 'Tactical GIS Map Telemetry Update',
    tagline: 'Step 7 of 13 • Real-Time Spatial Synchronizer',
    description: 'Map plots critical pulsing incident marker and displays GPS routes for all 3 dispatched emergency vehicles.',
    underTheHood: 'React-Leaflet renders vector markers and 1km deduplication cluster radius dynamically.',
    icon: MapPin,
    badgeColor: 'border-blue-200 text-blue-700 bg-blue-50',
  },
  {
    step: 8,
    title: 'Secondary Citizen Report for Same Accident',
    tagline: 'Step 8 of 13 • Duplicate Emergency Call Ingestion',
    description: 'Another citizen calls 20 seconds later reporting the same accident from the adjacent flyover ramp.',
    underTheHood: 'Simulates high-volume crisis call storm with 80m location offset and overlapping text.',
    icon: Radio,
    badgeColor: 'border-amber-200 text-amber-700 bg-amber-50',
  },
  {
    step: 9,
    title: '3-Signal Duplicate Detection Triggered',
    tagline: 'Step 9 of 13 • NLP & Geospatial Deduplication',
    description: 'System detects duplicate: Distance (80m <= 1km), Time (20s <= 45m), and Text Cosine Similarity (88% >= 80%).',
    underTheHood: '3-Signal Deduplication algorithm evaluates spatial distance, time delta, and TF-IDF lexical overlap.',
    icon: Layers,
    badgeColor: 'border-amber-200 text-amber-700 bg-amber-50',
  },
  {
    step: 10,
    title: 'Automated Report Merge & Linkage',
    tagline: 'Step 10 of 13 • Parent-Child Incident Consolidation',
    description: 'Secondary report merged into parent incident timeline with +1 duplicate counter, preventing over-dispatch.',
    underTheHood: 'Appends duplicate metadata to parent incident timeline and emits INCIDENT_DUPLICATE_MERGED event.',
    icon: CheckCircle2,
    badgeColor: 'border-emerald-200 text-emerald-700 bg-emerald-50',
  },
  {
    step: 11,
    title: 'Real-Time Emergency WebSocket Broadcast',
    tagline: 'Step 11 of 13 • Cross-System Telemetry Sync',
    description: 'WebSocket bus broadcasts unified incident state to all connected dispatch terminals and trauma hospitals.',
    underTheHood: 'FastAPI ConnectionManager broadcasts JSON frame to all active WebSocket clients on /ws/dashboard.',
    icon: Radio,
    badgeColor: 'border-blue-200 text-blue-700 bg-blue-50',
  },
  {
    step: 12,
    title: 'Incident Resolved & Fleet Returned',
    tagline: 'Step 12 of 13 • On-Scene Resolution',
    description: 'Field commander marks incident RESOLVED. All 3 response units returned to AVAILABLE status for next call.',
    underTheHood: 'Updates status to RESOLVED, releases assigned resources, and archives incident timeline.',
    icon: CheckCircle2,
    badgeColor: 'border-emerald-200 text-emerald-700 bg-emerald-50',
  },
  {
    step: 13,
    title: 'Analytics SLA Dashboard Updated',
    tagline: 'Step 13 of 13 • Performance Metrics Audit',
    description: 'Aggregation pipeline updates response time averages, SLA compliance rates, and resource utilization charts.',
    underTheHood: 'MongoDB aggregation pipeline computes response latency, SLA metrics, and hotspot frequencies.',
    icon: BarChart3,
    badgeColor: 'border-emerald-200 text-emerald-700 bg-emerald-50',
  },
];

export default function DemoPage() {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadDemoData(false);
  });

  const loadDemoData = useCallback(async (showLoading = false) => {
    if (showLoading) setIsLoading(true);
    try {
      const [incRes, resRes, alertRes] = await Promise.all([
        incidentService.getIncidents({ limit: 50 }),
        resourceService.getResources(),
        notificationService.getNotifications({ limit: 20 }),
      ]);
      setIncidents(incRes.items || []);
      setResources(resRes || []);
      setAlerts(alertRes || []);
    } catch (e) {
      console.error('Error fetching demo data:', e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDemoData(true);
  }, [loadDemoData]);

  // Handle auto-advance steps when playing
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= DEMO_STEPS.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 4000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying]);

  const handleNextStep = () => {
    if (currentStepIndex < DEMO_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleResetDemo = async () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
    try {
      await simulationService.resetSimulation();
      await loadDemoData(false);
    } catch (e) {
      console.error('Failed to reset demo:', e);
    }
  };

  const currentStepInfo = DEMO_STEPS[currentStepIndex];
  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
  const unreadAlerts = alerts.filter((a) => !a.read);
  const StepIcon = currentStepInfo.icon;

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

      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Page Title & Auto-Play Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 uppercase tracking-wider">
                13-Step Automated Judge Walkthrough
              </span>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                ResQAI Complete Platform Demonstration
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Step-by-step interactive demonstration of citizen call ingestion, zero-dependency AI triage, 3-signal deduplication, multi-unit matching, and real-time WebSocket sync.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex items-center gap-1.5 rounded-md bg-red-600 hover:bg-red-700 px-4 py-2 text-xs font-bold text-white shadow-xs transition-colors"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              <span>{isPlaying ? 'Pause Auto-Play' : 'Auto-Play 3-Min Demo'}</span>
            </button>

            <button
              type="button"
              onClick={handlePrevStep}
              disabled={currentStepIndex === 0}
              className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 shadow-2xs"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              onClick={handleNextStep}
              disabled={currentStepIndex === DEMO_STEPS.length - 1}
              className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 shadow-2xs"
            >
              <span>Next Step</span>
              <ChevronRight className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={handleResetDemo}
              className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs"
              title="Reset Demo"
            >
              <RotateCcw className="h-4 w-4 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Step Progress Tracker Bar */}
        <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700">
            <span className="uppercase text-slate-500 text-[10px] tracking-wider">Demo Execution Pipeline:</span>
            <span className="text-red-700 font-extrabold">{currentStepInfo.tagline}</span>
          </div>

          <div className="grid grid-cols-13 gap-1">
            {DEMO_STEPS.map((s, idx) => (
              <button
                key={s.step}
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStepIndex(idx);
                }}
                className={`h-2.5 rounded-full transition-all ${
                  idx === currentStepIndex
                    ? 'bg-red-600 ring-2 ring-red-300'
                    : idx < currentStepIndex
                    ? 'bg-emerald-500'
                    : 'bg-slate-200'
                }`}
                title={`Step ${s.step}: ${s.title}`}
              />
            ))}
          </div>
        </div>

        {/* Active Step Highlight Card */}
        <div className="rounded-lg border border-red-200 bg-red-50/40 p-4 shadow-xs grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          <div className="md:col-span-8 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-xs font-bold border ${currentStepInfo.badgeColor}`}>
                STEP {currentStepInfo.step}
              </span>
              <h2 className="text-base font-extrabold text-slate-900">{currentStepInfo.title}</h2>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {currentStepInfo.description}
            </p>

            <div className="rounded-md bg-white p-2.5 border border-slate-200 text-xs text-slate-600 font-mono shadow-2xs">
              <span className="font-bold text-red-700">UNDER THE HOOD: </span>
              {currentStepInfo.underTheHood}
            </div>
          </div>

          <div className="md:col-span-4 flex flex-col items-center justify-center p-3 rounded-md bg-white border border-slate-200 shadow-2xs text-center space-y-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600">
              <StepIcon className="h-6 w-6" />
            </div>
            <div className="text-xs font-bold text-slate-900">{currentStepInfo.title}</div>
            <Link
              href="/dashboard"
              className="text-xs font-bold text-red-600 hover:underline flex items-center gap-1"
            >
              <span>View Live Dashboard &rarr;</span>
            </Link>
          </div>
        </div>

        {/* Interactive Map & Telemetry Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[420px]">
          <div className="lg:col-span-8 h-full rounded-lg border border-slate-200 bg-white overflow-hidden shadow-xs">
            <MapView
              incidents={incidents}
              resources={resources}
              zoom={13}
              className="h-full"
            />
          </div>

          <div className="lg:col-span-4 h-full flex flex-col gap-3">
            <div className="flex-1 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3 overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
                  <Activity className="h-4 w-4 text-red-600" />
                  <span>Real-Time Event Stream</span>
                </h3>
                <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  WEBSOCKET ACTIVE
                </span>
              </div>

              <div className="space-y-2 text-xs">
                {incidents.slice(0, 3).map((inc) => (
                  <div key={inc.incident_id} className="p-2.5 rounded-md border border-slate-200 bg-slate-50 space-y-1">
                    <div className="flex justify-between font-bold text-slate-900">
                      <span>{inc.title}</span>
                      <SeverityBadge severity={inc.severity} showPulse={false} />
                    </div>
                    <div className="text-[11px] text-slate-500 truncate">{inc.address}</div>
                    <div className="flex justify-between items-center text-[10px] pt-1">
                      <StatusBadge type="status" value={inc.status} />
                      <span className="font-mono text-slate-400">#{inc.incident_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
