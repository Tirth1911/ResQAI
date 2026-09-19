'use client';

import dynamic from 'next/dynamic';
import React from 'react';

const EmergencyMapClient = dynamic(
  () => import('./EmergencyMap'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[480px] rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-mono text-slate-400">Loading Geospatial Engine & Map Tiles...</p>
      </div>
    ),
  }
);

export default EmergencyMapClient;
export { EmergencyMapClient as EmergencyMap };
