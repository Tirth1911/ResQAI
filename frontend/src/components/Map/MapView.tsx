'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Incident, Resource, Hospital } from '@/types';
import { IncidentMarker } from './IncidentMarker';
import { ResourceMarker } from './ResourceMarker';
import {
  Layers,
  Crosshair,
  Maximize2,
  Filter,
  Eye,
  EyeOff,
  Flame,
  Truck,
  RotateCcw,
} from 'lucide-react';

interface MapViewProps {
  incidents: Incident[];
  resources?: Resource[];
  hospitals?: Hospital[];
  selectedIncident?: Incident | null;
  onSelectIncident?: (incident: Incident) => void;
  onSelectResource?: (resource: Resource) => void;
  onAssignResource?: (resource: Resource) => void;
  center?: [number, number]; // [lat, lon]
  zoom?: number;
  showResourcesToggle?: boolean;
  showRadiusToggle?: boolean;
  className?: string;
}

// Controller component to interact with the Leaflet map instance
function MapController({
  selectedIncident,
  filteredIncidents,
  triggerFitAll,
  center,
  zoom,
}: {
  selectedIncident?: Incident | null;
  filteredIncidents: Incident[];
  triggerFitAll: number;
  center?: [number, number];
  zoom?: number;
}) {
  const map = useMap();

  // Locate selected incident
  useEffect(() => {
    if (selectedIncident?.location?.coordinates && selectedIncident.location.coordinates.length >= 2) {
      const [lon, lat] = selectedIncident.location.coordinates;
      if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
        map.flyTo([lat, lon], 14, { duration: 1.2 });
      }
    }
  }, [selectedIncident, map]);

  // Fit all active incidents
  useEffect(() => {
    if (triggerFitAll > 0 && filteredIncidents.length > 0) {
      const validPoints: [number, number][] = [];
      filteredIncidents.forEach((inc) => {
        if (inc.location?.coordinates && inc.location.coordinates.length >= 2) {
          const [lon, lat] = inc.location.coordinates;
          if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
            validPoints.push([lat, lon]);
          }
        }
      });

      if (validPoints.length > 0) {
        const bounds = L.latLngBounds(validPoints);
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
      }
    }
  }, [triggerFitAll, filteredIncidents, map]);

  return null;
}

import MapLegend from './MapLegend';

