'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Incident, Resource, Hospital } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import {
  Flame,
  AlertTriangle,
  Radio,
  Ambulance,
  Shield,
  Truck,
  Building2,
  Navigation,
  Crosshair,
  Layers,
  Hospital as HospitalIcon,
  Tent,
} from 'lucide-react';

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

// Controller component to auto-fit on first load and fly-to when an incident is selected
function MapController({
  selectedIncident,
  incidents,
  initialFitDone,
  setInitialFitDone,
}: {
  selectedIncident: Incident | null;
  incidents: Incident[];
  initialFitDone: boolean;
  setInitialFitDone: (val: boolean) => void;
}) {
  const map = useMap();

  // Auto-fit bounds on initial load
  useEffect(() => {
    if (!initialFitDone && incidents.length > 0) {
      const validPoints: [number, number][] = [];
      incidents.forEach((inc) => {
        const coords = inc.location?.coordinates;
        if (coords && coords.length >= 2 && !isNaN(coords[0]) && !isNaN(coords[1])) {
          validPoints.push([coords[1], coords[0]]);
        }
      });
      if (validPoints.length > 0) {
        const bounds = L.latLngBounds(validPoints);
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
        setInitialFitDone(true);
      }
    }
  }, [incidents, initialFitDone, map, setInitialFitDone]);

  // Fly-to when an incident is selected
  useEffect(() => {
    if (selectedIncident && selectedIncident.location?.coordinates) {
      const [lon, lat] = selectedIncident.location.coordinates;
      if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
        map.flyTo([lat, lon], 14, { duration: 1.2 });
      }
    }
  }, [selectedIncident, map]);

  return null;
}

// Icon generator for Incidents: circle divIcons by severity, with pulsing animation for critical
const createIncidentIcon = (incident: Incident, isSelected: boolean) => {
  const severity = (incident.severity || 'MEDIUM').toUpperCase();
  let bgClass = 'bg-amber-600';
  let pulseClass = '';

  if (severity === 'CRITICAL') {
    bgClass = 'bg-red-600';
    pulseClass = 'marker-pulse-critical';
  } else if (severity === 'HIGH') {
    bgClass = 'bg-orange-600';
    pulseClass = 'marker-pulse-high';
  } else if (severity === 'MEDIUM') {
    bgClass = 'bg-amber-600';
  } else {
    bgClass = 'bg-sky-600';
  }

  const borderClass = isSelected
    ? 'ring-4 ring-white ring-offset-2 ring-offset-slate-950 scale-125 z-50'
    : 'border-2 border-slate-900 shadow-lg';

  const type = (incident.type || '').toLowerCase();
  let emoji = '🚨';
  if (type.includes('fire')) emoji = '🔥';
  else if (type.includes('flood')) emoji = '🌊';
  else if (type.includes('road') || type.includes('accident')) emoji = '🚗';
  else if (type.includes('gas')) emoji = '☣️';
  else if (type.includes('medical')) emoji = '🚑';
  else if (type.includes('collapse') || type.includes('building')) emoji = '🏚️';
  else if (type.includes('earthquake')) emoji = '🌋';
  else if (type.includes('industrial')) emoji = '🏭';

  const dupCount = (incident as any).report_count || incident.duplicate_count || 0;

  const html = `
    <div class="relative flex items-center justify-center transition-all duration-300">
      <div class="${pulseClass} ${bgClass} ${borderClass} w-9 h-9 rounded-full flex items-center justify-center text-sm text-white shadow-xl cursor-pointer">
        <span>${emoji}</span>
      </div>
      ${dupCount > 1 ? `
        <span class="absolute -top-1 -right-1 bg-purple-600 text-[10px] font-mono font-bold text-white w-4 h-4 rounded-full flex items-center justify-center border border-slate-900 shadow">
          +${dupCount}
        </span>
      ` : ''}
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-incident-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -20],
  });
};

// Icon generator for Resources with distinct small icons by kind:
// (fire truck, ambulance, police, rescue, hospital, relief camp, control center)
const createResourceIcon = (resource: Resource) => {
  const isAvailable = (resource.status || '').toUpperCase() === 'AVAILABLE';
  const bgClass = isAvailable ? 'bg-emerald-600' : 'bg-amber-600';
  const kind = (resource.category || resource.type || (resource as any).kind || '').toUpperCase();

  let symbol = '🚚';
  if (kind.includes('FIRE')) symbol = '🚒';
  else if (kind.includes('AMBULANCE') || kind.includes('MEDICAL')) symbol = '🚑';
  else if (kind.includes('POLICE')) symbol = '🚓';
  else if (kind.includes('RESCUE') || kind.includes('BOAT')) symbol = '🚤';
  else if (kind.includes('HOSPITAL')) symbol = '🏥';
  else if (kind.includes('RELIEF') || kind.includes('CAMP')) symbol = '⛺';
  else if (kind.includes('CONTROL') || kind.includes('CENTER')) symbol = '🏢';
  else if (kind.includes('HAZMAT')) symbol = '☣️';
  else if (kind.includes('DRONE')) symbol = '🛸';

  const html = `
    <div class="relative flex items-center justify-center">
      <div class="${bgClass} border border-slate-900 shadow-md w-7 h-7 rounded-lg flex items-center justify-center text-xs text-white">
        <span>${symbol}</span>
      </div>
      <span class="absolute -bottom-1 -right-1 w-2.5 h-2.5 rounded-full border border-slate-900 ${
        isAvailable ? 'bg-emerald-400' : 'bg-amber-400'
      }"></span>
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

