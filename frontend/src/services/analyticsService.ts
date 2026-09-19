import { fetchApi } from '@/lib/api';
import { SystemHealth, IncidentStats } from '@/types';

export interface AnalyticsOverview {
  total_incidents: number;
  active_incidents: number;
  critical_incidents: number;
  resolved_incidents: number;
  average_response_time: number;
  average_response_time_unit: string;
  resources_available: number;
  resources_busy: number;
  resource_utilization: string;
  resource_utilization_rate: number;
  duplicate_reports_merged: number;
  total_calls_handled: number;
  resolution_rate_percent?: number;
}

export const analyticsService = {
  async getHealth(): Promise<SystemHealth> {
    return fetchApi<SystemHealth>('/health');
  },

  async getIncidentStats(): Promise<IncidentStats> {
    return fetchApi<IncidentStats>('/incidents/stats');
  },

  async getOverview(): Promise<AnalyticsOverview> {
    return fetchApi<AnalyticsOverview>('/analytics/overview');
  },

  async getIncidentsByType(): Promise<{ total_categorized: number; data: Array<{ type: string; name: string; count: number; percentage: number }> }> {
    return fetchApi('/analytics/incidents-by-type');
  },

  async getIncidentsBySeverity(): Promise<{ total_assessed: number; data: Array<{ severity: string; count: number; percentage: number }> }> {
    return fetchApi('/analytics/incidents-by-severity');
  },

  async getIncidentsByRegion(): Promise<{ total_regions: number; data: Array<{ region: string; incident_count: number; critical_count: number; active_count: number }> }> {
    return fetchApi('/analytics/incidents-by-region');
  },

  async getResponseTimes(): Promise<any> {
    return fetchApi('/analytics/response-times');
  },

  async getResourceUtilization(): Promise<any> {
    return fetchApi('/analytics/resource-utilization');
  },

  async getTrends(days: number = 7): Promise<{ period_days: number; data: Array<{ date: string; total_incidents: number; critical: number; high: number; resolved: number }> }> {
    return fetchApi(`/analytics/trends?days=${days}`);
  },

  async getHotspots(limit: number = 10): Promise<{ total_hotspots: number; data: Array<{ location: string; incident_count: number; critical_count: number; active_count: number; primary_type: string; last_reported_at?: string }> }> {
    return fetchApi(`/analytics/hotspots?limit=${limit}`);
  },

  async triggerSimulation(scenarioIndex: number = 0, duplicate: boolean = false): Promise<any> {
    return fetchApi<any>(
      `/simulation/trigger?scenario_index=${scenarioIndex}&duplicate_simulation=${duplicate}`,
      {
        method: 'POST',
      }
    );
  },
};

