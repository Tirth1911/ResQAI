export type IncidentType =
  | 'fire'
  | 'flood'
  | 'road_accident'
  | 'medical_emergency'
  | 'industrial_hazard'
  | 'building_collapse'
  | 'gas_leak'
  | 'earthquake'
  | 'other';

export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentPriority = 'P1' | 'P2' | 'P3' | 'P4';
export type IncidentStatus =
  | 'REPORTED'
  | 'VERIFIED'
  | 'DISPATCHED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED';

export type IncidentSource =
  | 'citizen'
  | 'call_center'
  | 'iot'
  | 'field_team'
  | 'hospital'
  | 'government'
  | 'simulation';

export type ResourceCategory =
  | 'AMBULANCE'
  | 'FIRE_TRUCK'
  | 'POLICE'
  | 'RESCUE_BOAT'
  | 'HAZMAT'
  | 'HEAVY_RESCUE'
  | 'DRONE'
  | 'HELICOPTER'
  | 'OTHER';

export type ResourceStatus =
  | 'AVAILABLE'
  | 'BUSY'
  | 'EN_ROUTE'
  | 'OFFLINE'
  | 'MAINTENANCE';

export type HospitalStatus = 'OPEN' | 'LIMITED' | 'CLOSED';

export interface GeoPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
  address?: string;
}

export interface TimelineEvent {
  event: string;
  timestamp: string;
  actor: string;
  notes?: string;
}

export interface AIAnalysis {
  incident_type: IncidentType;
  severity: IncidentSeverity;
  priority: IncidentPriority;
  confidence: number;
  people_at_risk: number;
  recommended_resources: string[];
  immediate_actions: string[];
  summary: string;
  reasoning: string;
  provider?: string;
  model?: string;
}

export interface Incident {
  _id?: string;
  id?: string;
  incident_id: string;
  source: IncidentSource;
  type: IncidentType;
  title: string;
  description: string;
  severity: IncidentSeverity;
  priority: IncidentPriority;
  status: IncidentStatus;
  location: GeoPoint;
  address: string;
  reported_at: string;
  updated_at: string;
  ai_analysis: AIAnalysis | Record<string, any>;
  ai_triage?: any;
  duplicate_of?: string | null;
  duplicate_count?: number;
  duplicate_reports?: Array<{
    title: string;
    description: string;
    reported_at: string;
    source: string;
    similarity_score?: number;
  }>;
  confidence: number;
  assigned_resources: string[];
  timeline: TimelineEvent[];
  distance_km?: number;
}

