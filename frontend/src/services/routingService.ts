/**
 * RESQAI Tactical Routing Engine
 * Provides actual road-network routing using OSRM (Open Source Routing Machine),
 * with straight-line flight paths for aerial drones, in-memory caching,
 * and automatic fallback if the routing API is unavailable.
 */

export interface RouteResult {
  coordinates: [number, number][]; // [latitude, longitude] tuples for Leaflet
  distanceKm: number;
  durationMin: number;
  isRoadRoute: boolean;
  isDrone: boolean;
}

// In-memory route cache: key -> RouteResult
const routeCache = new Map<string, RouteResult>();

/**
 * Calculate great-circle distance between two [lat, lon] coordinates in kilometers.
 */
export function calculateHaversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Determine if a resource category is an aerial drone.
 */
export function isDroneCategory(category?: string, name?: string): boolean {
  const cat = (category || '').toUpperCase();
  const n = (name || '').toUpperCase();
  return (
    cat.includes('DRONE') ||
    cat.includes('RECON') ||
    cat.includes('UAV') ||
    n.includes('DRONE') ||
    n.includes('RECON')
  );
}

/**
 * Fetch or compute a tactical route between start and end coordinates.
 *
 * @param start [latitude, longitude] of origin
 * @param end [latitude, longitude] of destination
 * @param category Unit category (e.g., 'FIRE_TRUCK', 'AMBULANCE', 'POLICE', 'DRONE', 'NDRF')
 * @param name Unit name for secondary identification
 */
export async function fetchTacticalRoute(
  start: [number, number],
  end: [number, number],
  category?: string,
  name?: string
): Promise<RouteResult> {
  const [startLat, startLon] = start;
  const [endLat, endLon] = end;

  // Validation
  if (
    isNaN(startLat) ||
    isNaN(startLon) ||
    isNaN(endLat) ||
    isNaN(endLon) ||
    (startLat === 0 && startLon === 0)
  ) {
    return {
      coordinates: [start, end],
      distanceKm: 0,
      durationMin: 0,
      isRoadRoute: false,
      isDrone: false,
    };
  }

  const isDrone = isDroneCategory(category, name);
  const cacheKey = `${startLat.toFixed(5)},${startLon.toFixed(5)}_${endLat.toFixed(5)},${endLon.toFixed(5)}_${isDrone ? 'drone' : 'road'}`;

  // Check cache
  const cached = routeCache.get(cacheKey);
  if (cached) {
    return cached;
  }

  // 1. DRONE RECON: Drones fly directly in a straight line
  if (isDrone) {
    const directKm = calculateHaversineKm(startLat, startLon, endLat, endLon);
    // Average drone speed: ~60 km/h (1 km per minute)
    const etaMin = Math.max(1, Math.round(directKm * 1.0));
    const result: RouteResult = {
      coordinates: [
        [startLat, startLon],
        [endLat, endLon],
      ],
      distanceKm: parseFloat(directKm.toFixed(2)),
      durationMin: etaMin,
      isRoadRoute: false,
      isDrone: true,
    };
    routeCache.set(cacheKey, result);
    return result;
  }

  // 2. GROUND UNITS: Query OSRM Driving Router API
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4500);

    const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${startLon},${startLat};${endLon},${endLat}?overview=full&geometries=geojson`;

    const response = await fetch(osrmUrl, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (
        data.code === 'Ok' &&
        data.routes &&
        data.routes.length > 0 &&
        data.routes[0].geometry?.coordinates
      ) {
        const route = data.routes[0];
        // OSRM returns GeoJSON coordinates as [lon, lat]. Convert to Leaflet [lat, lon]
        const latLngs: [number, number][] = route.geometry.coordinates.map(
          (c: [number, number]) => [c[1], c[0]]
        );

        const distKm = parseFloat((route.distance / 1000).toFixed(2));
        // OSRM duration is in seconds. Convert to minutes.
        const durMin = Math.max(1, Math.round(route.duration / 60));

        const result: RouteResult = {
          coordinates: latLngs,
          distanceKm: distKm,
          durationMin: durMin,
          isRoadRoute: true,
          isDrone: false,
        };

        routeCache.set(cacheKey, result);
        return result;
      }
    }
  } catch (err) {
    // Network timeout or error - fallback gracefully
    console.debug('OSRM routing unavailable, using tactical geometric fallback:', err);
  }

  // 3. FALLBACK: High-accuracy straight-line fallback with road curvature factor
  const straightKm = calculateHaversineKm(startLat, startLon, endLat, endLon);
  const roadAdjustedKm = parseFloat((straightKm * 1.28).toFixed(2)); // Typical urban road winding factor
  // Average emergency response speed: ~42 km/h
  const fallbackEta = Math.max(1, Math.round((roadAdjustedKm / 42) * 60));

  const fallbackResult: RouteResult = {
    coordinates: [
      [startLat, startLon],
      [endLat, endLon],
    ],
    distanceKm: roadAdjustedKm,
    durationMin: fallbackEta,
    isRoadRoute: false,
    isDrone: false,
  };

  routeCache.set(cacheKey, fallbackResult);
  return fallbackResult;
}

/**
 * Clear the route cache when dispatches are updated or reset.
 */
export function clearRouteCache(): void {
  routeCache.clear();
}
