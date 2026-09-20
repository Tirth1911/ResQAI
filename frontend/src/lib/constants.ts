export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    const proto = window.location.protocol;
    const host = window.location.hostname;
    // On Vercel production deployment without localhost port 8000
    if (
      !window.location.port ||
      window.location.port === '80' ||
      window.location.port === '443' ||
      host.includes('vercel.app')
    ) {
      return '/api/v1';
    }
    return `${proto}//${host}:8000/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
}

export function getWsBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== 'undefined') {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    if (
      !window.location.port ||
      window.location.port === '80' ||
      window.location.port === '443' ||
      host.includes('vercel.app')
    ) {
      return `${wsProto}//${window.location.host}/ws/dashboard`;
    }
    return `${wsProto}//${host}:8000/ws/dashboard`;
  }
  return 'ws://localhost:8000/ws/dashboard';
}

export const API_BASE_URL = getApiBaseUrl();
export const WS_BASE_URL = getWsBaseUrl();

export const INCIDENT_TYPES = [
  'Fire',
  'Flood',
  'Road Accident',
  'Medical Emergency',
  'Industrial Hazard',
  'Building Collapse',
  'Gas Leak',
  'Earthquake',
  'Other',
] as const;

export const INCIDENT_SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;

export const INCIDENT_PRIORITIES = ['P1', 'P2', 'P3', 'P4'] as const;

export const RESOURCE_TYPES = [
  'Ambulance',
  'Fire Truck',
  'Police Patrol',
  'Rescue Boat',
  'Hazmat Team',
  'Heavy Rescue / Crane',
  'Drone Recon',
] as const;
