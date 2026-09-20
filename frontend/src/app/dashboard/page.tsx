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
import { useWebSocketContext } from '@/context/WebSocketContext';
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

  // Tactical Routing & Simulation Interactive States
  const [hoveredUnitId, setHoveredUnitId] = useState<string | null>(null);
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [liveTelemetry, setLiveTelemetry] = useState<Record<string, { distanceKm: number; etaMin: number; arrived: boolean }>>({});

  // Real-time WebSocket Event Handler with targeted in-memory state updates
  const handleWebSocketEvent = useCallback((payload: WebSocketEventPayload) => {
    const ev = payload.event;
    const data = (payload.data || {}) as any;

    if (ev === 'NEW_INCIDENT' || ev === 'INCIDENT_CREATED') {
      const inc = (data.incident_id ? data : { ...data, incident_id: payload.incident_id }) as Incident;
      const incId = inc.incident_id || (inc as any)._id || (inc as any).id;
      if (incId) {
        setIncidents((prev) => {
          const exists = prev.some((i) => i.incident_id === incId || i.id === incId);
          if (exists) {
            return prev.map((i) => (i.incident_id === incId || i.id === incId ? { ...i, ...inc } : i));
          }
          return [inc, ...prev];
        });
        setSelectedIncident((curr) => (!curr || inc.severity === 'CRITICAL' ? inc : curr));
      }
    } else if (
      ev === 'INCIDENT_UPDATED' ||
      ev === 'INCIDENT_VERIFIED' ||
      ev === 'INCIDENT_CLASSIFIED' ||
      ev === 'AI_ANALYSIS_UPDATED'
    ) {
      const incId = data.incident_id || payload.incident_id;
      if (incId) {
        setIncidents((prev) =>
          prev.map((i) => (i.incident_id === incId || i.id === incId ? { ...i, ...data } : i))
        );
        setSelectedIncident((curr) =>
          curr && (curr.incident_id === incId || curr.id === incId) ? { ...curr, ...data } : curr
        );
      }
    } else if (ev === 'INCIDENT_RESOLVED' || ev === 'INCIDENT_CLOSED') {
      const incId = data.incident_id || payload.incident_id;
      if (incId) {
        const newStatus = ev === 'INCIDENT_CLOSED' ? 'CLOSED' : 'RESOLVED';
        setIncidents((prev) =>
          prev.map((i) =>
            i.incident_id === incId || i.id === incId ? { ...i, ...data, status: newStatus as any } : i
          )
        );
        setSelectedIncident((curr) =>
          curr && (curr.incident_id === incId || curr.id === incId)
            ? { ...curr, ...data, status: newStatus as any }
            : curr
        );
      }
    } else if (ev === 'RESOURCE_UPDATED') {
      const resId = data.resource_id || payload.resource_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) => (r.resource_id === resId ? { ...r, ...data } : r))
        );
      }
    } else if (ev === 'RESOURCE_DISPATCHED' || ev === 'RESOURCE_ASSIGNED') {
      const resId = data.resource_id || payload.resource_id;
      const targetIncId = data.incident_id || payload.incident_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) =>
            r.resource_id === resId
              ? { ...r, ...data, status: 'BUSY', current_incident_id: targetIncId }
              : r
          )
        );
      }
      if (targetIncId) {
        setIncidents((prev) =>
          prev.map((inc) => {
            if (inc.incident_id === targetIncId || inc.id === targetIncId) {
              const assigned = inc.assigned_resources || [];
              const updatedAssigned =
                resId && !assigned.includes(resId) ? [...assigned, resId] : assigned;
              return {
                ...inc,
                assigned_resources: updatedAssigned,
                status:
                  inc.status === 'REPORTED' || inc.status === 'VERIFIED'
                    ? 'DISPATCHED'
                    : inc.status,
              };
            }
            return inc;
          })
        );
      }
    } else if (ev === 'RESOURCE_AVAILABLE' || ev === 'RESOURCE_RELEASED') {
      const resId = data.resource_id || payload.resource_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) =>
            r.resource_id === resId
              ? { ...r, ...data, status: 'AVAILABLE', current_incident_id: undefined }
              : r
          )
        );
      }
    } else if (
      ev === 'ALERT_CREATED' ||
      ev === 'NOTIFICATION_CREATED' ||
      ev === 'ALERT_TRIGGERED'
    ) {
      const newAlert = data as AlertNotification;
      setAlerts((prev) => {
        const aId = newAlert.id || (newAlert as any)._id || newAlert.alert_id;
        if (aId && prev.some((a) => a.id === aId || (a as any)._id === aId || a.alert_id === aId)) {
          return prev;
        }
        return [newAlert, ...prev];
      });
    } else if (
      ev === 'DUPLICATE_DETECTED' ||
      ev === 'INCIDENT_DUPLICATED' ||
      ev === 'INCIDENT_DUPLICATE_MERGED'
    ) {
      const targetIncId = data.matched_incident_id || payload.incident_id;
      if (targetIncId) {
        setIncidents((prev) =>
          prev.map((inc) => {
            if (inc.incident_id === targetIncId || inc.id === targetIncId) {
              return {
                ...inc,
                duplicate_count: (inc.duplicate_count || 1) + 1,
              };
            }
            return inc;
          })
        );
      }
    }
  }, []);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(handleWebSocketEvent);
  const { reconnectCount } = useWebSocketContext();

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

  // Synchronize latest server state whenever WebSocket reconnects
  useEffect(() => {
    if (reconnectCount > 0) {
      console.log('[Dashboard] WebSocket reconnected. Synchronizing latest state from server...');
      loadDashboardData(false);
    }
  }, [reconnectCount]);

  // Auto-select inc-001 or sync selected incident with latest incident data
  useEffect(() => {
    if (incidents.length > 0) {
      if (!selectedIncident) {
        const inc001 = incidents.find((i) => i.incident_id === 'inc-001') || incidents[0];
        setSelectedIncident(inc001);
      } else {
        const fresh = incidents.find(
          (i) => i.incident_id === selectedIncident.incident_id || i.id === selectedIncident.id || (i as any)._id === (selectedIncident as any)._id
        );
        if (fresh && fresh.assigned_resources?.length !== selectedIncident.assigned_resources?.length) {
          setSelectedIncident(fresh);
        }
      }
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
        onSimulate={() => setIsSimulating((prev) => !prev)}
        isSimulating={isSimulating}
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
            onSelectIncident={(inc) => {
              setSelectedIncident(inc);
              setSelectedUnitId(null);
            }}
            onAssignResource={(inc, res) => {
              setDispatchIncident(inc);
              setIsDispatchModalOpen(true);
            }}
            hoveredUnitId={hoveredUnitId}
            selectedUnitId={selectedUnitId}
            onHoverUnit={(uId) => setHoveredUnitId(uId)}
            onSelectUnit={(uId) => setSelectedUnitId(uId)}
            isSimulating={isSimulating}
            onToggleSimulate={() => setIsSimulating((prev) => !prev)}
            onTelemetryUpdate={(tel) => setLiveTelemetry(tel)}
            className="w-full h-full"
          />
        </div>

        {/* Right (400px): Resource Status Summary & AI Situation Briefing / Detail Panel */}
        <RightCommandPanel
          selectedIncident={selectedIncident}
          onSelectIncident={(inc) => {
            setSelectedIncident(inc);
            setSelectedUnitId(null);
          }}
          resources={resources}
          hospitals={hospitals}
          onIncidentUpdated={() => loadDashboardData(false)}
          hoveredUnitId={hoveredUnitId}
          selectedUnitId={selectedUnitId}
          onHoverUnit={(uId) => setHoveredUnitId(uId)}
          onSelectUnit={(uId) => setSelectedUnitId(uId)}
          liveTelemetry={liveTelemetry}
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
