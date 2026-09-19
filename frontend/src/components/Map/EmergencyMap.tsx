'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
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
} from 'lucide-react';

interface EmergencyMapProps {
  incidents: Incident[];
  resources?: Resource[];
  hospitals?: Hospital[];
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident) => void;
  onDispatchResource?: (incidentId: string, resourceId: string) => void;
  showResources?: boolean;
  showHospitals?: boolean;
  showDedupRadius?: boolean;
}

// Helper to pan map dynamically
function MapController({ selectedIncident }: { selectedIncident: Incident | null }) {
  const map = useMap();

  useEffect(() => {
    if (selectedIncident && selectedIncident.location?.coordinates) {
      const [lon, lat] = selectedIncident.location.coordinates;
      if (lat && lon) {
        map.flyTo([lat, lon], 14, { duration: 1.2 });
      }
    }
  }, [selectedIncident, map]);

  return null;
}

// Icon generator for Incidents
const createIncidentIcon = (incident: Incident, isSelected: boolean) => {
  const severity = incident.severity?.toUpperCase();
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

  const type = incident.type?.toLowerCase();
  let emoji = '🚨';
  if (type?.includes('fire')) emoji = '🔥';
  else if (type?.includes('flood')) emoji = '🌊';
  else if (type?.includes('road') || type?.includes('accident')) emoji = '🚗';
  else if (type?.includes('gas')) emoji = '☣️';
  else if (type?.includes('medical')) emoji = '🚑';
  else if (type?.includes('collapse') || type?.includes('building')) emoji = '🏚️';
  else if (type?.includes('earthquake')) emoji = '🌋';

  const html = `
    <div class="relative flex items-center justify-center transition-all duration-300">
      <div class="${pulseClass} ${bgClass} ${borderClass} w-9 h-9 rounded-full flex items-center justify-center text-sm text-white shadow-xl cursor-pointer">
        <span>${emoji}</span>
      </div>
      ${incident.duplicate_count && incident.duplicate_count > 0 ? `
        <span class="absolute -top-1 -right-1 bg-purple-600 text-[10px] font-mono font-bold text-white w-4 h-4 rounded-full flex items-center justify-center border border-slate-900 shadow">
          +${incident.duplicate_count}
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

// Icon generator for Resources
const createResourceIcon = (resource: Resource) => {
  const isAvailable = resource.status === 'AVAILABLE';
  const bgClass = isAvailable ? 'bg-emerald-600' : 'bg-slate-700';
  const category = resource.category?.toUpperCase();

  let symbol = '🚑';
  if (category?.includes('FIRE')) symbol = '🚒';
  else if (category?.includes('POLICE')) symbol = '🚓';
  else if (category?.includes('BOAT')) symbol = '🚤';
  else if (category?.includes('HAZMAT')) symbol = '☣️';
  else if (category?.includes('DRONE')) symbol = '🛸';

  const html = `
    <div class="relative flex items-center justify-center">
      <div class="${bgClass} border border-slate-900 shadow-md w-7 h-7 rounded-lg flex items-center justify-center text-xs text-white">
        <span>${symbol}</span>
      </div>
      <span class="absolute -bottom-1 -right-1 w-2.5 h-2.5 rounded-full border border-slate-900 ${isAvailable ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}"></span>
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

// Icon generator for Hospitals
const createHospitalIcon = (hospital: Hospital) => {
  const isOpen = hospital.status === 'OPEN';
  const html = `
    <div class="relative flex items-center justify-center">
      <div class="bg-blue-600 border border-slate-900 shadow-md w-7 h-7 rounded-full flex items-center justify-center font-black text-xs text-white">
        H
      </div>
      <span class="absolute -top-1 -right-1 text-[9px] font-mono px-1 rounded bg-slate-950 border border-blue-500 text-blue-300 font-bold">
        ${hospital.available_beds}
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
  showResources = true,
  showHospitals = true,
  showDedupRadius = true,
}) => {
  // Default map center: Ahmedabad / Gujarat hub [23.0225, 72.5714]
  const defaultCenter: [number, number] = useMemo(() => {
    if (selectedIncident && selectedIncident.location?.coordinates) {
      return [selectedIncident.location.coordinates[1], selectedIncident.location.coordinates[0]];
    }
    if (incidents.length > 0 && incidents[0].location?.coordinates) {
      return [incidents[0].location.coordinates[1], incidents[0].location.coordinates[0]];
    }
    return [23.0225, 72.5714];
  }, [incidents, selectedIncident]);

  return (
    <div className="relative w-full h-full min-h-[480px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
      <MapContainer
        center={defaultCenter}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ background: '#090d16', minHeight: '480px' }}
      >
        <MapController selectedIncident={selectedIncident} />

        {/* High-Contrast Humanitarian OSM Basemap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles by <a href="https://www.hotosm.org/">HOT</a>'
          url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* 1km Dedup / Threat Radius Circle for Selected Incident */}
        {showDedupRadius && selectedIncident && selectedIncident.location?.coordinates && (
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

        {/* Render Incidents */}
        {incidents.map((incident) => {
          const coords = incident.location?.coordinates;
          if (!coords || coords.length < 2) return null;
          const [lon, lat] = coords;
          const isSelected = selectedIncident?.incident_id === incident.incident_id;

          return (
            <Marker
              key={incident.incident_id || incident._id}
              position={[lat, lon]}
              icon={createIncidentIcon(incident, isSelected)}
              eventHandlers={{
                click: () => onSelectIncident(incident),
              }}
            >
              <Popup>
                <div className="p-3 bg-slate-900 text-slate-200 text-xs space-y-2 rounded-lg min-w-[220px]">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <span className="font-mono text-red-400 font-bold">
                      {incident.incident_id}
                    </span>
                    <StatusBadge type="severity" value={incident.severity} />
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-sm line-clamp-1">
                      {incident.title}
                    </h4>
                    <p className="text-slate-400 text-[11px] line-clamp-2 mt-0.5">
                      {incident.description}
                    </p>
                  </div>
                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Status: <strong className="text-white">{incident.status}</strong></span>
                    <span>P: <strong className="text-amber-400">{incident.priority}</strong></span>
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">
                    📍 {incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </div>
                  <button
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

        {/* Render Resources */}
        {showResources &&
          resources.map((resource) => {
            const coords = resource.location?.coordinates;
            if (!coords || coords.length < 2) return null;
            const [lon, lat] = coords;

            return (
              <Marker
                key={resource.resource_id || resource._id}
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
                      <p className="text-slate-400 text-[11px]">{resource.category}</p>
                    </div>
                    {resource.capabilities && resource.capabilities.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {resource.capabilities.slice(0, 3).map((cap, i) => (
                          <span
                            key={i}
                            className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 font-mono"
                          >
                            {cap}
                          </span>
                        ))}
                      </div>
                    )}
                    {selectedIncident && resource.status === 'AVAILABLE' && onDispatchResource && (
                      <button
                        onClick={() =>
                          onDispatchResource(selectedIncident.incident_id, resource.resource_id)
                        }
                        className="w-full mt-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium text-xs transition-colors"
                      >
                        Dispatch to {selectedIncident.incident_id}
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

            return (
              <Marker
                key={hospital.hospital_id || hospital._id}
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
                        <div className="text-emerald-400 font-bold">{hospital.available_beds} / {hospital.total_beds}</div>
                      </div>
                      <div>
                        <div className="text-slate-500">ICU Beds</div>
                        <div className="text-cyan-400 font-bold">{hospital.icu_available}</div>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400">
                      📞 {hospital.contact_phone}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* Floating Map Controls & Legend Overlay */}
      <div className="absolute top-3 right-3 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-2.5 rounded-lg text-xs space-y-2 shadow-2xl">
        <div className="flex items-center space-x-2 text-[11px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-1">
          <Layers className="h-3.5 w-3.5 text-red-500" />
          <span>Tactical Map Layers</span>
        </div>
        <div className="flex flex-col space-y-1.5 text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-red-600 border border-slate-900 inline-block shadow-xs shadow-red-500"></span>
            <span className="text-slate-300">Critical Incidents ({incidents.filter(i => i.severity === 'CRITICAL').length})</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-md bg-emerald-600 border border-slate-900 inline-block"></span>
            <span className="text-slate-300">Available Fleet ({resources.filter(r => r.status === 'AVAILABLE').length})</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-blue-600 border border-slate-900 inline-block"></span>
            <span className="text-slate-300">Emergency Hospitals ({hospitals.length})</span>
          </div>
          {selectedIncident && (
            <div className="flex items-center space-x-2 pt-1 border-t border-slate-800">
              <span className="w-3 h-3 rounded-full border border-dashed border-red-500 inline-block"></span>
              <span className="text-red-400 font-mono text-[10px]">1km Dedup Radius Active</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmergencyMap;
