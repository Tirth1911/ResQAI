'use client';

import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Incident, Resource } from '@/types';
import { fetchTacticalRoute, RouteResult, calculateHaversineKm, isDroneCategory } from '@/services/routingService';

export type UnitTypeKey = 'fire' | 'medical' | 'police' | 'drone' | 'ndrf' | 'recommended';

export interface TacticalRouteStyle {
  color: string;
  dashArray: string;
  weight: number;
  label: string;
  unitType: UnitTypeKey;
}

export interface TacticalUnitRoute {
  unitId: string;
  unitName: string;
  incidentId: string;
  isDispatched: boolean;
  style: TacticalRouteStyle;
  fullCoordinates: [number, number][];
  remainingCoordinates: [number, number][];
  distanceKm: number;
  durationMin: number;
  currentCoord: [number, number];
  progress: number; // 0.0 to 1.0
  arrived: boolean;
  isRoadRoute: boolean;
  isDrone: boolean;
}

export const UNIT_TYPE_STYLES: Record<UnitTypeKey, TacticalRouteStyle> = {
  fire: {
    color: '#ef4444', // Red
    dashArray: '10, 8',
    weight: 3.5,
    label: 'Fire & Rescue',
    unitType: 'fire',
  },
  medical: {
    color: '#10b981', // Green
    dashArray: '8, 6',
    weight: 3.5,
    label: 'Medical 108',
    unitType: 'medical',
  },
  police: {
    color: '#3b82f6', // Blue
    dashArray: '12, 6, 3, 6',
    weight: 3.5,
    label: 'Police Patrol',
    unitType: 'police',
  },
  drone: {
    color: '#a855f7', // Purple
    dashArray: '3, 7',
    weight: 3.0,
    label: 'Drone Recon',
    unitType: 'drone',
  },
  ndrf: {
    color: '#f97316', // Orange
    dashArray: '14, 7',
    weight: 3.5,
    label: 'NDRF / Heavy Rescue',
    unitType: 'ndrf',
  },
  recommended: {
    color: '#94a3b8', // Slate-400
    dashArray: '5, 6',
    weight: 2.5,
    label: 'Recommended Unit',
    unitType: 'recommended',
  },
};

/**
 * Classify a unit into a standardized Tactical Unit Type.
 */
export function getUnitType(category?: string, name?: string, capabilities?: string[]): UnitTypeKey {
  const cat = (category || '').toUpperCase();
  const n = (name || '').toUpperCase();
  const caps = (capabilities || []).map((c) => c.toUpperCase());

  if (isDroneCategory(category, name) || caps.includes('DRONE') || caps.includes('UAV')) {
    return 'drone';
  }
  if (
    cat.includes('FIRE') ||
    n.includes('FIRE') ||
    caps.includes('FIRE_TRUCK') ||
    caps.includes('FOAM_TENDER') ||
    caps.includes('EXTRICATION')
  ) {
    return 'fire';
  }
  if (
    cat.includes('AMBULANCE') ||
    cat.includes('MEDICAL') ||
    n.includes('108') ||
    n.includes('AMBULANCE') ||
    n.includes('TRAUMA') ||
    caps.includes('AMBULANCE') ||
    caps.includes('ALS') ||
    caps.includes('PARAMEDIC')
  ) {
    return 'medical';
  }
  if (
    cat.includes('POLICE') ||
    n.includes('POLICE') ||
    n.includes('PATROL') ||
    caps.includes('POLICE') ||
    caps.includes('CORDON') ||
    caps.includes('GREEN_CORRIDOR')
  ) {
    return 'police';
  }
  if (
    cat.includes('DISASTER') ||
    cat.includes('HAZMAT') ||
    n.includes('NDRF') ||
    n.includes('RESCUE') ||
    n.includes('HAZMAT') ||
    caps.includes('HAZMAT') ||
    caps.includes('CHEMICAL_NEUTRALIZATION') ||
    caps.includes('DECONTAMINATION')
  ) {
    return 'ndrf';
  }

  return 'fire';
}

interface UseUnitRoutesProps {
  selectedIncident: Incident | null;
  resources: Resource[];
  recommendations?: any[];
  isSimulating?: boolean;
  simulationSpeed?: number;
}

