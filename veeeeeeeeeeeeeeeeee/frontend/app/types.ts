export type IncidentType = 'fire' | 'flood' | 'accident' | 'industrial' | 'medical' | 'collapse' | 'other';
export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'open' | 'triaged' | 'dispatched' | 'in_progress' | 'resolved' | 'closed';
export type ReportSource = 'citizen' | 'hotline' | 'iot_sensor' | 'field_officer';

export type ResourceKind = 'fire_truck' | 'ambulance' | 'police_van' | 'rescue_boat' | 'hazmat_unit' | 'ndrf_team' | 'drone';
export type ResourceStatus = 'available' | 'dispatched' | 'on_scene' | 'returning' | 'maintenance';

export type AssignmentStatus = 'assigned' | 'en_route' | 'on_scene' | 'completed' | 'cancelled';
export type AlertLevel = 'critical' | 'warning' | 'info';

export interface ReportItem {
  id: string;
  source: ReportSource;
  reporter?: string;
  raw_text: string;
  lat: float;
  lng: float;
  reported_at: string;
}

type float = number;

export interface Assignment {
  id: string;
  incident_id: string;
  resource_id: string;
  resource_name?: string;
  resource_kind?: ResourceKind;
  status: AssignmentStatus;
  score: number;
  distance_km: number;
  eta_min: number;
  assigned_at: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  type: IncidentType;
  severity: IncidentSeverity;
  priority: number;
  status: IncidentStatus;
  lat: number;
  lng: number;
  address?: string;
  source: ReportSource;
  report_count: number;
  reports: ReportItem[];
  ai_confidence?: number;
  ai_reasoning?: string;
  classified_by: 'ai' | 'rules';
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assignments?: Assignment[];
}

export interface Resource {
  id: string;
  name: string;
  kind: ResourceKind;
  status: ResourceStatus;
  lat: number;
  lng: number;
  capacity: number;
  capabilities: IncidentType[];
  station: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  type: 'delayed_response' | 'resource_shortage' | 'severity_escalation' | 'system';
  level: AlertLevel;
  title: string;
  description: string;
  incident_id?: string;
  resource_id?: string;
  created_at: string;
  resolved: boolean;
}

export interface DispatchRecommendation {
  resource: Resource;
  score: number;
  distance_km: number;
  eta_min: number;
  match_reasons: string[];
}
