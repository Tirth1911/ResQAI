'use client';

import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Resource } from '@/types';

interface ResourceMarkerProps {
  resource: Resource;
  isSelected?: boolean;
  onSelect?: (resource: Resource) => void;
  onAssign?: (resource: Resource) => void;
}

export const createResourceLeafletIcon = (resource: Resource, isSelected: boolean) => {
  const status = (resource.status || 'AVAILABLE').toUpperCase();

  // Resource status color styling:
  // AVAILABLE = green, BUSY = yellow/orange, EN_ROUTE = cyan/blue, OFFLINE = gray/dark
  let bgClass = 'bg-emerald-600';
  let badgeColor = 'bg-emerald-400';

  if (status === 'AVAILABLE') {
    bgClass = 'bg-emerald-600';
    badgeColor = 'bg-emerald-400';
  } else if (status === 'BUSY') {
    bgClass = 'bg-amber-600';
    badgeColor = 'bg-amber-400';
  } else if (status === 'EN_ROUTE') {
    bgClass = 'bg-cyan-600';
    badgeColor = 'bg-cyan-400';
  } else {
    // OFFLINE / MAINTENANCE
    bgClass = 'bg-slate-700';
    badgeColor = 'bg-slate-500';
  }

  const selectRing = isSelected ? 'ring-4 ring-white scale-125 z-40' : '';

  const category = (resource.category || '').toUpperCase();
  let emoji = '🚚';
  if (category.includes('AMBULANCE')) emoji = '🚑';
  else if (category.includes('FIRE')) emoji = '🚒';
  else if (category.includes('POLICE')) emoji = '🚓';
  else if (category.includes('BOAT')) emoji = '🚤';
  else if (category.includes('HAZMAT')) emoji = '☣️';
  else if (category.includes('HEAVY')) emoji = '🏗️';
  else if (category.includes('DRONE')) emoji = '🛸';
  else if (category.includes('HELICOPTER')) emoji = '🚁';

  const html = `
    <div class="relative flex items-center justify-center cursor-pointer">
      <div class="${bgClass} ${selectRing} flex h-8 w-8 items-center justify-center rounded-lg text-white shadow-lg transition-transform border border-slate-950">
        <span class="text-xs select-none">${emoji}</span>
      </div>
      <span class="absolute -bottom-1 -right-1 h-2.5 w-2.5 rounded-full border border-slate-950 ${badgeColor}"></span>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'resqai-resource-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

export function ResourceMarker({
  resource,
  isSelected = false,
  onSelect,
  onAssign,
}: ResourceMarkerProps) {
  if (!resource.location?.coordinates || resource.location.coordinates.length < 2) {
    return null;
  }

  // NOTE: MongoDB stores GeoJSON as [longitude, latitude]
  // Leaflet expects [latitude, longitude]
  const [lon, lat] = resource.location.coordinates;
  if (lat === undefined || lon === undefined || isNaN(lat) || isNaN(lon)) {
    return null;
  }

  const icon = createResourceLeafletIcon(resource, isSelected);

  return (
    <Marker
      position={[lat, lon]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect?.(resource),
      }}
    >
      <Popup className="resqai-dark-popup">
        <div className="p-1.5 min-w-[210px] max-w-[260px] bg-slate-950 text-slate-100 rounded-lg text-xs font-mono">
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2 mb-2">
            <div>
              <h4 className="font-bold text-white text-xs leading-tight">
                {resource.name}
              </h4>
              <span className="font-mono text-[10px] text-cyan-400">
                {resource.resource_id}
              </span>
            </div>
            <span
              className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                resource.status === 'AVAILABLE'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : resource.status === 'BUSY'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : resource.status === 'EN_ROUTE'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {resource.status}
            </span>
          </div>

          <div className="text-[11px] text-slate-300 space-y-1 mb-2">
            <p>🏷️ Category: <span className="text-white capitalize">{resource.category?.replace(/_/g, ' ')}</span></p>
            <p>
              🛠️ Capabilities:{' '}
              <span className="text-slate-400">
                {resource.capabilities?.join(', ') || 'Standard'}
              </span>
            </p>
            {resource.current_incident_id && (
              <p>🎯 Bound to: <span className="text-cyan-400 font-bold">{resource.current_incident_id}</span></p>
            )}
          </div>

          {resource.status === 'AVAILABLE' && onAssign && (
            <button
              type="button"
              onClick={() => onAssign(resource)}
              className="w-full py-1 text-center text-xs font-bold rounded bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
            >
              Dispatch Unit
            </button>
          )}
        </div>
      </Popup>
    </Marker>
  );
}

export default ResourceMarker;
