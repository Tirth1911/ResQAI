'use client';

import React from 'react';
import { ResourceRecommendation as RecommendationType } from '@/types';
import { Truck, Sparkles, Navigation, CheckCircle2, Shield } from 'lucide-react';

interface ResourceRecommendationProps {
  recommendation: RecommendationType;
  onAssign?: (recommendation: RecommendationType) => void;
  isAssigning?: boolean;
}

export function ResourceRecommendation({
  recommendation,
  onAssign,
  isAssigning = false,
}: ResourceRecommendationProps) {
  const categoryIcons: Record<string, string> = {
    AMBULANCE: '🚑',
    FIRE_TRUCK: '🚒',
    POLICE: '🚓',
    RESCUE_BOAT: '🚤',
    HAZMAT: '☣️',
    HEAVY_RESCUE: '🏗️',
    DRONE: '🛸',
    HELICOPTER: '🚁',
    OTHER: '🚚',
  };

  const icon = categoryIcons[recommendation.category?.toUpperCase()] || '🚒';

  // Format percentages
  const capabilityMatchPercent = Math.round((recommendation.capability_match || 0) * 100);
  const readinessPercent = Math.round((recommendation.readiness || 0) * 100);
  const overallScorePercent = Math.round((recommendation.score || 0) * 100);

  return (
    <div className="relative overflow-hidden rounded-xl border border-cyan-800/80 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/30 p-4 shadow-xl transition-all duration-200 hover:border-cyan-500/80 font-mono text-xs">
      {/* Top Banner: Name, Category, Overall Match Score */}
      <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-3 mb-3">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl" title={recommendation.category}>
            {icon}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-sans font-bold text-white text-sm">
                {recommendation.name}
              </h4>
              <span className="text-[10px] text-cyan-400 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
                {recommendation.resource_id}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 capitalize mt-0.5">
              Category: <span className="text-slate-200">{recommendation.category?.toLowerCase().replace(/_/g, ' ')}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold">
            Match Score
          </span>
          <span className="text-lg font-black text-cyan-300 font-mono">
            {overallScorePercent}%
          </span>
        </div>
      </div>

      {/* 3 Metric Signals Grid: Distance, Capability Match, Readiness */}
      <div className="grid grid-cols-3 gap-2 text-center mb-3">
        <div className="rounded-lg bg-slate-950/80 p-2 border border-slate-800">
          <span className="text-slate-500 text-[10px] block">Distance</span>
          <span className="text-white font-bold text-xs flex items-center justify-center gap-1 mt-0.5">
            <Navigation className="h-3 w-3 text-cyan-400" />
            <span>{recommendation.distance_km} km</span>
          </span>
        </div>

        <div className="rounded-lg bg-slate-950/80 p-2 border border-slate-800">
          <span className="text-slate-500 text-[10px] block">Capability Match</span>
          <span className="text-emerald-400 font-bold text-xs flex items-center justify-center gap-1 mt-0.5">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            <span>{capabilityMatchPercent}%</span>
          </span>
        </div>

        <div className="rounded-lg bg-slate-950/80 p-2 border border-slate-800">
          <span className="text-slate-500 text-[10px] block">Readiness</span>
          <span className="text-amber-400 font-bold text-xs flex items-center justify-center gap-1 mt-0.5">
            <Shield className="h-3 w-3 text-amber-400" />
            <span>{readinessPercent}%</span>
          </span>
        </div>
      </div>

      {/* AI Recommendation Reasoning */}
      {recommendation.reason && (
        <div className="rounded-lg bg-cyan-950/30 p-2.5 border border-cyan-900/60 mb-3 text-[11px] text-slate-300 italic flex items-start gap-2">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400 shrink-0 mt-0.5" />
          <p className="leading-snug">{recommendation.reason}</p>
        </div>
      )}

      {/* Capabilities Tags */}
      {recommendation.capabilities && recommendation.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {recommendation.capabilities.map((cap, idx) => (
            <span
              key={idx}
              className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 font-mono"
            >
              {cap.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Assign Button */}
      {onAssign && (
        <button
          type="button"
          onClick={() => onAssign(recommendation)}
          disabled={isAssigning}
          className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-950 disabled:opacity-50 uppercase tracking-wider"
        >
          <Truck className="h-3.5 w-3.5" />
          <span>{isAssigning ? 'Assigning Unit...' : 'Assign Unit to Call'}</span>
        </button>
      )}
    </div>
  );
}

export default ResourceRecommendation;
