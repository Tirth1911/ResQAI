'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { DynamicMapView } from '@/components/Map/DynamicMapView';
import { IncidentQueue } from '@/components/IncidentQueue/IncidentQueue';
import { RightCommandPanel } from '@/components/dashboard/RightCommandPanel';
import { AssignResourceModal } from '@/components/resources/AssignResourceModal';
import { ReportIncidentModal } from '@/components/ReportModal/ReportIncidentModal';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { hospitalService } from '@/services/hospitalService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, Hospital, AlertNotification, WebSocketEventPayload } from '@/types';

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Modals state
  const [dispatchIncident, setDispatchIncident] = useState<Incident | null>(null);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Real-time WebSocket Event Handler
  const handleWebSocketEvent = useCallback((payload: WebSocketEventPayload) => {
    const ev = payload.event;
    if (
      ev === 'INCIDENT_CREATED' ||
      ev === 'INCIDENT_UPDATED' ||
      ev === 'INCIDENT_VERIFIED' ||
      ev === 'INCIDENT_RESOLVED' ||
      ev === 'INCIDENT_CLOSED' ||
      ev === 'INCIDENT_DUPLICATED' ||
      ev === 'INCIDENT_DUPLICATE_MERGED' ||
      ev === 'INCIDENT_CLASSIFIED' ||
      ev === 'INCIDENT_ESCALATED'
    ) {
      loadIncidents();
    } else if (
      ev === 'RESOURCE_CREATED' ||
      ev === 'RESOURCE_UPDATED' ||
      ev === 'RESOURCE_ASSIGNED' ||
      ev === 'RESOURCE_RELEASED' ||
      ev === 'RESOURCE_SHORTAGE'
    ) {
      loadResources();
    } else if (
      ev === 'NOTIFICATION_CREATED' ||
      ev === 'ALERT_TRIGGERED' ||
      ev === 'NOTIFICATION_UPDATED' ||
      ev === 'NOTIFICATIONS_ALL_READ'
    ) {
      loadAlerts();
    }
  }, []);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(handleWebSocketEvent);

  // Load Incidents
  const loadIncidents = async () => {
    try {
      const res = await incidentService.getIncidents({ limit: 100 });
      const items = res.items || [];
      setIncidents(items);
    } catch (e) {
      console.error('Error fetching incidents:', e);
    }
  };

  // Load Resources
  const loadResources = async () => {
    try {
      const res = await resourceService.getResources();
      setResources(res || []);
    } catch (e) {
      console.error('Error fetching resources:', e);
    }
  };

  // Load Hospitals
  const loadHospitals = async () => {
    try {
      const res = await hospitalService.getHospitals();
      setHospitals(res || []);
    } catch (e) {
      console.error('Error fetching hospitals:', e);
    }
  };

  // Load Alerts
  const loadAlerts = async () => {
    try {
      const res = await notificationService.getNotifications({ limit: 50 });
      setAlerts(res || []);
    } catch (e) {
      console.error('Error fetching alerts:', e);
    }
  };

  // Full Initial Dashboard Data Load
  const loadDashboardData = async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    try {
      await Promise.all([
        loadIncidents(),
        loadResources(),
        loadHospitals(),
        loadAlerts(),
      ]);
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData(true);
  }, []);

  // Auto-select inc-001 if no incident is selected
  useEffect(() => {
    if (!selectedIncident && incidents.length > 0) {
      const inc001 = incidents.find((i) => i.incident_id === 'inc-001') || incidents[0];
      setSelectedIncident(inc001);
    }
  }, [incidents, selectedIncident]);

  // Top header statistics
  const activeIncidents = incidents.filter(
    (i) => !['RESOLVED', 'CLOSED'].includes(i.status?.toUpperCase())
  );
  const criticalIncidents = activeIncidents.filter(
    (i) => i.severity?.toUpperCase() === 'CRITICAL'
  );
  const availableResources = resources.filter(
    (r) => (r.status || '').toUpperCase() === 'AVAILABLE'
  );
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-100 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      {/* Top Header */}
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length || 5}
        criticalIncidentsCount={criticalIncidents.length || 1}
        availableResourcesCount={availableResources.length || 1}
        unreadAlertsCount={unreadAlerts.length || 2}
        onOpenNewIncidentModal={() => setIsReportModalOpen(true)}
      />

      {/* STEP 12: Full-Height 3-Column Desktop Layout (responsive stack on mobile) */}
      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
        {/* Center: Leaflet Emergency Map */}
        <div className="flex-1 h-[420px] lg:h-full relative overflow-hidden bg-slate-100">
          <DynamicMapView
            incidents={incidents}
            resources={resources}
            hospitals={hospitals}
            selectedIncident={selectedIncident}
            onSelectIncident={(inc) => setSelectedIncident(inc)}
            onAssignResource={(inc, res) => {
              setDispatchIncident(inc);
              setIsDispatchModalOpen(true);
            }}
            className="w-full h-full"
          />
        </div>

        {/* Right (400px): Resource Status Summary & AI Situation Briefing / Detail Panel */}
        <RightCommandPanel
          selectedIncident={selectedIncident}
          onSelectIncident={(inc) => setSelectedIncident(inc)}
          resources={resources}
          hospitals={hospitals}
          onIncidentUpdated={() => loadDashboardData(false)}
          className="w-full lg:w-[400px] lg:min-w-[400px] lg:max-w-[400px] h-[380px] lg:h-full shrink-0"
        />
      </main>

      {/* Quick Dispatch Modal */}
      <AssignResourceModal
        incident={dispatchIncident}
        isOpen={isDispatchModalOpen}
        onClose={() => setIsDispatchModalOpen(false)}
        onAssigned={() => {
          loadDashboardData(false);
        }}
      />

      {/* Manual Report Modal */}
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