export function MapView({
  incidents,
  resources = [],
  hospitals = [],
  selectedIncident = null,
  onSelectIncident,
  onSelectResource,
  onAssignResource,
  center = [28.6139, 77.209], // Default Delhi / NCR coordinates [lat, lon]
  zoom = 12,
  showResourcesToggle = true,
  showRadiusToggle = true,
  className = '',
}: MapViewProps) {
  // Visibility toggles
  const [showIncidents, setShowIncidents] = useState(true);
  const [showResources, setShowResources] = useState(true);
  const [showRadius, setShowRadius] = useState(true);
  const [tileMode, setTileMode] = useState<'osm' | 'dark' | 'satellite'>('osm');

  // Filter states
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);

  // Trigger state for Fit All
  const [fitAllTrigger, setFitAllTrigger] = useState(0);

  // Filtered Incidents calculation
  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      const matchesSeverity =
        filterSeverity === 'ALL' || inc.severity === filterSeverity;
      const matchesType =
        filterType === 'ALL' || inc.type.toLowerCase() === filterType.toLowerCase();
      const matchesStatus =
        filterStatus === 'ALL' || inc.status === filterStatus;
      return matchesSeverity && matchesType && matchesStatus;
    });
  }, [incidents, filterSeverity, filterType, filterStatus]);

  // Tile configurations using OpenStreetMap tiles
  const getTileConfig = () => {
    if (tileMode === 'dark') {
      return {
        url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      };
    }
    if (tileMode === 'satellite') {
      return {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
      };
    }
    // Default clean OpenStreetMap tile layer
    return {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    };
  };

  const activeTile = getTileConfig();

  const handleFitAll = () => {
    setFitAllTrigger((prev) => prev + 1);
  };

  const handleResetFilters = () => {
    setFilterSeverity('ALL');
    setFilterType('ALL');
    setFilterStatus('ALL');
  };

  const hasActiveFilters =
    filterSeverity !== 'ALL' || filterType !== 'ALL' || filterStatus !== 'ALL';

  return (
    <div className={`relative h-full w-full overflow-hidden rounded-lg border border-slate-200 bg-white ${className}`}>
      {/* Tactical Top Bar: Layer & Filter Controls */}
      <div className="absolute top-3 left-3 right-3 z-[1000] flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Left Quick Action Pill */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/95 p-1.5 shadow-md backdrop-blur-md text-xs pointer-events-auto">
          {/* Fit all active incidents */}
          <button
            type="button"
            onClick={handleFitAll}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold transition-colors"
            title="Fit map view to all active emergency incidents"
          >
            <Maximize2 className="h-3.5 w-3.5 text-red-600" />
            <span>Fit All ({filteredIncidents.length})</span>
          </button>

          {/* Filter Drawer Toggle */}
          <button
            type="button"
            onClick={() => setShowFilterDrawer(!showFilterDrawer)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded transition-colors ${
              hasActiveFilters || showFilterDrawer
                ? 'bg-red-50 text-red-700 border border-red-200 font-semibold'
                : 'text-slate-600 hover:text-slate-900 bg-slate-100'
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            <span>Filter</span>
            {hasActiveFilters && (
              <span className="h-1.5 w-1.5 rounded-full bg-red-600" />
            )}
          </button>
        </div>

        {/* Right Layer & Visibility Toggles */}
        <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-slate-200 bg-white/95 p-1.5 shadow-md backdrop-blur-md text-xs pointer-events-auto">
          {/* Incident Visibility Toggle */}
          <button
            type="button"
            onClick={() => setShowIncidents(!showIncidents)}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              showIncidents
                ? 'bg-red-50 text-red-700 border border-red-200 font-semibold'
                : 'text-slate-500 hover:text-slate-700'
            }`}
            title="Toggle Emergency Incident Markers"
          >
            <Flame className="h-3.5 w-3.5 text-red-600" />
            <span>Incidents ({filteredIncidents.length})</span>
          </button>

          {/* Resource Visibility Toggle */}
          {showResourcesToggle && (
            <button
              type="button"
              onClick={() => setShowResources(!showResources)}
              className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
                showResources
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
              title="Toggle Resource Fleet Markers"
            >
              <Truck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Units ({resources.length})</span>
            </button>
          )}

          {/* 1km Dedup Radius Toggle */}
          {showRadiusToggle && (
            <button
              type="button"
              onClick={() => setShowRadius(!showRadius)}
              className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
                showRadius
                  ? 'bg-blue-50 text-blue-700 border border-blue-200 font-semibold'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
              title="Toggle 1km Deduplication / Hazard Radius"
            >
              <span>🎯</span>
              <span>1km Radius</span>
            </button>
          )}

          {/* Tile Layer Switcher */}
          <select
            value={tileMode}
            onChange={(e) => setTileMode(e.target.value as any)}
            className="rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 focus:outline-none"
          >
            <option value="osm">Standard Map</option>
            <option value="dark">Humanitarian</option>
            <option value="satellite">Satellite</option>
          </select>
        </div>
      </div>

      {/* Expandable Filter Drawer */}
      {showFilterDrawer && (
        <div className="absolute top-16 left-3 z-[1000] w-80 rounded-xl border border-slate-800 bg-slate-950/95 p-4 shadow-2xl backdrop-blur-md text-xs font-mono space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5 text-cyan-400" />
              <span>Tactical Map Filters</span>
            </h4>
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="text-[10px] text-cyan-400 hover:underline flex items-center gap-0.5"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Reset</span>
              </button>
            )}
          </div>

          {/* Filter: Severity */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">
              Severity Level
            </label>
            <div className="grid grid-cols-5 gap-1">
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setFilterSeverity(sev)}
                  className={`py-1 rounded text-[10px] font-semibold uppercase transition-colors ${
                    filterSeverity === sev
                      ? 'bg-cyan-600 text-white shadow'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {sev === 'CRITICAL' ? 'CRIT' : sev}
                </button>
              ))}
            </div>
          </div>

          {/* Filter: Incident Type */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">
              Incident Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
            >
              <option value="ALL">All Types</option>
              <option value="fire">Fire</option>
              <option value="flood">Flood</option>
              <option value="road_accident">Road Accident</option>
              <option value="medical_emergency">Medical Emergency</option>
              <option value="industrial_hazard">Industrial Hazard</option>
              <option value="building_collapse">Building Collapse</option>
              <option value="gas_leak">Gas Leak</option>
              <option value="earthquake">Earthquake</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Filter: Status */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate-400 mb-1">
              Lifecycle Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="REPORTED">Reported</option>
              <option value="VERIFIED">Verified</option>
              <option value="DISPATCHED">Dispatched</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div className="pt-1 text-[10px] text-slate-500 text-right">
            Displaying {filteredIncidents.length} of {incidents.length} incidents
          </div>
        </div>
      )}

      {/* Map Container */}
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution={activeTile.attribution}
          url={activeTile.url}
        />

        <MapController
          selectedIncident={selectedIncident}
          filteredIncidents={filteredIncidents}
          triggerFitAll={fitAllTrigger}
          center={center}
          zoom={zoom}
        />

        {/* Render Incident Markers */}
        {showIncidents &&
          filteredIncidents.map((incident) => (
            <IncidentMarker
              key={incident.incident_id || incident.id || incident._id}
              incident={incident}
              isSelected={selectedIncident?.incident_id === incident.incident_id}
              onSelect={onSelectIncident}
              showRadius={showRadius}
            />
          ))}

        {/* Render Resource Markers */}
        {showResources &&
          resources.map((resource) => (
            <ResourceMarker
              key={resource.resource_id || resource.id || resource._id}
              resource={resource}
              onSelect={onSelectResource}
              onAssign={onAssignResource}
            />
          ))}
      </MapContainer>

      {/* Map Legend Overlay */}
      <MapLegend />
    </div>
  );
}

export default MapView;
