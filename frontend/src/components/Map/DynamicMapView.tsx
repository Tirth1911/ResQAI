'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import { Incident, Resource, Hospital } from '@/types';

const MapView = dynamic(() => import('./MapView'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-xl border border-slate-800 bg-slate-950 text-slate-500 font-mono text-xs">
      <div className="flex flex-col items-center gap-2">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
        <span>Initializing Tactical Cartography Engine...</span>
      </div>
    </div>
  ),
});

interface DynamicMapViewProps {
  incidents: Incident[];
  resources?: Resource[];
  hospitals?: Hospital[];
  selectedIncident?: Incident | null;
  onSelectIncident?: (incident: Incident) => void;
  onSelectResource?: (resource: Resource) => void;
  onAssignResource?: (resource: Resource) => void;
  center?: [number, number];
  zoom?: number;
  showResourcesToggle?: boolean;
  showRadiusToggle?: boolean;
  className?: string;
}

export function DynamicMapView(props: DynamicMapViewProps) {
  return <MapView {...props} />;
}

export default DynamicMapView;
