'use client';

import React, { useState } from 'react';
import { Polyline, Tooltip, useMap } from 'react-leaflet';
import { TacticalUnitRoute } from '@/hooks/useUnitRoutes';

interface RouteLayerProps {
  routes: TacticalUnitRoute[];
  hoveredUnitId?: string | null;
  selectedUnitId?: string | null;
  onHoverUnit?: (unitId: string | null) => void;
  onSelectUnit?: (unitId: string) => void;
  showRoutes?: boolean;
}

/**
 * RouteLayer: Renders intelligent, road-following, animated, color-coded polylines
 * connecting emergency fleet units to the active incident.
 */
export const RouteLayer: React.FC<RouteLayerProps> = ({
  routes,
  hoveredUnitId,
  selectedUnitId,
  onHoverUnit,
  onSelectUnit,
  showRoutes = true,
}) => {
  const map = useMap();
  const currentZoom = map.getZoom();

  // Local hover state for individual route polylines
  const [localHoveredId, setLocalHoveredId] = useState<string | null>(null);

  if (!showRoutes || routes.length === 0) {
    return null;
  }

  // Adjust dashArray proportionally with zoom level to maintain consistent visual rhythm
  const getZoomAdjustedDashArray = (baseDash: string): string => {
    if (currentZoom >= 14) {
      // Slightly larger dashes at close street zoom
      return baseDash
        .split(',')
        .map((s) => Math.round(parseFloat(s.trim()) * 1.2))
        .join(', ');
    }
    if (currentZoom <= 10) {
      // Slightly tighter dashes at wide regional zoom
      return baseDash
        .split(',')
        .map((s) => Math.max(2, Math.round(parseFloat(s.trim()) * 0.85)))
        .join(', ');
    }
    return baseDash;
  };

  return (
    <>
      {routes.map((route) => {
        // Dispatched or currently hovered/selected units take visual precedence
        const isHovered = hoveredUnitId === route.unitId || localHoveredId === route.unitId;
        const isSelected = selectedUnitId === route.unitId;
        const isProminent = isHovered || isSelected;

        // Skip un-dispatched units unless hovered/previewed
        if (!route.isDispatched && !isProminent) {
          // Render subtle, faint preview line for recommended units
          return (
            <Polyline
              key={`rec-${route.unitId}`}
              positions={route.remainingCoordinates}
              eventHandlers={{
                mouseover: () => {
                  setLocalHoveredId(route.unitId);
                  onHoverUnit?.(route.unitId);
                },
                mouseout: () => {
                  setLocalHoveredId(null);
                  onHoverUnit?.(null);
                },
                click: () => onSelectUnit?.(route.unitId),
              }}
              pathOptions={{
                color: '#94a3b8',
                weight: 2,
                dashArray: getZoomAdjustedDashArray('4, 6'),
                opacity: 0.45,
              }}
            >
              <Tooltip sticky direction="top" className="tactical-route-tooltip">
                <div className="p-2 text-xs font-sans space-y-1 bg-white rounded-lg shadow-md border border-slate-200">
                  <div className="font-bold text-slate-800 flex items-center justify-between gap-3">
                    <span>{route.unitName}</span>
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono">
                      STANDBY
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center gap-2">
                    <span>Est. Distance: {route.distanceKm} km</span>
                    <span>•</span>
                    <span>ETA: {route.durationMin} min</span>
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium">
                    Click to view recommendation details
                  </div>
                </div>
              </Tooltip>
            </Polyline>
          );
        }

        const dashArray = getZoomAdjustedDashArray(route.style.dashArray);
        const weight = isProminent ? 5.5 : route.style.weight;
        const opacity = isProminent ? 1.0 : route.isDispatched ? 0.9 : 0.65;
        const animClass = route.isDispatched ? 'route-flow-animated' : '';
        const highlightClass = isProminent ? 'tactical-route-highlight' : '';

        return (
          <Polyline
            key={`route-${route.unitId}-${route.isDispatched ? 'active' : 'standby'}`}
            positions={route.remainingCoordinates}
            eventHandlers={{
              mouseover: () => {
                setLocalHoveredId(route.unitId);
                onHoverUnit?.(route.unitId);
              },
              mouseout: () => {
                setLocalHoveredId(null);
                onHoverUnit?.(null);
              },
              click: () => onSelectUnit?.(route.unitId),
            }}
            pathOptions={{
              color: route.style.color,
              weight,
              dashArray,
              opacity,
              className: `${animClass} ${highlightClass}`.trim(),
            }}
          >
            <Tooltip sticky direction="top" className="tactical-route-tooltip">
              <div className="p-2.5 text-xs font-sans space-y-1.5 bg-white/98 backdrop-blur-sm rounded-xl shadow-lg border border-slate-200 min-w-[210px]">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                  <span className="font-bold text-slate-900 text-[12px]">{route.unitName}</span>
                  <span
                    className="text-[9px] font-black uppercase px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: `${route.style.color}15`,
                      color: route.style.color,
                      border: `1px solid ${route.style.color}35`,
                    }}
                  >
                    {route.arrived ? 'ARRIVED' : route.isDispatched ? 'EN ROUTE' : 'RECOMMENDED'}
                  </span>
                </div>

                {/* Telemetry row */}
                <div className="grid grid-cols-2 gap-2 text-[11px] pt-0.5">
                  <div className="bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                      Distance
                    </span>
                    <span className="font-extrabold text-slate-800 font-mono">
                      {route.distanceKm} km
                    </span>
                  </div>
                  <div className="bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                    <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                      Live ETA
                    </span>
                    <span className="font-extrabold text-red-600 font-mono">
                      {route.arrived ? 'On Scene' : `${route.durationMin} min`}
                    </span>
                  </div>
                </div>

                {/* Road vs Aerial indicator */}
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                  <span className="flex items-center gap-1 font-medium">
                    {route.isDrone ? '🛸 Aerial Line-of-Sight' : route.isRoadRoute ? '🛣️ OSRM Road Route' : '📍 Tactical Waypoints'}
                  </span>
                  <span className="text-red-600 font-bold hover:underline cursor-pointer">
                    Inspect Unit →
                  </span>
                </div>
              </div>
            </Tooltip>
          </Polyline>
        );
      })}
    </>
  );
};

export default RouteLayer;
