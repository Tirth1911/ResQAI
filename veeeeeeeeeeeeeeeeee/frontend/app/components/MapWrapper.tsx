'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import { Incident, Resource, DispatchRecommendation } from '../types';

interface TacticalMapProps {
  incidents: Incident[];
  resources: Resource[];
  selectedIncident: Incident | null;
  onSelectIncident: (inc: Incident) => void;
  onDispatchUnit: (incidentId: string, resourceId: string) => void;
  recommendations: DispatchRecommendation[];
}

const DynamicTacticalMap = dynamic(() => import('./TacticalMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[calc(100vh-4.5rem)] bg-[#F5F1E8] flex flex-col items-center justify-center text-[#667085] gap-3">
      <div className="w-8 h-8 border-3 border-[#B42318] border-t-transparent rounded-full animate-spin"></div>
      <div className="text-xs font-semibold tracking-wider text-[#1F2933]">INITIALIZING GIS TACTICAL MAP...</div>
    </div>
  )
});

export default function MapWrapper(props: TacticalMapProps) {
  return <DynamicTacticalMap {...props} />;
}
