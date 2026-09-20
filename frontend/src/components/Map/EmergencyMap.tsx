'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
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
  className?: string;
}

// Map controller: fit all incidents on first load, fly-to on selection
function MapController({
  selectedIncident,
  incidents,
  initialFitDone,
  setInitialFitDone,
}: {
  selectedIncident: Incident | null;
  incidents: Incident[];
  initialFitDone: boolean;
  setInitialFitDone: (v: boolean) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!initialFitDone && incidents.length > 0) {
      const pts: [number, number][] = [];
      incidents.forEach((inc) => {
        const c = inc.location?.coordinates;
        if (c && c.length >= 2 && !isNaN(c[0]) && !isNaN(c[1])) {
          pts.push([c[1], c[0]]);
        }
      });
      if (pts.length > 0) {
        const bounds = L.latLngBounds(pts);
        map.fitBounds(bounds, { padding: [80, 80], maxZoom: 12 });
        setInitialFitDone(true);
      }
    }
  }, [incidents, initialFitDone, map, setInitialFitDone]);

  // Fly to selected incident but stay at wide enough zoom to show lines
  useEffect(() => {
    if (selectedIncident?.location?.coordinates) {
      const [lon, lat] = selectedIncident.location.coordinates;
      if (!isNaN(lat) && !isNaN(lon)) {
        map.flyTo([lat, lon], 12, { duration: 1.0 });
      }
    }
  }, [selectedIncident, map]);

  return null;
}

// ─── Incident Marker Icon ─────────────────────────────────────────────────────
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
    ? 'box-shadow:0 0 0 4px #dc2626, 0 0 0 7px rgba(220,38,38,0.25); transform: scale(1.15);'
    : '';
  const size = isSelected ? 44 : 36;

  const html = `
    <div class="${pulse}" style="position:relative;display:flex;align-items:center;justify-content:center;">
      <div style="background:white;border-radius:14px;border:2.5px solid ${bg};padding:3px;display:flex;align-items:center;justify-content:center;${selectedRing};transition:all 0.15s;">
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

// ─── Resource Marker Icon ─────────────────────────────────────────────────────
const createResourceIcon = (resource: Resource) => {
  const isAvail = (resource.status || '').toUpperCase() === 'AVAILABLE';
  const kind = (resource.category || resource.type || (resource as any).kind || '').toUpperCase();

  let bg = '#dc2626';
  let symbol = '🚒';
  if (kind.includes('AMBULANCE') || kind.includes('MEDICAL')) {
    bg = '#059669'; symbol = '🚑';
  } else if (kind.includes('POLICE')) {
    bg = '#2563eb'; symbol = '🚓';
  } else if (kind.includes('DRONE')) {
    bg = '#0891b2'; symbol = '🛸';
  } else if (kind.includes('HAZMAT')) {
    bg = '#9f1239'; symbol = '☣️';
  } else if (kind.includes('RESCUE') || kind.includes('BOAT') || kind.includes('DISASTER')) {
    bg = '#d97706'; symbol = '🦺';
  }

  const statusDot = isAvail ? '#22c55e' : '#f59e0b';
  const html = `
    <div style="position:relative;display:flex;align-items:center;justify-content:center;">
      <div style="background:${bg};border-radius:8px;border:2px solid white;padding:2px;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:11px;box-shadow:0 1px 4px rgba(0,0,0,0.3);">
        <span>${symbol}</span>
      </div>
      <span style="position:absolute;bottom:-2px;right:-2px;width:8px;height:8px;border-radius:50%;background:${statusDot};border:1.5px solid white;display:block;"></span>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-resource-marker',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -16],
  });
};

