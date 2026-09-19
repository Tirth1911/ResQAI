'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { DynamicMapView } from '@/components/Map/DynamicMapView';
import { RightIncidentPanel } from '@/components/incidents/RightIncidentPanel';
import { DashboardCard } from '@/components/common/DashboardCard';
import { AnalyticsChart } from '@/components/Analytics/AnalyticsChart';
import { IncidentDetailsModal } from '@/components/incidents/IncidentDetailsModal';
import { AssignResourceModal } from '@/components/resources/AssignResourceModal';
import { ReportIncidentModal } from '@/components/ReportModal/ReportIncidentModal';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { notificationService } from '@/services/notificationService';
import { analyticsService, AnalyticsOverview } from '@/services/analyticsService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, AlertNotification, WebSocketEventPayload } from '@/types';
import {
  Flame,
  AlertOctagon,
  Truck,
  Layers,
  Clock,
  CheckCircle,
  RefreshCw,
  PlusCircle,
  BarChart2
} from 'lucide-react';

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [analyticsOverview, setAnalyticsOverview] = useState<AnalyticsOverview | null>(null);
  const [typeChartData, setTypeChartData] = useState<Array<{ name: string; count: number }>>([]);
  const [severityChartData, setSeverityChartData] = useState<Array<{ name: string; count: number }>>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modals & Selected states
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [dispatchIncident, setDispatchIncident] = useState<Incident | null>(null);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Real-time WebSocket Event Handler
  const handleWebSocketEvent = useCallback((payload: WebSocketEventPayload) => {
    if (
      payload.event === 'INCIDENT_CREATED' ||
      payload.event === 'INCIDENT_UPDATED' ||
      payload.event === 'INCIDENT_VERIFIED' ||
      payload.event === 'INCIDENT_RESOLVED' ||
      payload.event === 'INCIDENT_CLOSED' ||
      payload.event === 'INCIDENT_DUPLICATED' ||
      payload.event === 'INCIDENT_DUPLICATE_MERGED' ||
      payload.event === 'INCIDENT_CLASSIFIED' ||
      payload.event === 'INCIDENT_ESCALATED'
    ) {
      loadDashboardData(false);
    } else if (
      payload.event === 'RESOURCE_CREATED' ||
      payload.event === 'RESOURCE_UPDATED' ||
      payload.event === 'RESOURCE_ASSIGNED' ||
      payload.event === 'RESOURCE_RELEASED' ||
      payload.event === 'RESOURCE_SHORTAGE'
    ) {
      loadResources();
      loadAnalyticsOverview();
    } else if (
      payload.event === 'NOTIFICATION_CREATED' ||
      payload.event === 'ALERT_TRIGGERED' ||
      payload.event === 'NOTIFICATION_UPDATED' ||
      payload.event === 'NOTIFICATIONS_ALL_READ'
    ) {
      loadAlerts();
    }
  }, []);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(handleWebSocketEvent);

  // Initial Data Fetching
  const loadDashboardData = async (showLoadingState = true) => {
    if (showLoadingState) setIsLoading(true);
    try {
      await Promise.all([
        loadIncidents(),
        loadResources(),
        loadAlerts(),
        loadAnalyticsOverview(),
        loadChartData(),
      ]);
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    } finally {
      if (showLoadingState) setIsLoading(false);
    }
  };

  const loadIncidents = async () => {
    try {
      const res = await incidentService.getIncidents({ limit: 100 });
      const items = res.items || [];
      setIncidents(items);
      // Auto-select first active incident if none selected
      if (!selectedIncident && items.length > 0) {
        const active = items.find((i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED') || items[0];
        setSelectedIncident(active);
      }
    } catch (e) {
      console.error('Error fetching incidents:', e);
    }
  };

  const loadResources = async () => {
    try {
      const res = await resourceService.getResources();
      setResources(res || []);
    } catch (e) {
      console.error('Error fetching resources:', e);
    }
  };

  const loadAlerts = async () => {
    try {
      const res = await notificationService.getNotifications({ limit: 50 });
      setAlerts(res || []);
    } catch (e) {
      console.error('Error fetching alerts:', e);
    }
  };

  const loadAnalyticsOverview = async () => {
    try {
      const res = await analyticsService.getOverview();
      setAnalyticsOverview(res);
    } catch (e) {
      console.error('Error fetching analytics overview:', e);
    }
  };

  const loadChartData = async () => {
    try {
      const [byType, bySev] = await Promise.all([
        analyticsService.getIncidentsByType(),
        analyticsService.getIncidentsBySeverity(),
      ]);

      if (byType?.data) {
        setTypeChartData(
          byType.data.map((item) => ({
            name: item.name || item.type,
            count: item.count,
          }))
        );
      }

      if (bySev?.data) {
        setSeverityChartData(
          bySev.data.map((item) => ({
            name: item.severity,
            count: item.count,
          }))
        );
      }
    } catch (e) {
      console.error('Error fetching chart analytics:', e);
    }
  };

  useEffect(() => {
    loadDashboardData(true);
  }, []);

  const handleOpenDispatch = (incident: Incident) => {
    setDispatchIncident(incident);
    setIsDispatchModalOpen(true);
  };

  // Metrics
  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableResources = resources.filter((r) => r.status === 'AVAILABLE');
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      {/* TOP: Navigation Header */}
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length}
        criticalIncidentsCount={criticalIncidents.length}
        availableResourcesCount={availableResources.length}
        unreadAlertsCount={unreadAlerts.length}
        onOpenNewIncidentModal={() => setIsReportModalOpen(true)}
      />

      {/* Main Command Center Body */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Metric Overview Bar */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <DashboardCard
            title="Active Incidents"
            value={activeIncidents.length}
            subtitle="Under tactical management"
            icon={<Flame className="h-4 w-4" />}
            variant={activeIncidents.length > 0 ? 'warning' : 'default'}
          />

          <DashboardCard
            title="Critical Emergencies"
            value={criticalIncidents.length}
            subtitle="P1 priority queue"
            icon={<AlertOctagon className="h-4 w-4" />}
            variant={criticalIncidents.length > 0 ? 'critical' : 'default'}
          />

          <DashboardCard
            title="Available Units"
            value={availableResources.length}
            subtitle={`Out of ${resources.length} total units`}
            icon={<Truck className="h-4 w-4" />}
            variant="info"
          />

          <DashboardCard
            title="Duplicates Merged"
            value={analyticsOverview?.duplicate_reports_merged ?? 0}
            subtitle="Spatiotemporal AI linked"
            icon={<Layers className="h-4 w-4" />}
            variant="default"
          />

          <DashboardCard
            title="Avg Response Time"
            value={`${analyticsOverview?.average_response_time ?? 4.8}m`}
            subtitle="Target SLA < 8.0 min"
            icon={<Clock className="h-4 w-4" />}
            variant="success"
          />

          <DashboardCard
            title="Resolved Cases"
            value={analyticsOverview?.resolved_incidents ?? incidents.filter((i) => i.status === 'RESOLVED').length}
            subtitle="Successfully closed"
            icon={<CheckCircle className="h-4 w-4" />}
            variant="default"
          />
        </div>

        {/* MAP & RIGHT INCIDENT PANEL (Command Center Split View) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[580px]">
          {/* LEFT / CENTER: Interactive Emergency Map (8 cols) */}
          <div className="lg:col-span-8 h-full flex flex-col">
            <DynamicMapView
              incidents={incidents}
              resources={resources}
              selectedIncident={selectedIncident}
              onSelectIncident={(inc) => {
                setSelectedIncident(inc);
              }}
              onAssignResource={(res) => {
                if (selectedIncident) {
                  handleOpenDispatch(selectedIncident);
                } else if (activeIncidents.length > 0) {
                  handleOpenDispatch(activeIncidents[0]);
                }
              }}
              className="h-full"
            />
          </div>

          {/* RIGHT: Selected Incident & AI Dispatch Panel (4 cols) */}
          <div className="lg:col-span-4 h-full flex flex-col">
            <RightIncidentPanel
              incident={selectedIncident}
              resources={resources}
              onDispatch={(inc) => handleOpenDispatch(inc)}
            />
          </div>
        </div>

        {/* BOTTOM: Analytics & Resource Fleet Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnalyticsChart
            title="Incidents By Category"
            type="bar"
            data={typeChartData}
            subtitle="Distribution of incoming crises by category"
            colors={['#dc2626', '#ea580c', '#d97706', '#2563eb', '#059669', '#7c3aed']}
          />

          <AnalyticsChart
            title="Severity Matrix"
            type="donut"
            data={severityChartData}
            subtitle="Triage breakdown (CRITICAL / HIGH / MED / LOW)"
            colors={['#dc2626', '#ea580c', '#d97706', '#059669']}
          />

          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2 border-b border-slate-100 pb-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Resource Fleet Utilization
                </h4>
                <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                  {analyticsOverview?.resource_utilization || '35% Deployed'}
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-normal">
                Real-time operational status across ready ambulances, fire engines, police units, and specialized response fleets.
              </p>
            </div>

            <div className="space-y-3 mt-4">
              <div>
                <div className="flex justify-between text-xs text-slate-600 mb-1">
                  <span>Available Response Fleet</span>
                  <span className="text-emerald-700 font-bold">
                    {availableResources.length} / {resources.length} Ready
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full bg-emerald-600 transition-all duration-500 rounded-full"
                    style={{
                      width: `${
                        resources.length > 0
                          ? (availableResources.length / resources.length) * 100
                          : 0
                      }%`,
                    }}
                  />
                </div>
              </div>

              <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-600">Adaptive Deduplication</span>
                <span className="text-red-700 font-bold bg-red-50 px-2 py-0.5 rounded border border-red-200">
                  {analyticsOverview?.duplicate_reports_merged ?? 0} Merged
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Modals & Dialogs */}
      <IncidentDetailsModal
        incident={selectedIncident}
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        onOpenDispatch={(inc) => {
          setIsDetailsModalOpen(false);
          handleOpenDispatch(inc);
        }}
        onIncidentUpdated={(updated) => {
          setSelectedIncident(updated);
          setIncidents((prev) =>
            prev.map((i) => (i.incident_id === updated.incident_id ? updated : i))
          );
        }}
      />

      <AssignResourceModal
        incident={dispatchIncident}
        isOpen={isDispatchModalOpen}
        onClose={() => setIsDispatchModalOpen(false)}
        onAssigned={(updatedInc, assignedRes) => {
          loadDashboardData(false);
        }}
      />

      <ReportIncidentModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onCreated={(newInc) => {
          loadDashboardData(false);
          setSelectedIncident(newInc);
        }}
      />
    </div>
  );
}
