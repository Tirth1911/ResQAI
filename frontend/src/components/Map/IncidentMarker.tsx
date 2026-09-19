'use client';

import React from 'react';
import { Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { Incident } from '@/types';
import { SeverityBadge } from '../common/SeverityBadge';
import { PriorityBadge } from '../common/PriorityBadge';

interface IncidentMarkerProps {
  incident: Incident;
  isSelected?: boolean;
  onSelect?: (incident: Incident) => void;
  showRadius?: boolean;
}

export const createIncidentLeafletIcon = (incident: Incident, isSelected: boolean) => {
  const severity = (incident.severity || 'LOW').toUpperCase();
  
  // Color specifications: LOW = green, MEDIUM = yellow, HIGH = orange, CRITICAL = red
  let bgClass = 'bg-emerald-500';
  let pulseHtml = '';

  if (severity === 'CRITICAL') {
    bgClass = 'bg-red-600 ring-2 ring-red-400';
    pulseHtml = '<span class="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping"></span>';
  } else if (severity === 'HIGH') {
    bgClass = 'bg-orange-500 ring-2 ring-orange-400';
    pulseHtml = '<span class="absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-50 animate-ping"></span>';
  } else if (severity === 'MEDIUM') {
    bgClass = 'bg-yellow-500';
  } else {
    // LOW
    bgClass = 'bg-emerald-500';
  }

  const selectRing = isSelected ? 'ring-4 ring-cyan-400 scale-125 z-50' : '';

  const type = incident.type?.toLowerCase() || '';
  let emoji = '🚨';
  if (type.includes('fire')) emoji = '🔥';
  else if (type.includes('flood')) emoji = '🌊';
  else if (type.includes('road') || type.includes('accident')) emoji = '🚗';
  else if (type.includes('gas') || type.includes('hazard')) emoji = '☣️';
  else if (type.includes('medical')) emoji = '🚑';
  else if (type.includes('building') || type.includes('collapse')) emoji = '🏚️';
  else if (type.includes('earthquake')) emoji = '🌋';

  const html = `
    <div class="relative flex items-center justify-center cursor-pointer">
      ${pulseHtml}
      <div class="${bgClass} ${selectRing} relative flex h-9 w-9 items-center justify-center rounded-full text-white shadow-xl transition-transform border border-slate-950">
        <span class="text-sm select-none">${emoji}</span>
      </div>
      ${
        incident.duplicate_count && incident.duplicate_count > 0
          ? `<span class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-purple-600 text-[10px] font-bold text-white border border-slate-900 font-mono shadow">+${incident.duplicate_count}</span>`
          : ''
      }
    </div>
  `;

  return L.divIcon({
    html,
    className: 'resqai-incident-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -20],
  });
};

export function IncidentMarker({
  incident,
  isSelected = false,
  onSelect,
  showRadius = true,
}: IncidentMarkerProps) {
  if (!incident.location?.coordinates || incident.location.coordinates.length < 2) {
    return null;
  }

  // NOTE: MongoDB stores GeoJSON as [longitude, latitude]
  // Leaflet expects [latitude, longitude]
  const [lon, lat] = incident.location.coordinates;
  if (lat === undefined || lon === undefined || isNaN(lat) || isNaN(lon)) {
    return null;
  }

  const icon = createIncidentLeafletIcon(incident, isSelected);

  const formattedTime = incident.reported_at
    ? new Date(incident.reported_at).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Recently';

  return (
    <>
      <Marker
        position={[lat, lon]}
        icon={icon}
        eventHandlers={{
          click: () => onSelect?.(incident),
        }}
      >
        <Popup className="resqai-dark-popup">
          <div className="p-1.5 min-w-[240px] max-w-[300px] bg-slate-950 text-slate-100 rounded-lg text-xs font-mono">
            {/* Header: ID, Priority, Severity */}
            <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2 mb-2">
              <span className="font-bold text-cyan-400">{incident.incident_id}</span>
              <div className="flex items-center gap-1">
                <PriorityBadge priority={incident.priority} />
                <SeverityBadge severity={incident.severity} />
              </div>
            </div>

            {/* Title & Type */}
            <h4 className="font-sans font-bold text-white text-xs leading-snug mb-1">
              {incident.title}
            </h4>
            <p className="text-[11px] text-slate-400 capitalize mb-2">
              Type: <strong className="text-slate-200">{incident.type.replace(/_/g, ' ')}</strong>
            </p>

            {/* Details: Status, Location, Reported, Assigned Resources */}
            <div className="text-[11px] text-slate-300 space-y-1 bg-slate-900/80 p-2 rounded border border-slate-800 mb-2.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span
                  className={`font-bold uppercase ${
                    incident.status === 'REPORTED'
                      ? 'text-purple-400'
                      : incident.status === 'VERIFIED'
                      ? 'text-blue-400'
                      : incident.status === 'DISPATCHED' || incident.status === 'IN_PROGRESS'
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {incident.status}
                </span>
              </div>

              <div className="flex justify-between gap-2">
                <span className="text-slate-500 shrink-0">Location:</span>
                <span className="text-slate-300 truncate max-w-[170px]" title={incident.address}>
                  {incident.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-500">Reported:</span>
                <span className="text-slate-300">{formattedTime}</span>
              </div>

              <div className="flex justify-between gap-2 border-t border-slate-800/80 pt-1 mt-1">
                <span className="text-slate-500">Assigned:</span>
                <span className="text-cyan-400 font-semibold">
                  {incident.assigned_resources && incident.assigned_resources.length > 0
                    ? incident.assigned_resources.join(', ')
                    : 'None Dispatched'}
                </span>
              </div>
            </div>

            {/* Action button to open IncidentDetailsModal */}
            <button
              type="button"
              onClick={() => onSelect?.(incident)}
              className="w-full py-1.5 text-center text-xs font-bold rounded bg-cyan-600 hover:bg-cyan-500 text-white transition-colors uppercase tracking-wider"
            >
              Open Tactical Briefing &rarr;
            </button>
          </div>
        </Popup>
      </Marker>

      {/* 1km Deduplication & Hazard Radius Circle */}
      {showRadius && (
        <Circle
          center={[lat, lon]}
          radius={1000}
          pathOptions={{
            color:
              incident.severity === 'CRITICAL'
                ? '#ef4444'
                : incident.severity === 'HIGH'
                ? '#f97316'
                : '#06b6d4',
            fillColor:
              incident.severity === 'CRITICAL'
                ? '#ef4444'
                : incident.severity === 'HIGH'
                ? '#f97316'
                : '#06b6d4',
            fillOpacity: 0.08,
            weight: 1,
            dashArray: '4, 6',
          }}
        />
      )}
    </>
  );
}

export default IncidentMarker;