// ─── Main Component ───────────────────────────────────────────────────────────
export const EmergencyMap: React.FC<EmergencyMapProps> = ({
  incidents,
  resources = [],
  hospitals = [],
  selectedIncident,
  onSelectIncident,
  onDispatchResource,
  className = '',
}) => {
  // Ahmedabad center
  const defaultCenter: [number, number] = [23.0225, 72.5714];
  const [initialFitDone, setInitialFitDone] = useState(false);
  const [showResources, setShowResources] = useState(true);

  // Green dashed lines: resources → selected incident only
  const candidateLines = useMemo(() => {
    if (!selectedIncident?.location?.coordinates) return [];
    const [iLon, iLat] = selectedIncident.location.coordinates;
    const incPt: [number, number] = [iLat, iLon];
    return resources
      .filter((r) => r.location?.coordinates)
      .map((r) => {
        const [rLon, rLat] = r.location!.coordinates;
        return {
          key: r.resource_id,
          positions: [[rLat, rLon], incPt] as [[number, number], [number, number]],
        };
      });
  }, [resources, selectedIncident]);

  // Assigned resource lines (darker green, solid)
  const assignedLines = useMemo(() => {
    return resources
      .filter((r) => {
        const assignedId = r.current_incident_id || (r as any).assigned_incident_id;
        return assignedId && r.location?.coordinates;
      })
      .map((r) => {
        const assignedId = r.current_incident_id || (r as any).assigned_incident_id;
        const targetInc = incidents.find(
          (i) => i.incident_id === assignedId || i.id === assignedId
        );
        if (!targetInc?.location?.coordinates) return null;
        const [rLon, rLat] = r.location!.coordinates;
        const [iLon, iLat] = targetInc.location.coordinates;
        return {
          key: r.resource_id + '-assigned',
          positions: [[rLat, rLon], [iLat, iLon]] as [[number, number], [number, number]],
        };
      })
      .filter(Boolean) as Array<{ key: string; positions: [[number, number], [number, number]] }>;
  }, [resources, incidents]);

  return (
    <div className={`relative w-full h-full min-h-[480px] overflow-hidden bg-slate-100 ${className}`}>
      <MapContainer
        center={defaultCenter}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ background: '#f8fafc', minHeight: '100%', height: '100%' }}
      >
        <MapController
          selectedIncident={selectedIncident}
          incidents={incidents}
          initialFitDone={initialFitDone}
          setInitialFitDone={setInitialFitDone}
        />

        {/* Light OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* Candidate lines: resources → selected incident (dashed green) */}
        {candidateLines.map((line) => (
          <Polyline
            key={line.key}
            positions={line.positions}
            pathOptions={{
              color: '#16a34a',
              weight: 2,
              dashArray: '6, 7',
              opacity: 0.85,
            }}
          />
        ))}

        {/* Assigned lines (solid green) */}
        {assignedLines.map((line) => (
          <Polyline
            key={line.key}
            positions={line.positions}
            pathOptions={{
              color: '#15803d',
              weight: 2.5,
              opacity: 0.9,
            }}
          />
        ))}

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
              fillOpacity: 0.1,
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
                <div className="p-3 text-slate-800 text-xs space-y-1.5 min-w-[200px]">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                    <span className="font-bold text-red-600 font-mono text-[11px]">{incident.incident_id}</span>
                    <StatusBadge type="severity" value={incident.severity} />
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm leading-tight">{incident.title}</h4>
                  <p className="text-slate-500 text-[11px] line-clamp-2">{incident.description}</p>
                  <div className="text-[10px] text-slate-400 pt-0.5">
                    📍 {incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </div>
                  <button
                    type="button"
                    onClick={() => onSelectIncident(incident)}
                    className="w-full mt-1.5 py-1.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg text-xs transition-colors"
                  >
                    View Details →
                  </button>
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
            return (
              <Marker
                key={resource.resource_id || resource.id}
                position={[lat, lon]}
                icon={createResourceIcon(resource)}
              >
                <Popup>
                  <div className="p-2.5 text-slate-800 text-xs space-y-1 min-w-[170px]">
                    <div className="flex items-center justify-between font-bold border-b border-slate-100 pb-1">
                      <span className="text-slate-900 text-[12px]">{resource.name}</span>
                      <StatusBadge type="resource" value={resource.status} />
                    </div>
                    <p className="text-slate-400 text-[11px] capitalize">
                      {(resource.category || resource.type || '').replace('_', ' ')}
                    </p>
                    {resource.address && (
                      <p className="text-[10px] text-slate-400">📍 {resource.address}</p>
                    )}
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
        <button
          type="button"
          className={`px-3 py-1.5 rounded-lg transition-colors text-[11px] font-semibold flex items-center gap-1.5 ${
            selectedIncident
              ? 'bg-red-50 text-red-800 border border-red-200'
              : 'text-slate-400 border border-transparent'
          }`}
        >
          <span>⚡</span>
          Dispatches ({assignedLines.length})
        </button>
      </div>

      {/* ─── Map Legend (bottom-left, matching screenshot) ─── */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/96 backdrop-blur-sm border border-slate-200 p-3.5 rounded-2xl shadow-lg w-44 text-xs space-y-2.5">
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
            { color: '#059669', label: 'Medical / 108', shape: 'circle' },
            { color: '#0891b2', label: 'Drone Recon', shape: 'circle' },
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
          <div className="flex items-center gap-2 pt-0.5">
            <svg width="14" height="6" viewBox="0 0 14 6" className="shrink-0">
              <line x1="0" y1="3" x2="14" y2="3" stroke="#16a34a" strokeWidth="2" strokeDasharray="3,2" />
            </svg>
            <span>Response Route</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyMap;
