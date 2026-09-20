'use client';

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Incident, Resource, DispatchRecommendation } from '../types';
import { Flame, Truck, AlertTriangle, Shield, CheckCircle, Navigation, Radio, MapPin, X, AlertCircle } from 'lucide-react';

interface TacticalMapProps {
  incidents: Incident[];
  resources: Resource[];
  selectedIncident: Incident | null;
  onSelectIncident: (inc: Incident) => void;
  onDispatchUnit: (incidentId: string, resourceId: string) => void;
  recommendations: DispatchRecommendation[];
}

// Custom Leaflet DivIcons for Clean GIS Aesthetic
const createIncidentIcon = (severity: string, isSelected: boolean) => {
  let bgColor = 'bg-[#C62828]';
  let ringColor = 'border-[#C62828]/40';
  let iconText = '🔥';

  if (severity === 'critical') {
    bgColor = 'bg-[#C62828]';
    ringColor = 'border-[#C62828]/50';
    iconText = '🚨';
  } else if (severity === 'high') {
    bgColor = 'bg-[#C47A00]';
    ringColor = 'border-[#C47A00]/40';
    iconText = '⚠️';
  } else if (severity === 'medium') {
    bgColor = 'bg-[#EAB308]';
    ringColor = 'border-[#EAB308]/40';
    iconText = '⚡';
  } else {
    bgColor = 'bg-[#2563EB]';
    ringColor = 'border-[#2563EB]/40';
    iconText = 'ℹ️';
  }

  const selectedClass = isSelected ? 'scale-125 ring-4 ring-white shadow-xl z-50' : '';

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div class="relative flex items-center justify-center w-8 h-8 ${selectedClass} transition-transform">
        <span class="absolute inline-flex h-full w-full rounded-full border-2 ${ringColor} animate-ping"></span>
        <div class="relative inline-flex items-center justify-center w-7 h-7 rounded-full ${bgColor} text-white shadow-md font-bold text-xs ring-2 ring-white">
          <span>${iconText}</span>
        </div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

const createResourceIcon = (kind: string, status: string) => {
  let iconEmoji = '🚒';
  let badgeColor = 'bg-[#B42318]';

  if (kind === 'ambulance') {
    iconEmoji = '🚑';
    badgeColor = 'bg-[#16803C]';
  } else if (kind === 'police_van') {
    iconEmoji = '🚓';
    badgeColor = 'bg-[#2563EB]';
  } else if (kind === 'hazmat_unit') {
    iconEmoji = '☣️';
    badgeColor = 'bg-[#7C3AED]';
  } else if (kind === 'rescue_boat') {
    iconEmoji = '🚤';
    badgeColor = 'bg-[#0284C7]';
  } else if (kind === 'ndrf_team') {
    iconEmoji = '🛟';
    badgeColor = 'bg-[#D97706]';
  } else if (kind === 'drone') {
    iconEmoji = '🛸';
    badgeColor = 'bg-[#0891B2]';
  }

  const isDispatched = status === 'dispatched';

  return L.divIcon({
    className: 'custom-resource-marker',
    html: `
      <div class="flex items-center justify-center w-7 h-7 rounded-lg ${badgeColor} text-white shadow-md border-2 border-white text-xs ${isDispatched ? 'ring-2 ring-[#16803C]' : ''}">
        <span>${iconEmoji}</span>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
};

// Controller component to pan map smoothly when selectedIncident changes
function MapController({ selectedIncident }: { selectedIncident: Incident | null }) {
  const map = useMap();
  useEffect(() => {
    if (selectedIncident) {
      map.flyTo([selectedIncident.lat, selectedIncident.lng], 13.5, { duration: 1.2 });
    }
  }, [selectedIncident, map]);
  return null;
}

export default function TacticalMap({
  incidents,
  resources,
  selectedIncident,
  onSelectIncident,
  onDispatchUnit,
  recommendations
}: TacticalMapProps) {
  const [mapHasError, setMapHasError] = useState<boolean>(false);

  const centerLat = selectedIncident ? selectedIncident.lat : 23.0300;
  const centerLng = selectedIncident ? selectedIncident.lng : 72.5700;

  return (
    <div className="relative w-full h-[calc(100vh-4.5rem)] bg-[#F5F1E8] flex overflow-hidden">
      
      {/* Light Map Area */}
      <div className="flex-1 relative h-full">
        {mapHasError && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 bg-[#FEF6E7] border border-[#FDE68A] text-[#C47A00] px-4 py-2 rounded-xl text-xs font-semibold shadow-md flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-[#C47A00]" />
            <span>Map Tile Provider connection degraded. Retrying tile stream...</span>
          </div>
        )}

        <MapContainer
          center={[centerLat, centerLng]}
          zoom={12}
          scrollWheelZoom={true}
          className="w-full h-full z-0"
          style={{ background: '#F5F1E8' }}
        >
          {/* Official OpenStreetMap Light Tile Layer (No API Key Required) */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
            eventHandlers={{
              tileerror: () => setMapHasError(true)
            }}
          />

          <MapController selectedIncident={selectedIncident} />

          {/* Render Active Incidents */}
          {incidents.map((incident) => {
            const isSelected = selectedIncident?.id === incident.id;
            return (
              <React.Fragment key={incident.id}>
                {incident.severity === 'critical' && (
                  <Circle
                    center={[incident.lat, incident.lng]}
                    radius={1000}
                    pathOptions={{
                      color: '#C62828',
                      fillColor: '#C62828',
                      fillOpacity: 0.08,
                      dashArray: '4, 6',
                      weight: 1.5
                    }}
                  />
                )}

                <Marker
                  position={[incident.lat, incident.lng]}
                  icon={createIncidentIcon(incident.severity, isSelected)}
                  eventHandlers={{
                    click: () => onSelectIncident(incident)
                  }}
                >
                  <Popup className="tactical-popup">
                    <div className="p-3 bg-white text-[#1F2933] rounded-xl min-w-[240px] text-xs font-sans">
                      <div className="flex items-center justify-between gap-2 border-b border-[#DED8CC] pb-2 mb-2">
                        <span className="font-bold text-sm text-[#1F2933]">{incident.title}</span>
                        <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded ${
                          incident.severity === 'critical' ? 'bg-[#FEEFEF] text-[#C62828] border border-[#FCA5A5]' :
                          incident.severity === 'high' ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]' :
                          'bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]'
                        }`}>
                          {incident.severity}
                        </span>
                      </div>
                      <p className="text-[#667085] text-[11px] leading-snug mb-2">{incident.description}</p>
                      <div className="text-[10px] text-[#667085] space-y-1 mb-3">
                        <div>📍 {incident.address}</div>
                        <div>📞 Merged Reports: <strong className="text-[#1F2933]">{incident.report_count}</strong></div>
                      </div>
                      <button
                        onClick={() => onSelectIncident(incident)}
                        className="w-full py-1.5 bg-[#B42318] hover:bg-[#911E14] text-white rounded-lg font-semibold text-center transition-colors text-xs"
                      >
                        Open Dispatch Panel
                      </button>
                    </div>
                  </Popup>
                </Marker>
              </React.Fragment>
            );
          })}

          {/* Render Fleet Resources */}
          {resources.map((resource) => (
            <Marker
              key={resource.id}
              position={[resource.lat, resource.lng]}
              icon={createResourceIcon(resource.kind, resource.status)}
            >
              <Popup>
                <div className="p-2.5 bg-white text-[#1F2933] text-xs font-sans rounded-lg">
                  <div className="font-bold text-sm text-[#16803C]">{resource.name}</div>
                  <div className="text-[11px] text-[#667085] mt-1">Station: {resource.station}</div>
                  <div className="text-[11px] text-[#667085]">Status: <span className="text-[#1F2933] font-bold uppercase">{resource.status}</span></div>
                  <div className="text-[11px] text-[#667085]">Capacity: {resource.capacity} Personnel</div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Render Active Dispatch Route Lines */}
          {incidents.flatMap((inc) => 
            (inc.assignments || []).map((asgn) => {
              const res = resources.find((r) => r.id === asgn.resource_id);
              if (!res) return null;
              return (
                <Polyline
                  key={asgn.id}
                  positions={[
                    [res.lat, res.lng],
                    [inc.lat, inc.lng]
                  ]}
                  pathOptions={{
                    color: '#16803C',
                    weight: 3,
                    opacity: 0.85,
                    dashArray: '6, 6'
                  }}
                />
              );
            })
          )}
        </MapContainer>

        {/* Clean Floating GIS Legend */}
        <div className="absolute bottom-6 left-6 z-20 bg-white border border-[#DED8CC] p-4 rounded-xl shadow-md text-[#1F2933] text-xs space-y-2.5 font-sans min-w-[200px]">
          <div className="font-bold text-[#1F2933] border-b border-[#DED8CC] pb-1.5 flex items-center justify-between text-xs tracking-wider uppercase">
            <span>MAP LEGEND</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#C62828]"></span><span>🔴 Critical Incident</span></div>
            <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#C47A00]"></span><span>🟠 High Severity</span></div>
            <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#EAB308]"></span><span>🟡 Medium Severity</span></div>
            <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]"></span><span>🔵 Police Patrol</span></div>
            <div className="flex items-center gap-2"><span>🚒</span><span>Fire & Rescue</span></div>
            <div className="flex items-center gap-2"><span>🚑</span><span>Medical 108</span></div>
            <div className="flex items-center gap-2"><span>🚁</span><span>Drone Recon</span></div>
          </div>
        </div>
      </div>

      {/* Right Incident Sidebar Panel */}
      {selectedIncident && (
        <div className="w-[440px] bg-white border-l border-[#DED8CC] p-6 overflow-y-auto flex flex-col gap-6 text-[#1F2933] z-10 shadow-lg font-sans">
          
          {/* Header Box */}
          <div className="flex items-start justify-between gap-3 border-b border-[#DED8CC] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-[#F5F1E8] border border-[#DED8CC] text-[#1F2933]">
                  {selectedIncident.id}
                </span>
                <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                  selectedIncident.severity === 'critical' ? 'bg-[#FEEFEF] text-[#C62828] border border-[#FCA5A5]' :
                  selectedIncident.severity === 'high' ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]' :
                  'bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]'
                }`}>
                  {selectedIncident.severity === 'critical' ? 'Critical Priority' : selectedIncident.severity === 'high' ? 'High Priority' : 'Medium Priority'}
                </span>
              </div>
              <h2 className="text-lg font-bold text-[#1F2933] mt-2 leading-snug">{selectedIncident.title}</h2>
            </div>
            <button
              onClick={() => onSelectIncident(null as any)}
              className="text-[#667085] hover:text-[#1F2933] p-1 rounded-lg hover:bg-[#F5F1E8]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Location & AI Triage Box */}
          <div className="space-y-3 bg-[#F5F1E8] p-4 rounded-xl border border-[#DED8CC] text-xs">
            <div>
              <span className="text-[10px] font-bold text-[#667085] uppercase tracking-wider block mb-1">LOCATION</span>
              <div className="text-[#1F2933] font-medium flex items-start gap-1.5">
                <MapPin className="w-4 h-4 text-[#B42318] shrink-0 mt-0.5" />
                <span>{selectedIncident.address}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-[#DED8CC]">
              <span className="text-[10px] font-bold text-[#667085] uppercase tracking-wider block mb-1">AI TRIAGE ANALYSIS</span>
              <p className="text-[#1F2933] text-xs leading-relaxed">{selectedIncident.ai_reasoning}</p>
            </div>

            {/* Horizontal Priority Score Bar */}
            <div className="pt-2 border-t border-[#DED8CC]">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-[#667085] font-medium">Priority Score</span>
                <span className="font-bold text-[#1F2933]">{selectedIncident.priority} / 100</span>
              </div>
              <div className="w-full h-2 rounded-full bg-[#DED8CC] overflow-hidden">
                <div
                  className="h-full bg-[#B42318] rounded-full transition-all duration-500"
                  style={{ width: `${selectedIncident.priority}%` }}
                />
              </div>
            </div>
          </div>

          {/* Recommended Response Units */}
          <div className="space-y-3 flex-1">
            <h3 className="text-xs font-bold text-[#667085] uppercase tracking-wider">
              RECOMMENDED RESPONSE UNITS
            </h3>

            {recommendations.length === 0 ? (
              <div className="p-4 bg-[#F5F1E8] text-center text-xs text-[#667085] rounded-xl border border-[#DED8CC]">
                No available response units matching criteria right now.
              </div>
            ) : (
              <div className="space-y-3">
                {recommendations.slice(0, 4).map((rec) => {
                  const isAssigned = (selectedIncident.assignments || []).some(a => a.resource_id === rec.resource.id);

                  return (
                    <div
                      key={rec.resource.id}
                      className={`p-4 rounded-xl border transition-all space-y-3 text-xs ${
                        isAssigned
                          ? 'bg-[#EAF6ED] border-[#16803C]'
                          : 'bg-white border-[#DED8CC] hover:border-[#B42318]/50 shadow-xs'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-[#1F2933] text-sm">{rec.resource.name}</h4>
                          <span className="text-[#667085] text-xs">{rec.resource.station}</span>
                        </div>
                        <span className="px-2.5 py-1 rounded bg-[#FDECEC] text-[#B42318] font-bold text-xs">
                          {rec.score}% MATCH
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 py-2 px-3 bg-[#F5F1E8] rounded-lg text-[11px] text-[#667085]">
                        <div>📍 {rec.distance_km} km away</div>
                        <div>⏱️ ETA {rec.eta_min} min</div>
                        <div>👥 Capacity {rec.resource.capacity}</div>
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[11px] text-[#667085]">
                          {rec.match_reasons[0]}
                        </span>

                        {isAssigned ? (
                          <span className="px-4 py-2 bg-[#16803C] text-white font-bold text-xs rounded-lg flex items-center gap-1.5">
                            <CheckCircle className="w-4 h-4 text-white" />
                            <span>DISPATCHED ✓</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => onDispatchUnit(selectedIncident.id, rec.resource.id)}
                            className="px-4 py-2 bg-[#B42318] hover:bg-[#911E14] text-white font-bold text-xs rounded-lg transition-colors shadow-xs flex items-center gap-1.5"
                          >
                            <Truck className="w-4 h-4" />
                            <span>Dispatch Unit</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
