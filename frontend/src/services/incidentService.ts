import { fetchApi } from '@/lib/api';
import {
  Incident,
  IncidentPaginatedResponse,
  DuplicateCheckResponse,
  AIAnalysis,
  IncidentStats,
} from '@/types';

export interface CreateIncidentPayload {
  title: string;
  description: string;
  source?: string;
  type?: string;
  severity?: string;
  priority?: string;
  location: {
    latitude: number;
    longitude: number;
    address?: string;
  };
  address?: string;
  reported_at?: string;
  duplicate_of?: string;
}

export const incidentService = {
  async getIncidents(params?: {
    status?: string;
    type?: string;
    severity?: string;
    priority?: string;
    source?: string;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<IncidentPaginatedResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.type) query.append('type', params.type);
    if (params?.severity) query.append('severity', params.severity);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.source) query.append('source', params.source);
    if (params?.search) query.append('search', params.search);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchApi<IncidentPaginatedResponse>(`/incidents${qs}`);
  },

  async getActiveIncidents(limit: number = 50): Promise<IncidentPaginatedResponse> {
    return this.getIncidents({ limit });
  },

  async getCriticalIncidents(limit: number = 20): Promise<IncidentPaginatedResponse> {
    return this.getIncidents({ severity: 'CRITICAL', limit });
  },

  async getIncidentById(incidentId: string): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/${incidentId}`);
  },

  async createIncident(
    payload: CreateIncidentPayload,
    autoDedup: boolean = true
  ): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/?auto_dedup=${autoDedup}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateIncident(
    incidentId: string,
    updates: Partial<Incident>
  ): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/${incidentId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async verifyIncident(
    incidentId: string,
    actor: string = 'Command Officer',
    notes?: string
  ): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/${incidentId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ actor, notes }),
    });
  },

  async resolveIncident(
    incidentId: string,
    actor: string = 'Command Officer',
    notes?: string
  ): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/${incidentId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ actor, notes }),
    });
  },

  async closeIncident(
    incidentId: string,
    actor: string = 'Command Officer',
    notes?: string
  ): Promise<Incident> {
    return fetchApi<Incident>(`/incidents/${incidentId}/close`, {
      method: 'POST',
      body: JSON.stringify({ actor, notes }),
    });
  },

  async analyzeIncident(
    incidentId: string,
    saveToDb: boolean = true
  ): Promise<{ incident_id: string; ai_analysis: AIAnalysis; saved_to_database: boolean }> {
    return fetchApi<{ incident_id: string; ai_analysis: AIAnalysis; saved_to_database: boolean }>(
      `/incidents/${incidentId}/analyze?save_to_database=${saveToDb}`,
      { method: 'POST' }
    );
  },

  async checkDuplicate(payload: {
    title: string;
    description: string;
    location: { latitude: number; longitude: number };
    reported_at?: string;
  }): Promise<DuplicateCheckResponse> {
    return fetchApi<DuplicateCheckResponse>(`/incidents/check-duplicate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getRelatedIncidents(incidentId: string): Promise<any> {
    return fetchApi<any>(`/incidents/${incidentId}/related`);
  },

  async assignResource(
    incidentId: string,
    resourceId: string,
    actor: string = 'Command Dispatcher',
    notes?: string
  ): Promise<any> {
    return fetchApi<any>(`/incidents/${incidentId}/assign-resource`, {
      method: 'POST',
      body: JSON.stringify({ resource_id: resourceId, actor, notes }),
    });
  },

  async getStats(): Promise<IncidentStats> {
    return fetchApi<IncidentStats>(`/incidents/stats`);
  },

  async getBriefing(): Promise<{
    timestamp: string;
    total_active_incidents: number;
    severity_counts: Record<string, number>;
    available_resources: number;
    top_priority_incidents: any[];
    briefing_narrative: string;
  }> {
    return fetchApi('/briefing');
  },
};

