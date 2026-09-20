'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Incident, Resource, Hospital } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import { Truck } from 'lucide-react';

// Fix Leaflet default icon paths in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface EmergencyMapProps {
  incidents: Incident[];
  resources?: Resource[];
  hospitals?: Hospital[];
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident) => void;
  onDispatchResource?: (incident: Incident, resource: Resource) => void;
  hoveredUnitId?: string | null;
  selectedUnitId?: string | null;
  onHoverUnit?: (unitId: string | null) => void;
  onSelectUnit?: (unitId: string) => void;
  isSimulating?: boolean;
  onToggleSimulate?: () => void;
  onTelemetryUpdate?: (telemetry: Record<string, { distanceKm: number; etaMin: number; arrived: boolean }>) => void;
  className?: string;
}

// Map controller: smoothly center on selected incident
function MapController({
  selectedIncident,
}: {
  selectedIncident: Incident | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedIncident?.location?.coordinates) {
      const [lon, lat] = selectedIncident.location.coordinates;
      if (!isNaN(lat) && !isNaN(lon)) {
        map.setView([lat, lon], 12, { animate: true });
      }
    }
  }, [selectedIncident, map]);

  return null;
}

// ─── Incident Marker Icon (matching screenshot) ─────────────────────────────
const createIncidentIcon = (incident: Incident, isSelected: boolean) => {
  const severity = (incident.severity || 'MEDIUM').toUpperCase();

  let bg = '#dc2626'; // red-600
  let pulse = '';
  if (severity === 'CRITICAL') {
    bg = '#dc2626';
    pulse = 'inc-pulse-critical';
  } else if (severity === 'HIGH') {
    bg = '#ea580c'; // orange-600
    pulse = 'inc-pulse-high';
  } else if (severity === 'MEDIUM') {
    bg = '#d97706'; // amber-600
  } else {
    bg = '#2563eb'; // blue-600
  }

  const type = (incident.type || '').toLowerCase();
  let emoji = '🚨';
  if (type.includes('fire') || type.includes('factory')) emoji = '🔥';
  else if (type.includes('flood')) emoji = '🌊';
  else if (type.includes('road') || type.includes('accident')) emoji = '🚗';
  else if (type.includes('gas') || type.includes('hazmat') || type.includes('industrial')) emoji = '☣️';
  else if (type.includes('medical')) emoji = '🚑';
  else if (type.includes('collapse') || type.includes('building')) emoji = '🏚️';

  const selectedRing = isSelected
    ? 'box-shadow: 0 0 0 4px #dc2626, 0 0 0 8px rgba(220,38,38,0.25); transform: scale(1.15);'
    : '';
  const size = isSelected ? 44 : 36;

  const html = `
    <div class="${pulse}" style="position:relative;display:flex;align-items:center;justify-content:center;">
      <div style="background:white;border-radius:14px;border:2.5px solid ${bg};padding:3px;display:flex;align-items:center;justify-content:center;${selectedRing}transition:all 0.15s;">
        <div style="background:${bg};width:${size - 14}px;height:${size - 14}px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:13px;box-shadow:inset 0 1px 3px rgba(0,0,0,0.25);">
          <span>${emoji}</span>
        </div>
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-incident-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
  });
};

// ─── Resource Marker Icon (matching screenshot) ─────────────────────────────
const createResourceIcon = (
  resource: Resource,
  isDispatched: boolean = false,
  isHovered: boolean = false,
  isSelected: boolean = false
) => {
  const isAvail = (resource.status || '').toUpperCase() === 'AVAILABLE';
  const kind = (resource.category || resource.type || (resource as any).kind || '').toUpperCase();

  let bg = '#dc2626';
  let symbol = '🚒';
  if (kind.includes('AMBULANCE') || kind.includes('MEDICAL')) {
    bg = '#059669';
    symbol = '🚑';
  } else if (kind.includes('POLICE')) {
    bg = '#2563eb';
    symbol = '🚓';
  } else if (kind.includes('DRONE') || kind.includes('RECON')) {
    bg = '#9333ea';
    symbol = '🛸';
  } else if (kind.includes('HAZMAT')) {
    bg = '#9f1239';
    symbol = '☣️';
  } else if (kind.includes('RESCUE') || kind.includes('BOAT') || kind.includes('DISASTER')) {
    bg = '#ea580c';
    symbol = '🦺';
  }

  const statusDot = isDispatched ? '#16a34a' : isAvail ? '#22c55e' : '#f59e0b';
  const ringStyle = isDispatched
    ? 'box-shadow: 0 0 0 3px #16a34a, 0 0 10px rgba(22,163,74,0.45); transform: scale(1.12);'
    : isHovered || isSelected
    ? 'box-shadow: 0 0 0 3px #2563eb, 0 0 8px rgba(37,99,235,0.4); transform: scale(1.1);'
    : 'box-shadow: 0 1px 4px rgba(0,0,0,0.3);';

  const dispatchedBadge = isDispatched
    ? `<span style="position:absolute;top:-4px;right:-4px;width:10px;height:10px;border-radius:50%;background:#16a34a;border:2px solid white;display:block;animation:pulse-ring 1.8s infinite;"></span>`
    : '';

  const html = `
    <div style="position:relative;display:flex;align-items:center;justify-content:center;">
      <div style="background:${bg};border-radius:8px;border:2px solid white;padding:2px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:12px;${ringStyle}transition:all 0.15s;">
        <span>${symbol}</span>
      </div>
      ${dispatchedBadge}
      <span style="position:absolute;bottom:-2px;right:-2px;width:9px;height:9px;border-radius:50%;background:${statusDot};border:1.5px solid white;display:block;"></span>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-resource-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

// ─── Main Emergency Map Component ───────────────────────────────────────────
export const EmergencyMap: React.FC<EmergencyMapProps> = ({
  incidents,
  resources = [],
  hospitals = [],
  selectedIncident,
  onSelectIncident,
  onDispatchResource,
  hoveredUnitId,
  selectedUnitId,
  onHoverUnit,
  onSelectUnit,
  className = '',
}) => {
  // Center on Ahmedabad / Odhav GIDC
  const defaultCenter: [number, number] = [23.0135, 72.6582];
  const [showResources, setShowResources] = useState(true);

  // Set of assigned/dispatched resource IDs for the selected incident
  const dispatchedResourceIds = useMemo(() => {
    const set = new Set<string>();
    if (!selectedIncident) return set;

    // Check selectedIncident.assigned_resources
    if (Array.isArray(selectedIncident.assigned_resources)) {
      selectedIncident.assigned_resources.forEach((id) => {
        if (id) set.add(String(id));
      });
    }

    // Check resources matching current or assigned incident
    const incId = selectedIncident.incident_id || selectedIncident.id || (selectedIncident as any)._id;
    resources.forEach((r) => {
      const rId = r.resource_id || r.id || (r as any)._id;
      if (
        (r.current_incident_id && (r.current_incident_id === incId || r.current_incident_id === selectedIncident.incident_id)) ||
        (r.assigned_incident_id && (r.assigned_incident_id === incId || r.assigned_incident_id === selectedIncident.incident_id))
      ) {
        if (rId) set.add(String(rId));
      }
    });

    return set;
  }, [selectedIncident, resources]);

  // Dotted lines: ONLY show lines connected to units that are dispatched,
  // or active preview when hovered/selected from the dispatch command panel
  const dispatchLines = useMemo(() => {
    if (!selectedIncident?.location?.coordinates) return [];
    const [iLon, iLat] = selectedIncident.location.coordinates;
    if (isNaN(iLat) || isNaN(iLon)) return [];
    const incPt: [number, number] = [iLat, iLon];

    return resources
      .filter((r) => {
        if (!r.location?.coordinates || r.location.coordinates.length < 2) return false;
        const [rLon, rLat] = r.location.coordinates;
        if (isNaN(rLat) || isNaN(rLon)) return false;

        const rId = r.resource_id || r.id || (r as any)._id;
        const isDispatched = dispatchedResourceIds.has(String(rId));
        const isHovered = Boolean(hoveredUnitId && hoveredUnitId === rId);
        const isSelected = Boolean(selectedUnitId && selectedUnitId === rId);

        // Crucial requirement: only show line when unit is dispatched (or active hover/select preview)
        return isDispatched || isHovered || isSelected;
      })
      .map((r) => {
        const [rLon, rLat] = r.location.coordinates;
        const rId = r.resource_id || r.id || (r as any)._id;
        const isDispatched = dispatchedResourceIds.has(String(rId));
        const isHovered = Boolean(hoveredUnitId && hoveredUnitId === rId);
        const isSelected = Boolean(selectedUnitId && selectedUnitId === rId);

        // Distance & ETA calculation (Haversine)
        const dLat = ((incPt[0] - rLat) * Math.PI) / 180;
        const dLon = ((incPt[1] - rLon) * Math.PI) / 180;
        const a =
          Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos((rLat * Math.PI) / 180) *
            Math.cos((incPt[0] * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distKm = Math.round(6371 * c * 10) / 10;
        const estEtaMin = Math.max(1, Math.round((distKm / 35) * 60));

        return {
          key: `route-${rId}`,
          resource: r,
          resourceId: rId,
          positions: [[rLat, rLon], incPt] as [[number, number], [number, number]],
          isDispatched,
          isHovered,
          isSelected,
          distanceKm: distKm,
          etaMinutes: estEtaMin,
        };
      });
  }, [resources, selectedIncident, dispatchedResourceIds, hoveredUnitId, selectedUnitId]);

  return (
    <div className={`relative w-full h-full min-h-[480px] overflow-hidden bg-slate-100 ${className}`}>
      <MapContainer
        center={defaultCenter}
        zoom={12}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ background: '#f8fafc', minHeight: '100%', height: '100%' }}
      >
        <MapController selectedIncident={selectedIncident} />

        {/* Light OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* Dotted lines connecting dispatched units to the incident */}
        {selectedIncident &&
          dispatchLines.map((line) => {
            const isDispatched = line.isDispatched;
            const isProminent = line.isHovered || line.isSelected;

            return (
              <Polyline
                key={line.key}
                positions={line.positions}
                eventHandlers={{
                  mouseover: () => onHoverUnit?.(line.resourceId),
                  mouseout: () => onHoverUnit?.(null),
                  click: () => onSelectUnit?.(line.resourceId),
                }}
                pathOptions={{
                  color: isDispatched ? '#16a34a' : '#2563eb',
                  weight: isProminent ? 4 : isDispatched ? 3 : 2,
                  dashArray: isDispatched ? '7, 7' : '5, 6',
                  opacity: isProminent ? 1 : isDispatched ? 0.92 : 0.65,
                  className: isDispatched ? 'route-flow-animated cursor-pointer' : 'cursor-pointer',
                }}
              >
                <Tooltip sticky direction="top" className="tactical-route-tooltip">
                  <div className="p-2.5 text-xs font-sans space-y-1 bg-white rounded-xl shadow-lg border border-slate-200 min-w-[190px]">
                    <div className="font-bold text-slate-800 flex items-center justify-between gap-2">
                      <span className="truncate">{line.resource.name}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold shrink-0 ${
                          isDispatched
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : 'bg-blue-100 text-blue-800 border border-blue-300'
                        }`}
                      >
                        {isDispatched ? 'DISPATCHED' : 'PREVIEW ROUTE'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-600 flex items-center gap-1.5 pt-0.5 font-medium">
                      <span>⚡ {line.distanceKm} km away</span>
                      <span>•</span>
                      <span>ETA: ~{line.etaMinutes} min</span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate pt-0.5 border-t border-slate-100">
                      Destination: {selectedIncident.title || selectedIncident.incident_id}
                    </div>
                  </div>
                </Tooltip>
              </Polyline>
            );
          })}

        {/* 1 km threat radius for selected incident */}
        {selectedIncident?.location?.coordinates && (
          <Circle
            center={[
              selectedIncident.location.coordinates[1],
              selectedIncident.location.coordinates[0],
            ]}
            radius={1000}
            pathOptions={{
              color: '#dc2626',
              fillColor: '#ef4444',
              fillOpacity: 0.08,
              weight: 1.5,
              dashArray: '5, 5',
            }}
          />
        )}

        {/* Incident Markers */}
        {incidents.map((incident) => {
          const coords = incident.location?.coordinates;
          if (!coords || coords.length < 2) return null;
          const [lon, lat] = coords;
          if (isNaN(lat) || isNaN(lon)) return null;
          const isSelected = selectedIncident?.incident_id === incident.incident_id;

          return (
            <Marker
              key={incident.incident_id || incident.id}
              position={[lat, lon]}
              icon={createIncidentIcon(incident, isSelected)}
              eventHandlers={{ click: () => onSelectIncident(incident) }}
            >
              <Popup>
                <div className="p-3 text-slate-800 text-xs space-y-1.5 min-w-[210px]">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                    <span className="font-bold text-red-600 font-mono text-[11px]">{incident.incident_id}</span>
                    <StatusBadge type="severity" value={incident.severity} />
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm leading-tight">{incident.title}</h4>
                  <p className="text-slate-500 text-[11px] line-clamp-2">{incident.description}</p>
                  <div className="text-[10px] text-slate-400 pt-0.5">
                    📍 {incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Resource Markers */}
        {showResources &&
          resources.map((resource) => {
            const coords = resource.location?.coordinates;
            if (!coords || coords.length < 2) return null;
            const [lon, lat] = coords;
            if (isNaN(lat) || isNaN(lon)) return null;

            const rId = resource.resource_id || resource.id || (resource as any)._id;
            const isDispatched = dispatchedResourceIds.has(String(rId));
            const isHovered = Boolean(hoveredUnitId && hoveredUnitId === rId);
            const isSelected = Boolean(selectedUnitId && selectedUnitId === rId);

            return (
              <Marker
                key={rId}
                position={[lat, lon]}
                icon={createResourceIcon(resource, isDispatched, isHovered, isSelected)}
                eventHandlers={{
                  click: () => onSelectUnit?.(rId),
                  mouseover: () => onHoverUnit?.(rId),
                  mouseout: () => onHoverUnit?.(null),
                }}
              >
                <Popup>
                  <div className="p-2.5 text-slate-800 text-xs space-y-1.5 min-w-[180px]">
                    <div className="flex items-center justify-between font-bold border-b border-slate-100 pb-1">
                      <span className="text-slate-900 text-[12px]">{resource.name}</span>
                      <StatusBadge type="resource" value={isDispatched ? 'EN_ROUTE' : resource.status} />
                    </div>
                    {isDispatched && (
                      <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded px-2 py-0.5 text-[10px] font-bold">
                        ✓ Dispatched to active incident
                      </div>
                    )}
                    <p className="text-slate-500 text-[11px] capitalize">
                      {(resource.category || resource.type || '').replace('_', ' ')}
                    </p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* ─── Top Right Controls ─── */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-white/95 backdrop-blur-sm border border-slate-200 p-1.5 rounded-xl text-xs shadow-md">
        <button
          type="button"
          onClick={() => setShowResources(!showResources)}
          className={`px-3 py-1.5 rounded-lg transition-colors text-[11px] font-semibold flex items-center gap-1.5 ${
            showResources
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'text-slate-600 hover:bg-slate-100 border border-transparent'
          }`}
        >
          <Truck className="h-3.5 w-3.5" />
          Fleet Units
        </button>
      </div>

      {/* ─── Map Legend (bottom-left, matching reference image) ─── */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/96 backdrop-blur-sm border border-slate-200 p-3.5 rounded-2xl shadow-lg w-44 text-xs space-y-2.5 select-none pointer-events-auto">
        <div className="text-[10px] font-black uppercase tracking-widest text-slate-700">
          MAP LEGEND
        </div>
        <div className="space-y-1.5 text-[11px] text-slate-600 font-medium">
          {[
            { color: '#dc2626', label: 'Critical Incident', shape: 'circle' },
            { color: '#ea580c', label: 'High Severity', shape: 'circle' },
            { color: '#d97706', label: 'Medium Severity', shape: 'circle' },
            { color: '#2563eb', label: 'Police Patrol', shape: 'circle' },
            { color: '#dc2626', label: 'Fire & Rescue', shape: 'square' },
            { color: '#059669', label: 'Medical 108', shape: 'square' },
            { color: '#9333ea', label: 'Drone Recon', shape: 'circle' },
          ].map(({ color, label, shape }) => (
            <div key={label} className="flex items-center gap-2">
              <span
                className="shrink-0"
                style={{
                  display: 'inline-block',
                  width: 10,
                  height: 10,
                  borderRadius: shape === 'circle' ? '50%' : '2px',
                  background: color,
                }}
              />
              <span>{label}</span>
            </div>
          ))}
          {/* Dashed line legend */}
          <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
            <svg width="14" height="6" viewBox="0 0 14 6" className="shrink-0">
              <line x1="0" y1="3" x2="14" y2="3" stroke="#16a34a" strokeWidth="2.5" strokeDasharray="3,2" />
            </svg>
            <span className="font-semibold text-slate-700">Dispatched Route</span>
          </div>
          <div className="flex items-center gap-2">
            <svg width="14" height="6" viewBox="0 0 14 6" className="shrink-0">
              <line x1="0" y1="3" x2="14" y2="3" stroke="#2563eb" strokeWidth="2" strokeDasharray="2,2" />
            </svg>
            <span className="text-slate-500">Preview Route</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyMap;
