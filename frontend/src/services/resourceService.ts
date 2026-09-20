import { fetchApi } from '@/lib/api';
import { Resource, IncidentRecommendationsResponse } from '@/types';

export interface CreateResourcePayload {
  name: string;
  category: string;
  capabilities: string[];
  status?: string;
  location: {
    latitude: number;
    longitude: number;
    address?: string;
  };
  capacity?: number;
}

export const resourceService = {
  async getResources(params?: {
    status?: string;
    category?: string;
    limit?: number;
  }): Promise<Resource[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.category) query.append('category', params.category);
    if (params?.limit) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    const raw = await fetchApi<any>(`/resources${qs}`);
    if (Array.isArray(raw)) return raw;
    if (raw && Array.isArray(raw.items)) return raw.items;
    return raw || [];
  },

  async getResourceById(resourceId: string): Promise<Resource> {
    return fetchApi<Resource>(`/resources/${resourceId}`);
  },

  async createResource(payload: CreateResourcePayload): Promise<Resource> {
    return fetchApi<Resource>(`/resources/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateResource(
    resourceId: string,
    updates: Partial<Resource>
  ): Promise<Resource> {
    return fetchApi<Resource>(`/resources/${resourceId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async updateResourceStatus(
    resourceId: string,
    status: string
  ): Promise<Resource> {
    return this.updateResource(resourceId, { status: status as any });
  },


  async getRecommendations(
    incidentId: string,
    topK: number = 5
  ): Promise<IncidentRecommendationsResponse> {
    return fetchApi<IncidentRecommendationsResponse>(
      `/resources/recommend/${incidentId}?top_k=${topK}`
    );
  },

  async releaseResource(
    resourceId: string,
    actor: string = 'Command Officer'
  ): Promise<any> {
    return fetchApi<any>(
      `/resources/${resourceId}/release?actor=${encodeURIComponent(actor)}`,
      {
        method: 'POST',
      }
    );
  },

  async getNearbyResources(
    longitude: number,
    latitude: number,
    category?: string,
    status: string = 'AVAILABLE',
    maxDistanceMeters: number = 25000,
    limit: number = 10
  ): Promise<Resource[]> {
    const query = new URLSearchParams({
      longitude: longitude.toString(),
      latitude: latitude.toString(),
      status,
      max_distance_meters: maxDistanceMeters.toString(),
      limit: limit.toString(),
    });
    if (category) query.append('category', category);

    return fetchApi<Resource[]>(`/resources/nearby?${query.toString()}`);
  },
};
