import { fetchApi } from '@/lib/api';
import { AlertNotification } from '@/types';

export const notificationService = {
  async getNotifications(params?: {
    unread_only?: boolean;
    severity?: string;
    type?: string;
    limit?: number;
  }): Promise<AlertNotification[]> {
    const query = new URLSearchParams();
    if (params?.unread_only) query.append('unread_only', 'true');
    if (params?.severity) query.append('severity', params.severity);
    if (params?.type) query.append('type', params.type);
    if (params?.limit) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchApi<AlertNotification[]>(`/notifications${qs}`);
  },

  async markAsRead(id: string): Promise<AlertNotification> {
    return fetchApi<AlertNotification>(`/notifications/${id}/read`, {
      method: 'PATCH',
    });
  },

  async markAllAsRead(): Promise<{ status: string; marked_read_count: number }> {
    return fetchApi<{ status: string; marked_read_count: number }>(
      '/notifications/mark-all-read',
      {
        method: 'POST',
      }
    );
  },

  async deleteNotification(id: string): Promise<{ status: string; id: string }> {
    return fetchApi<{ status: string; id: string }>(`/notifications/${id}`, {
      method: 'DELETE',
    });
  },
};
