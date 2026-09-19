import { fetchApi } from '@/lib/api';
import { Hospital } from '@/types';

export const hospitalService = {
  async getHospitals(params?: {
    status?: string;
    near_longitude?: number;
    near_latitude?: number;
    max_distance_meters?: number;
    limit?: number;
  }): Promise<Hospital[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.near_longitude !== undefined)
      query.append('near_longitude', params.near_longitude.toString());
    if (params?.near_latitude !== undefined)
      query.append('near_latitude', params.near_latitude.toString());
    if (params?.max_distance_meters)
      query.append('max_distance_meters', params.max_distance_meters.toString());
    if (params?.limit) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchApi<Hospital[]>(`/hospitals${qs}`);
  },
};
