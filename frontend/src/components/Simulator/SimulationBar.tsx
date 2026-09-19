'use client';

import React, { useState } from 'react';
import { analyticsService } from '@/services/analyticsService';
import { Zap, Layers, Flame, Truck, Waves, ShieldAlert, Sparkles } from 'lucide-react';

interface SimulationBarProps {
  onSimulationDispatched: () => void;
}

const SCENARIOS = [
  { index: 0, title: 'Sanand Chemical Fire', icon: '🔥', type: 'Industrial' },
  { index: 1, title: 'NE1 Expressway Pileup', icon: '🚗', type: 'Road Accident' },
  { index: 2, title: 'Vadodara Flood Inundation', icon: '🌊', type: 'Flood' },
  { index: 3, title: 'Maninagar LPG Gas Leak', icon: '☣️', type: 'Hazard' },
];

export const SimulationBar: React.FC<SimulationBarProps> = ({ onSimulationDispatched }) => {
  const [duplicateMode, setDuplicateMode] = useState(false);
  const [triggeringIndex, setTriggeringIndex] = useState<number | null>(null);
  const [lastDispatchedInfo, setLastDispatchedInfo] = useState<string | null>(null);

  const handleTrigger = async (index: number) => {
    try {
      setTriggeringIndex(index);
      const res = await analyticsService.triggerSimulation(index, duplicateMode);
      setLastDispatchedInfo(
        res.is_duplicate_merged
          ? `Merged as duplicate into ${res.incident.incident_id}`
          : `Dispatched: ${res.incident.incident_id}`
      );
      onSimulationDispatched();
    } catch (err) {
      console.error('Simulation trigger failed:', err);
    } finally {
      setTriggeringIndex(null);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-3">
      <div className="flex items-center space-x-2">
        <div className="p-1.5 rounded-lg bg-red-950 border border-red-800 text-red-400">
          <Zap className="h-4 w-4" />
        </div>
        <div>
          <div className="text-xs font-bold text-white flex items-center space-x-1.5">
            <span>Crisis Simulator & Live Stress-Test</span>
            <span className="text-[10px] font-mono text-purple-400 bg-purple-950 border border-purple-800 px-1.5 py-0.2 rounded">
              Demo Tool
            </span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            Trigger real-time disaster events to test AI triage & deduplication engine
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Toggle Duplicate */}
        <label className="flex items-center space-x-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 cursor-pointer hover:border-purple-600 transition-colors">
          <input
            type="checkbox"
            checked={duplicateMode}
            onChange={(e) => setDuplicateMode(e.target.checked)}
            className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500"
          />
          <span className={duplicateMode ? 'text-purple-400 font-bold' : ''}>
            Simulate Duplicate Call
          </span>
        </label>

        {/* Scenarios */}
        {SCENARIOS.map((sc) => {
          const isTriggering = triggeringIndex === sc.index;
          return (
            <button
              key={sc.index}
              onClick={() => handleTrigger(sc.index)}
              disabled={isTriggering}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all active:scale-95 flex items-center space-x-1.5 ${
                duplicateMode
                  ? 'bg-purple-950/80 hover:bg-purple-900 border-purple-700 text-purple-200'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-white'
              }`}
            >
              <span>{sc.icon}</span>
              <span className="hidden sm:inline">{sc.title}</span>
              <span className="sm:hidden">{sc.type}</span>
              {isTriggering && <span className="animate-spin text-[10px]">⌛</span>}
            </button>
          );
        })}
      </div>

      {lastDispatchedInfo && (
        <div className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-800 truncate max-w-[240px]">
          ✓ {lastDispatchedInfo}
        </div>
      )}
    </div>
  );
};