export interface IncidentPaginatedResponse {
  items: Incident[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface Resource {
  _id?: string;
  id?: string;
  resource_id: string;
  name: string;
  category: ResourceCategory;
  type?: string;
  kind?: string;
  capabilities: string[];
  status: ResourceStatus;
  location: GeoPoint;
  capacity: number;
  current_incident_id?: string | null;
  assigned_incident_id?: string | null;
  updated_at: string;
  distance_km?: number;
}

export interface ResourceRecommendation {
  resource_id: string;
  name: string;
  resource_name?: string;
  category: string;
  resource_type?: string;
  distance_km: number;
  capability_match: number;
  readiness: number;
  score: number;
  reason: string;
  capabilities: string[];
}

export interface IncidentRecommendationsResponse {
  incident_id: string;
  incident_type: string;
  severity: string;
  required_capabilities: string[];
  recommendations: ResourceRecommendation[];
}

export interface Hospital {
  _id?: string;
  id?: string;
  hospital_id: string;
  name: string;
  location: GeoPoint;
  address: string;
  total_beds: number;
  available_beds: number;
  icu_available: number;
  has_trauma_center: boolean;
  has_burn_unit: boolean;
  status: HospitalStatus;
  contact_phone: string;
  distance_km?: number;
}

export interface DuplicateCandidate {
  incident_id: string;
  title: string;
  description: string;
  distance_km: number;
  time_difference_minutes: number;
  text_similarity: number;
  duplicate_confidence: number;
  reason: string;
}

export interface DuplicateCheckResponse {
  is_duplicate: boolean;
  matched_incident_id?: string | null;
  distance_km?: number | null;
  time_diff_minutes?: number | null;
  text_similarity?: number | null;
  duplicate_confidence: number;
  reasoning: string;
  candidate_matches: DuplicateCandidate[];
}

export interface IncidentStats {
  total_incidents: number;
  active_incidents: number;
  critical_incidents: number;
  resolved_incidents: number;
  closed_incidents: number;
  incidents_by_type: Record<string, number>;
  incidents_by_severity: Record<string, number>;
  incidents_by_priority: Record<string, number>;
  incidents_by_status: Record<string, number>;
  incidents_by_source: Record<string, number>;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  database: {
    type: string;
    connected: boolean;
    database_name: string;
  };
  environment: string;
}

export interface AlertNotification {
  _id?: string;
  id?: string;
  alert_id: string;
  type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  incident_id?: string;
  resource_id?: string;
  message: string;
  created_at: string;
  read: boolean;
  metadata?: Record<string, any>;
}

export interface WebSocketEventPayload<T = any> {
  event:
    | 'INCIDENT_CREATED'
    | 'INCIDENT_UPDATED'
    | 'INCIDENT_VERIFIED'
    | 'INCIDENT_RESOLVED'
    | 'INCIDENT_CLOSED'
    | 'INCIDENT_DUPLICATED'
    | 'INCIDENT_DUPLICATE_MERGED'
    | 'INCIDENT_CLASSIFIED'
    | 'INCIDENT_ESCALATED'
    | 'RESOURCE_CREATED'
    | 'RESOURCE_UPDATED'
    | 'RESOURCE_ASSIGNED'
    | 'RESOURCE_RELEASED'
    | 'RESOURCE_SHORTAGE'
    | 'ALERT_TRIGGERED'
    | 'NOTIFICATION_CREATED'
    | 'NOTIFICATION_UPDATED'
    | 'NOTIFICATIONS_ALL_READ'
    | 'CONNECTED'
    | 'PONG';
  data?: T;
  incident_id?: string;
  resource_id?: string;
  new_status?: string;
  timestamp?: string;
  merged_report?: {
    title: string;
    description: string;
    similarity_score?: number;
  };
}

export interface SimulationScenario {
  id: string;
  title: string;
  type: IncidentType | string;
  severity: IncidentSeverity | string;
  priority: IncidentPriority | string;
  address: string;
  description: string;
}

export interface SimulationLog {
  id: string;
  timestamp: string;
  event_type: string;
  stage: string;
  title: string;
  details: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | string;
  level?: string;
  message?: string;
  scenario_id?: string;
  metadata?: Record<string, any>;
}

export interface SimulationStatus {
  is_running: boolean;
  current_scenario_id: string | null;
  current_scenario_title: string | null;
  current_stage: string;
  current_step_index: number;
  current_step?: number;
  total_steps: number;
  progress_percentage: number;
  elapsed_seconds: number;
  speed_multiplier: number;
  events_log: SimulationLog[];
  logs?: SimulationLog[];
  created_incident_ids: string[];
  assigned_resource_ids: string[];
  available_scenarios: SimulationScenario[];
}

export interface StartSimulationPayload {
  scenario_id?: string | null;
  speed_multiplier?: number;
  auto_play_all?: boolean;
  step_delay_seconds?: number;
}

export type UserRole = 'ADMIN' | 'DISPATCHER' | 'FIELD_TEAM' | 'HOSPITAL' | 'VIEWER';

export interface User {
  id?: string;
  user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  phone?: string;
  is_active?: boolean;
  created_at?: string;
  last_login?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface RoleMeta {
  role: UserRole;
  title: string;
  badge_color: string;
  description: string;
  default_email: string;
  permissions: string[];
}



