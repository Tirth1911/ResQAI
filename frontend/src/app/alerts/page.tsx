'use client';

import React, { useEffect, useState } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { AlertCard } from '@/components/alerts/AlertCard';
import { IncidentDetailsModal } from '@/components/incidents/IncidentDetailsModal';
import { notificationService } from '@/services/notificationService';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { AlertNotification, Incident, Resource } from '@/types';
import { Bell, CheckCheck, RefreshCw, Filter, Loader2 } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [unreadOnly, setUnreadOnly] = useState(false);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadAlerts();
  });

  const loadAlerts = async () => {
    setIsLoading(true);
    try {
      const [alertList, incList, resList] = await Promise.all([
        notificationService.getNotifications({ limit: 100 }),
        incidentService.getActiveIncidents(),
        resourceService.getResources(),
      ]);
      setAlerts(alertList || []);
      setIncidents(incList.items || []);
      setResources(resList || []);
    } catch (e) {
      console.error('Error fetching alerts:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleMarkRead = async (alert: AlertNotification) => {
    try {
      const id = alert.alert_id || alert.id || alert._id;
      if (id) {
        await notificationService.markAsRead(id);
        setAlerts((prev) =>
          prev.map((a) => (a.alert_id === id || a.id === id || a._id === id ? { ...a, read: true } : a))
        );
      }
    } catch (e) {
      console.error('Error marking alert read:', e);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
    } catch (e) {
      console.error('Error marking all alerts read:', e);
    }
  };

  const handleSelectIncident = (incidentId: string) => {
    incidentService.getIncidentById(incidentId).then((res) => {
      if (res) {
        setSelectedIncident(res);
        setIsDetailsModalOpen(true);
      }
    });
  };

  const filteredAlerts = alerts.filter((a) => {
    const matchesSeverity = severityFilter === 'ALL' || a.severity === severityFilter;
    const matchesUnread = !unreadOnly || !a.read;
    return matchesSeverity && matchesUnread;
  });

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      <TopHeader
        wsStatus={wsStatus}
        wsConnected={wsConnected}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length}
        criticalIncidentsCount={criticalIncidents.length}
        availableResourcesCount={availableCount}
        unreadAlertsCount={unreadAlerts.length}
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Header Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white">
                <Bell className="h-4 w-4" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Crisis Alert & Escalation Feed
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Automated incident escalations, SLA delay alerts, and real-time resource shortages
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleMarkAllRead}
              disabled={unreadAlerts.length === 0}
              className="flex items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-bold text-red-700 hover:bg-red-100 transition-colors disabled:opacity-40"
            >
              <CheckCheck className="h-4 w-4" />
              <span>Mark All Read</span>
            </button>

            <button
              type="button"
              onClick={loadAlerts}
              className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
                  severityFilter === sev
                    ? 'bg-slate-900 text-white shadow-2xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <label className="flex items-center gap-2 text-slate-700 font-semibold cursor-pointer select-none">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="rounded border-slate-300 text-red-600 focus:ring-red-500"
            />
            <span>Unread Only ({unreadAlerts.length})</span>
          </label>
        </div>

        {/* Alerts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {isLoading ? (
            <div className="col-span-full flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 text-xs font-semibold">
              <Loader2 className="h-5 w-5 animate-spin text-red-600 mr-2" />
              <span>Scanning alert telemetry records...</span>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="col-span-full flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 text-xs font-semibold">
              No alerts match the selected filter parameters.
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <AlertCard
                key={alert.alert_id || alert.id || alert._id}
                alert={alert}
                onMarkRead={handleMarkRead}
                onSelectIncident={handleSelectIncident}
              />
            ))
          )}
        </div>
      </main>

      <IncidentDetailsModal
        incident={selectedIncident}
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        onIncidentUpdated={() => loadAlerts()}
      />
    </div>
  );
}
