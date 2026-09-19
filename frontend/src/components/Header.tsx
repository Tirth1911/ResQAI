'use client';

import React from 'react';
import { ShieldAlert, Activity, Radio, Wifi, WifiOff } from 'lucide-react';

interface HeaderProps {
  wsConnected?: boolean;
  dbConnected?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ wsConnected = false, dbConnected = false }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-500 shadow-lg shadow-red-500/10">
            <ShieldAlert className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-wider">ResQ<span className="text-red-500">AI</span></span>
              <span className="text-xs uppercase px-2 py-0.5 rounded font-mono bg-red-950/80 text-red-400 border border-red-800/60">
                Command Hub
              </span>
            </div>
            <p className="text-xs text-slate-400">Intelligent Emergency Response & Resource Coordination</p>
          </div>
        </div>

        {/* Live Connectivity Status Indicators */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
            <Radio className={`h-3.5 w-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            <span className="text-slate-300">Live WS:</span>
            <span className={`font-medium ${wsConnected ? 'text-emerald-400' : 'text-amber-500'}`}>
              {wsConnected ? 'Connected' : 'Connecting'}
            </span>
          </div>

          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
            <Activity className={`h-3.5 w-3.5 ${dbConnected ? 'text-emerald-400' : 'text-slate-500'}`} />
            <span className="text-slate-300">MongoDB:</span>
            <span className={`font-medium ${dbConnected ? 'text-emerald-400' : 'text-amber-500'}`}>
              {dbConnected ? 'Active' : 'Offline / Standby'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
