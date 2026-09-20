'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import { Incident, Resource, Hospital } from '@/types';

const EmergencyMap = dynamic(() => import('./EmergencyMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-500 font-mono text-xs">
      <div className="flex flex-col items-center gap-2">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-red-500 border-t-transparent" />
        <span>Initializing Tactical Road Routing Cartography...</span>
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
  onAssignResource?: (incident: Incident, resource: Resource) => void;
  hoveredUnitId?: string | null;
  selectedUnitId?: string | null;
  onHoverUnit?: (unitId: string | null) => void;
  onSelectUnit?: (unitId: string) => void;
  isSimulating?: boolean;
  onToggleSimulate?: () => void;
  onTelemetryUpdate?: (telemetry: Record<string, { distanceKm: number; etaMin: number; arrived: boolean }>) => void;
  className?: string;
}

export function DynamicMapView(props: DynamicMapViewProps) {
  return (
    <EmergencyMap
      incidents={props.incidents}
      resources={props.resources}
      hospitals={props.hospitals}
      selectedIncident={props.selectedIncident || null}
      onSelectIncident={props.onSelectIncident || (() => {})}
      onDispatchResource={props.onAssignResource}
      hoveredUnitId={props.hoveredUnitId}
      selectedUnitId={props.selectedUnitId}
      onHoverUnit={props.onHoverUnit}
      onSelectUnit={props.onSelectUnit}
      isSimulating={props.isSimulating}
      onToggleSimulate={props.onToggleSimulate}
      onTelemetryUpdate={props.onTelemetryUpdate}
      className={props.className}
    />
  );
}

export default DynamicMapView;