// Icon for Hospitals
const createHospitalIcon = (hospital: Hospital) => {
  const html = `
    <div class="relative flex items-center justify-center">
      <div class="bg-blue-600 border border-slate-900 shadow-md w-7 h-7 rounded-full flex items-center justify-center font-black text-xs text-white">
        🏥
      </div>
      <span class="absolute -top-1 -right-1 text-[9px] font-mono px-1 rounded bg-slate-950 border border-blue-500 text-blue-300 font-bold">
        ${hospital.available_beds || 0}
      </span>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-hospital-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

export const EmergencyMap: React.FC<EmergencyMapProps> = ({
  incidents,
  resources = [],
  hospitals = [],
  selectedIncident,
  onSelectIncident,
  onDispatchResource,
  className = '',
}) => {
  // Center on lat 23.0225, lng 72.5714 (Ahmedabad emergency coordination center)
  const defaultCenter: [number, number] = [23.0225, 72.5714];
  const [initialFitDone, setInitialFitDone] = useState(false);
  const [showResources, setShowResources] = useState(true);
  const [showHospitals, setShowHospitals] = useState(true);
  const [showPolylines, setShowPolylines] = useState(true);

  // Calculate dispatched polylines: from assigned resource to target incident
  const activeDispatches = useMemo(() => {
    if (!showPolylines) return [];
    const lines: Array<{
      resourceId: string;
      incidentId: string;
      positions: [[number, number], [number, number]];
      color: string;
    }> = [];

    resources.forEach((res) => {
      const assignedIncId = res.current_incident_id || res.assigned_incident_id;
      if (assignedIncId && res.location?.coordinates) {
        const targetInc = incidents.find(
          (i) => i.incident_id === assignedIncId || i.id === assignedIncId || (i as any)._id === assignedIncId
        );
        if (targetInc?.location?.coordinates) {
          const resCoords: [number, number] = [res.location.coordinates[1], res.location.coordinates[0]];
          const incCoords: [number, number] = [targetInc.location.coordinates[1], targetInc.location.coordinates[0]];
          lines.push({
            resourceId: res.resource_id,
            incidentId: assignedIncId,
            positions: [resCoords, incCoords],
            color: '#06b6d4', // cyan-500
          });
        }
      }
    });

    return lines;
  }, [resources, incidents, showPolylines]);

  return (
    <div className={`relative w-full h-full min-h-[480px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 ${className}`}>
      <MapContainer
        center={defaultCenter}
        zoom={12}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ background: '#090d16', minHeight: '100%', height: '100%' }}
      >
        <MapController
          selectedIncident={selectedIncident}
          incidents={incidents}
          initialFitDone={initialFitDone}
          setInitialFitDone={setInitialFitDone}
        />

        {/* Standard OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* 1km Deduplication / Threat Radius Circle for Selected Incident */}
        {selectedIncident?.location?.coordinates && (
          <Circle
            center={[
              selectedIncident.location.coordinates[1],
              selectedIncident.location.coordinates[0],
            ]}
            radius={1000} // 1.0 km radius
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.12,
              weight: 1.5,
              dashArray: '6, 6',
            }}
          />
        )}

        {/* Dashed Polylines from Dispatched Resources to Their Incident */}
        {activeDispatches.map((disp, idx) => (
          <Polyline
            key={`disp-${disp.resourceId}-${idx}`}
            positions={disp.positions}
            pathOptions={{
              color: disp.color,
              weight: 2.5,
              dashArray: '6, 8',
              opacity: 0.85,
            }}
          />
        ))}

        {/* Render Incident Markers */}
        {incidents.map((incident) => {
          const coords = incident.location?.coordinates;
          if (!coords || coords.length < 2) return null;
          const [lon, lat] = coords;
          if (isNaN(lat) || isNaN(lon)) return null;

          const isSelected = selectedIncident?.incident_id === incident.incident_id;

          return (
            <Marker
              key={incident.incident_id || incident.id || incident._id}
              position={[lat, lon]}
              icon={createIncidentIcon(incident, isSelected)}
              eventHandlers={{
                click: () => onSelectIncident(incident),
              }}
            >
              <Popup>
                <div className="p-3 bg-slate-900 text-slate-200 text-xs space-y-2 rounded-lg min-w-[220px]">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span className="font-mono text-red-400 font-bold">{incident.incident_id}</span>
                    <StatusBadge type="severity" value={incident.severity} />
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-sm line-clamp-1">{incident.title}</h4>
                    <p className="text-slate-400 text-[11px] line-clamp-2 mt-0.5">
                      {incident.description}
                    </p>
                  </div>
                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>
                      Status: <strong className="text-white">{incident.status}</strong>
                    </span>
                    <span>
                      Priority: <strong className="text-amber-400">{incident.priority}</strong>
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">
                    📍 {incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </div>
                  <button
                    type="button"
                    onClick={() => onSelectIncident(incident)}
                    className="w-full mt-2 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded font-medium text-xs transition-colors flex items-center justify-center space-x-1"
                  >
                    <span>Inspect Incident</span>
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Render Resource Markers */}
        {showResources &&
          resources.map((resource) => {
            const coords = resource.location?.coordinates;
            if (!coords || coords.length < 2) return null;
            const [lon, lat] = coords;
            if (isNaN(lat) || isNaN(lon)) return null;

            return (
              <Marker
                key={resource.resource_id || resource.id || resource._id}
                position={[lat, lon]}
                icon={createResourceIcon(resource)}
              >
                <Popup>
                  <div className="p-3 bg-slate-900 text-slate-200 text-xs space-y-2 min-w-[200px]">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-1">
                      <span className="font-mono text-emerald-400 font-semibold">
                        {resource.resource_id}
                      </span>
                      <StatusBadge type="resource" value={resource.status} />
                    </div>
                    <div>
                      <h4 className="font-bold text-white text-sm">{resource.name}</h4>
                      <p className="text-slate-400 text-[11px] capitalize">
                        {(resource.category || resource.type || '').replace('_', ' ')}
                      </p>
                    </div>

                    {resource.current_incident_id && (
                      <div className="text-[11px] text-cyan-400 font-mono">
                        Dispatched: #{resource.current_incident_id}
                      </div>
                    )}

                    {selectedIncident && resource.status === 'AVAILABLE' && onDispatchResource && (
                      <button
                        type="button"
                        onClick={() => onDispatchResource(selectedIncident, resource)}
                        className="w-full mt-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium text-xs transition-colors"
                      >
                        Dispatch Unit
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* Render Hospitals */}
        {showHospitals &&
          hospitals.map((hospital) => {
            const coords = hospital.location?.coordinates;
            if (!coords || coords.length < 2) return null;
            const [lon, lat] = coords;
            if (isNaN(lat) || isNaN(lon)) return null;

            return (
              <Marker
                key={hospital.hospital_id || hospital.id || hospital._id}
                position={[lat, lon]}
                icon={createHospitalIcon(hospital)}
              >
                <Popup>
                  <div className="p-3 bg-slate-900 text-slate-200 text-xs space-y-2 min-w-[200px]">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-1">
                      <span className="font-mono text-blue-400 font-semibold">
                        {hospital.hospital_id}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 text-[10px] font-mono">
                        {hospital.status}
                      </span>
                    </div>
                    <h4 className="font-bold text-white text-sm">{hospital.name}</h4>
                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-950 p-2 rounded border border-slate-800">
                      <div>
                        <div className="text-slate-500">Available Beds</div>
                        <div className="text-emerald-400 font-bold">
                          {hospital.available_beds} / {hospital.total_beds}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-500">ICU Beds</div>
                        <div className="text-cyan-400 font-bold">{hospital.icu_available}</div>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400">📞 {hospital.contact_phone}</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* Top Layer Control Toggle Bar */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1.5 rounded-lg text-xs shadow-xl">
        <button
          type="button"
          onClick={() => setShowResources(!showResources)}
          className={`px-2 py-1 rounded transition-colors text-[11px] font-medium flex items-center gap-1 ${
            showResources
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Truck className="h-3 w-3 text-emerald-400" />
          <span>Fleet Units ({resources.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setShowPolylines(!showPolylines)}
          className={`px-2 py-1 rounded transition-colors text-[11px] font-medium flex items-center gap-1 ${
            showPolylines
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <span className="text-cyan-400">⚡</span>
          <span>Dispatches ({activeDispatches.length})</span>
        </button>
      </div>

      {/* Map Legend in bottom-left corner */}
      <div className="absolute bottom-3 left-3 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-2.5 rounded-lg text-xs space-y-1.5 shadow-2xl">
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold pb-1 border-b border-slate-800">
          Command Legend
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-600 inline-block ring-2 ring-red-400/40" />
            <span>Critical Incident</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            <span>Medium / High</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-md bg-emerald-600 inline-block" />
            <span>Available Fleet</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-md bg-amber-600 inline-block" />
            <span>Assigned Fleet</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-cyan-400 inline-block" />
            <span>Active Dispatch</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full border border-dashed border-red-500 inline-block" />
            <span>1km Dedup Zone</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyMap;