export function useUnitRoutes({
  selectedIncident,
  resources,
  recommendations = [],
  isSimulating = false,
  simulationSpeed = 1.0,
}: UseUnitRoutesProps) {
  // Raw fetched routes: unitId -> RouteResult
  const [routesMap, setRoutesMap] = useState<Record<string, RouteResult>>({});
  // Simulation progress per unit: unitId -> 0.0 to 1.0
  const [progressMap, setProgressMap] = useState<Record<string, number>>({});
  const isFetchingRef = useRef(false);

  // Determine which units are dispatched to selected incident
  const dispatchedUnitIds = useMemo(() => {
    if (!selectedIncident) return new Set<string>();
    const ids = new Set<string>();
    (selectedIncident.assigned_resources || []).forEach((id) => ids.add(id));
    resources.forEach((r) => {
      const assignedId = r.current_incident_id || (r as any).assigned_incident_id;
      if (assignedId === selectedIncident.incident_id || assignedId === selectedIncident.id) {
        ids.add(r.resource_id);
      }
    });
    return ids;
  }, [selectedIncident, resources]);

  // Fetch routes for all relevant units when selected incident changes
  useEffect(() => {
    if (!selectedIncident?.location?.coordinates) {
      setRoutesMap({});
      setProgressMap({});
      return;
    }

    const [incLon, incLat] = selectedIncident.location.coordinates;
    if (isNaN(incLat) || isNaN(incLon)) return;

    let isMounted = true;

    async function loadAllRoutes() {
      if (isFetchingRef.current) return;
      isFetchingRef.current = true;

      const newRoutes: Record<string, RouteResult> = {};
      const unitsToFetch = resources.filter((r) => r.location?.coordinates && r.location.coordinates.length >= 2);

      // Fetch routes with controlled concurrency
      for (const res of unitsToFetch) {
        const [rLon, rLat] = res.location!.coordinates;
        if (isNaN(rLat) || isNaN(rLon)) continue;

        try {
          const route = await fetchTacticalRoute(
            [rLat, rLon],
            [incLat, incLon],
            res.category || (res as any).type,
            res.name
          );
          newRoutes[res.resource_id] = route;
        } catch (e) {
          console.error(`Route fetch failed for ${res.resource_id}`, e);
        }
      }

      if (isMounted) {
        setRoutesMap(newRoutes);
        isFetchingRef.current = false;
      }
    }

    loadAllRoutes();

    return () => {
      isMounted = false;
      isFetchingRef.current = false;
    };
  }, [selectedIncident?.incident_id, resources]);

  // Handle Simulation Animation Loop
  useEffect(() => {
    if (!isSimulating) {
      // If simulation stopped, we keep current progress or allow manual reset
      return;
    }

    const intervalMs = 250;
    const stepIncrement = 0.015 * simulationSpeed; // ~16 seconds for full route traversal

    const timer = setInterval(() => {
      setProgressMap((prev) => {
        let changed = false;
        const next = { ...prev };

        dispatchedUnitIds.forEach((unitId) => {
          const current = prev[unitId] || 0;
          if (current < 1.0) {
            next[unitId] = Math.min(1.0, current + stepIncrement);
            changed = true;
          }
        });

        return changed ? next : prev;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isSimulating, simulationSpeed, dispatchedUnitIds]);

  // Reset simulation helper
  const resetSimulation = useCallback(() => {
    setProgressMap({});
  }, []);

  // Compute processed Tactical Routes for rendering
  const tacticalRoutes: TacticalUnitRoute[] = useMemo(() => {
    if (!selectedIncident?.location?.coordinates) return [];
    const [incLon, incLat] = selectedIncident.location.coordinates;
    if (isNaN(incLat) || isNaN(incLon)) return [];

    const routes: TacticalUnitRoute[] = [];

    resources.forEach((resource) => {
      const coords = resource.location?.coordinates;
      if (!coords || coords.length < 2) return;
      const [rLon, rLat] = coords;
      if (isNaN(rLat) || isNaN(rLon)) return;

      const isDispatched = dispatchedUnitIds.has(resource.resource_id);
      const unitType = getUnitType(resource.category || (resource as any).type, resource.name, resource.capabilities);
      const baseStyle = UNIT_TYPE_STYLES[unitType];
      const style: TacticalRouteStyle = isDispatched
        ? baseStyle
        : {
            ...UNIT_TYPE_STYLES.recommended,
            label: `${baseStyle.label} (Standby)`,
          };

      const routeResult = routesMap[resource.resource_id];
      const fullCoordinates: [number, number][] = routeResult
        ? routeResult.coordinates
        : [
            [rLat, rLon],
            [incLat, incLon],
          ];

      const distanceKm = routeResult ? routeResult.distanceKm : parseFloat((calculateHaversineKm(rLat, rLon, incLat, incLon) * 1.25).toFixed(2));
      const durationMin = routeResult ? routeResult.durationMin : Math.max(1, Math.round((distanceKm / 40) * 60));

      const progress = progressMap[resource.resource_id] || 0;
      const arrived = progress >= 0.98;

      // Calculate current unit position and remaining coordinates
      let currentCoord: [number, number] = [rLat, rLon];
      let remainingCoordinates: [number, number][] = fullCoordinates;

      if (progress > 0 && fullCoordinates.length > 1) {
        if (arrived) {
          currentCoord = [incLat, incLon];
          remainingCoordinates = [[incLat, incLon], [incLat, incLon]];
        } else {
          const totalPoints = fullCoordinates.length;
          const floatIndex = progress * (totalPoints - 1);
          const startIndex = Math.floor(floatIndex);
          const endIndex = Math.min(startIndex + 1, totalPoints - 1);
          const segmentFraction = floatIndex - startIndex;

          const p1 = fullCoordinates[startIndex];
          const p2 = fullCoordinates[endIndex];

          const curLat = p1[0] + (p2[0] - p1[0]) * segmentFraction;
          const curLon = p1[1] + (p2[1] - p1[1]) * segmentFraction;
          currentCoord = [curLat, curLon];

          // Sliced remaining path from current position to incident
          remainingCoordinates = [[curLat, curLon], ...fullCoordinates.slice(endIndex)];
        }
      }

      // Live remaining distance and ETA
      const liveDistKm = parseFloat((distanceKm * (1 - progress)).toFixed(2));
      const liveEtaMin = arrived ? 0 : Math.max(1, Math.round(durationMin * (1 - progress)));

      routes.push({
        unitId: resource.resource_id,
        unitName: resource.name,
        incidentId: selectedIncident.incident_id,
        isDispatched,
        style,
        fullCoordinates,
        remainingCoordinates,
        distanceKm: liveDistKm,
        durationMin: liveEtaMin,
        currentCoord,
        progress,
        arrived,
        isRoadRoute: routeResult?.isRoadRoute ?? false,
        isDrone: routeResult?.isDrone ?? (unitType === 'drone'),
      });
    });

    return routes;
  }, [selectedIncident, resources, dispatchedUnitIds, routesMap, progressMap]);

  // Map of simulated coordinates for resources: resource_id -> [lat, lon]
  const simulatedPositions = useMemo(() => {
    const posMap: Record<string, [number, number]> = {};
    tacticalRoutes.forEach((tr) => {
      if (tr.progress > 0) {
        posMap[tr.unitId] = tr.currentCoord;
      }
    });
    return posMap;
  }, [tacticalRoutes]);

  // Map of live distance and ETA: resource_id -> { distanceKm, etaMin, arrived }
  const liveTelemetry = useMemo(() => {
    const telMap: Record<string, { distanceKm: number; etaMin: number; arrived: boolean }> = {};
    tacticalRoutes.forEach((tr) => {
      telMap[tr.unitId] = {
        distanceKm: tr.distanceKm,
        etaMin: tr.durationMin,
        arrived: tr.arrived,
      };
    });
    return telMap;
  }, [tacticalRoutes]);

  return {
    tacticalRoutes,
    simulatedPositions,
    liveTelemetry,
    dispatchedUnitIds,
    resetSimulation,
    hasActiveRoutes: tacticalRoutes.length > 0,
  };
}
