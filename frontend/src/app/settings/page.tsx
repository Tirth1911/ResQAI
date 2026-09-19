'use client';

import React, { useEffect, useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopHeader } from '@/components/layout/TopHeader';
import { analyticsService } from '@/services/analyticsService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { SystemHealth } from '@/types';
import { API_BASE_URL, WS_BASE_URL } from '@/lib/constants';
import { Settings, Database, Activity, Cpu, ShieldCheck, Radio } from 'lucide-react';

export default function SettingsPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents();

  useEffect(() => {
    analyticsService
      .getHealth()
      .then((h) => setHealth(h))
      .catch((e) => console.error(e))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100 antialiased">
      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">
        <TopHeader
          wsStatus={wsStatus}
          wsConnected={wsConnected}
          systemStatus="ONLINE"
          activeIncidentsCount={0}
          criticalIncidentsCount={0}
          availableResourcesCount={0}
        />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {/* Header */}
          <div>
            <h2 className="text-xl font-black tracking-wider text-white font-mono flex items-center gap-2">
              <Settings className="h-5 w-5 text-cyan-400" />
              <span>System Topology & Telemetry Settings</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Infrastructure diagnostics, MongoDB geospatial clustering indexes, and runtime configuration
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Database & Storage */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                <Database className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-white font-mono">
                  Primary Datastore: MongoDB
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono text-slate-300">
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Engine Type:</span>
                  <span className="font-bold text-emerald-400">
                    {health?.database?.type || 'MongoDB 7.0+ (Atlas/Local)'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Connection State:</span>
                  <span className="font-bold text-emerald-400">
                    {health?.database?.connected ? 'CONNECTED' : 'ONLINE (Local Replica/Standalone)'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Database Name:</span>
                  <span className="text-cyan-400">
                    {health?.database?.database_name || 'resqai'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Spatial Indexing:</span>
                  <span className="text-white">2dsphere (incidents, resources, hospitals)</span>
                </div>
              </div>
            </div>

            {/* Network Endpoints */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                <Radio className="h-5 w-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-white font-mono">
                  API & WebSocket Gateways
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono text-slate-300">
                <div className="flex flex-col gap-1 border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">NEXT_PUBLIC_API_URL:</span>
                  <span className="text-cyan-400 break-all bg-slate-950 p-1.5 rounded border border-slate-800">
                    {API_BASE_URL}
                  </span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-slate-500">NEXT_PUBLIC_WS_URL:</span>
                  <span className="text-cyan-400 break-all bg-slate-950 p-1.5 rounded border border-slate-800">
                    {WS_BASE_URL}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Incident Intelligence */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                <Cpu className="h-5 w-5 text-purple-400" />
                <h3 className="text-sm font-bold text-white font-mono">
                  AI Intelligence & Classification
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono text-slate-300">
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">AI Provider:</span>
                  <span className="text-purple-400 font-bold">Multi-Provider (Gemini / OpenAI / Fallback)</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Fallback Strategy:</span>
                  <span className="text-white">Deterministic Rule & Keyword Triage Engine</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Output Schema:</span>
                  <span className="text-white">Pydantic Structured JSON Validation</span>
                </div>
              </div>
            </div>

            {/* Deduplication & Matching Parameters */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                <ShieldCheck className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold text-white font-mono">
                  Deduplication & Dispatch Rules
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono text-slate-300">
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Distance Threshold:</span>
                  <span className="text-amber-400 font-bold">&le; 1.0 km (Geospatial $near)</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Time Window:</span>
                  <span className="text-amber-400 font-bold">&le; 45 minutes</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-slate-500">Text Similarity Threshold:</span>
                  <span className="text-amber-400 font-bold">&ge; 0.80 Cosine TF-IDF</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Dispatch Scoring:</span>
                  <span className="text-white">0.50 Dist + 0.30 Cap + 0.20 Read</span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
