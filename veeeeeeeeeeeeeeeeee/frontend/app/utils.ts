import { Incident, Resource, DispatchRecommendation } from './types';

// Haversine formula to calculate distance in km between two lat/lng points
export function calculateDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) *
      Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return parseFloat((R * c).toFixed(2));
}

// Estimate ETA in minutes assuming average emergency vehicle speed of 35 km/h in city traffic
export function estimateEtaMin(distanceKm: number): number {
  const speedKmH = 35;
  const timeHours = distanceKm / speedKmH;
  return Math.max(2, Math.round(timeHours * 60 + 2)); // Add 2 min dispatch prep buffer
}

// Calculate multi-factor dispatch recommendation score (0 - 100)
export function getDispatchRecommendations(incident: Incident, resources: Resource[]): DispatchRecommendation[] {
  const availableResources = resources.filter(r => r.status === 'available');

  const recommendations: DispatchRecommendation[] = availableResources.map(resource => {
    const distanceKm = calculateDistanceKm(incident.lat, incident.lng, resource.lat, resource.lng);
    const etaMin = estimateEtaMin(distanceKm);
    const matchReasons: string[] = [];

    // 1. Distance score (max 40 pts): 40 * exp(-distance / 8.0)
    const distanceScore = 40 * Math.exp(-distanceKm / 8.0);

    // 2. Capability match score (max 40 pts)
    let capabilityScore = 0;
    if (resource.capabilities.includes(incident.type)) {
      capabilityScore = 40;
      matchReasons.push(`Direct capability match for ${incident.type.toUpperCase()}`);
    } else {
      capabilityScore = 15; // Partial cross-functional capability
      matchReasons.push(`General emergency response asset`);
    }

    // 3. Capacity score (max 20 pts)
    const capacityScore = Math.min(20, resource.capacity * 3.5);
    matchReasons.push(`${resource.capacity} responder capacity`);

    if (distanceKm < 3.0) {
      matchReasons.push(`Proximity advantage (< 3km)`);
    }

    const totalScore = parseFloat((distanceScore + capabilityScore + capacityScore).toFixed(1));

    return {
      resource,
      score: Math.min(99.9, totalScore),
      distance_km: distanceKm,
      eta_min: etaMin,
      match_reasons: matchReasons
    };
  });

  // Sort descending by score
  return recommendations.sort((a, b) => b.score - a.score);
}

// Spatio-temporal deduplication check (2km radius, 30 min window)
export function checkDuplicateReport(newLat: number, newLng: number, incidents: Incident[]): Incident | null {
  for (const inc of incidents) {
    if (inc.status === 'resolved' || inc.status === 'closed') continue;
    const dist = calculateDistanceKm(newLat, newLng, inc.lat, inc.lng);
    if (dist <= 2.5) {
      return inc;
    }
  }
  return null;
}
