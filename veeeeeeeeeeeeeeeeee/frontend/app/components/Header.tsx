'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  MapPin, 
  Flame, 
  Truck, 
  Activity, 
  Bell, 
  Play, 
  Pause,
  Sparkles,
  BarChart3,
  Layers
} from 'lucide-react';

interface HeaderProps {
  activeTab: 'map' | 'incidents' | 'fleet' | 'ingestion' | 'analytics';
  setActiveTab: (tab: 'map' | 'incidents' | 'fleet' | 'ingestion' | 'analytics') => void;
  unresolvedAlertCount: number;
  openAlertsModal: () => void;
  isSimulating: boolean;
  setIsSimulating: (val: boolean | ((prev: boolean) => boolean)) => void;
  activeIncidentsCount: number;
  availableFleetCount: number;
}

export default function Header({
  activeTab,
  setActiveTab,
  unresolvedAlertCount,
  openAlertsModal,
  isSimulating,
  setIsSimulating,
  activeIncidentsCount,
  availableFleetCount
}: HeaderProps) {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }) + ' IST');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-[#DED8CC] text-[#1F2933] sticky top-0 z-50 h-[72px] shadow-sm">
      <div className="max-w-[1700px] mx-auto px-6 h-full flex items-center justify-between gap-6">
        
        {/* Left: Logo & Sector Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#B42318] text-white shadow-sm font-black text-lg">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-[#1F2933]">
                  RES<span className="text-[#B42318]">QAI</span>
                </span>
                <span className="text-xs text-[#667085] font-medium border-l border-[#DED8CC] pl-2">
                  Emergency Intelligence Platform
                </span>
              </div>
              <div className="text-[11px] text-[#667085] flex items-center gap-2 mt-0.5">
                <span className="font-semibold text-[#1F2933]">SECTOR:</span>
                <span>Ahmedabad • Gandhinagar</span>
                <span>•</span>
                <span className="flex items-center gap-1.5 text-[#16803C] font-semibold">
                  <span className="w-2 h-2 rounded-full bg-[#16803C]" />
                  SYSTEM OPERATIONAL
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Middle: Professional Navigation Tabs */}
        <nav className="flex items-center gap-1.5 bg-[#F5F1E8] p-1.5 rounded-xl border border-[#DED8CC]">
          <button
            onClick={() => setActiveTab('map')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'map'
                ? 'bg-[#FDECEC] text-[#B42318] font-bold shadow-xs'
                : 'text-[#667085] hover:text-[#1F2933] hover:bg-white/60'
            }`}
          >
            <MapPin className="w-4 h-4" />
            <span>Tactical Map</span>
          </button>

          <button
            onClick={() => setActiveTab('incidents')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'incidents'
                ? 'bg-[#FDECEC] text-[#B42318] font-bold shadow-xs'
                : 'text-[#667085] hover:text-[#1F2933] hover:bg-white/60'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Incidents</span>
          </button>

          <button
            onClick={() => setActiveTab('fleet')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'fleet'
                ? 'bg-[#FDECEC] text-[#B42318] font-bold shadow-xs'
                : 'text-[#667085] hover:text-[#1F2933] hover:bg-white/60'
            }`}
          >
            <Truck className="w-4 h-4" />
            <span>Fleet</span>
          </button>

          <button
            onClick={() => setActiveTab('ingestion')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'ingestion'
                ? 'bg-[#FDECEC] text-[#B42318] font-bold shadow-xs'
                : 'text-[#667085] hover:text-[#1F2933] hover:bg-white/60'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Triage</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'analytics'
                ? 'bg-[#FDECEC] text-[#B42318] font-bold shadow-xs'
                : 'text-[#667085] hover:text-[#1F2933] hover:bg-white/60'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </button>
        </nav>

        {/* Right: Quick KPI Counters & Simulation Toggle */}
        <div className="flex items-center gap-4">
          
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2 bg-[#F5F1E8] border border-[#DED8CC] px-3 py-1.5 rounded-lg">
              <Flame className="w-4 h-4 text-[#C62828]" />
              <span className="text-[#667085] font-medium">Active Incidents:</span>
              <span className="font-bold text-[#1F2933] text-sm">{activeIncidentsCount}</span>
            </div>

            <div className="flex items-center gap-2 bg-[#F5F1E8] border border-[#DED8CC] px-3 py-1.5 rounded-lg">
              <Truck className="w-4 h-4 text-[#16803C]" />
              <span className="text-[#667085] font-medium">Available Fleet:</span>
              <span className="font-bold text-[#16803C] text-sm">{availableFleetCount}</span>
            </div>
          </div>

          {/* Simulation Toggle Button */}
          <button
            onClick={() => setIsSimulating((prev: boolean) => !prev)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              isSimulating
                ? 'bg-[#EAF6ED] border-[#16803C] text-[#16803C]'
                : 'bg-white border-[#DED8CC] text-[#667085] hover:text-[#1F2933] hover:bg-[#F5F1E8]'
            }`}
            title="Toggle Live Emergency Simulation"
          >
            {isSimulating ? (
              <>
                <Pause className="w-3.5 h-3.5 text-[#16803C]" />
                <span>Simulating Feed</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-[#667085]" />
                <span>Simulate</span>
              </>
            )}
          </button>

          {/* Tactical Alerts Bell */}
          <button
            onClick={openAlertsModal}
            className="relative p-2 rounded-lg bg-white border border-[#DED8CC] hover:bg-[#F5F1E8] text-[#1F2933] transition-colors"
            title="View Tactical Alerts"
          >
            <Bell className="w-4 h-4 text-[#1F2933]" />
            {unresolvedAlertCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center text-[10px] font-bold text-white bg-[#B42318] rounded-full">
                {unresolvedAlertCount}
              </span>
            )}
          </button>

        </div>

      </div>
    </header>
  );
}
