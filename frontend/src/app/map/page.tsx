'use client';

import React, { useEffect, useState } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { DynamicMapView } from '@/components/Map/DynamicMapView';
import { IncidentDetailsModal } from '@/components/incidents/IncidentDetailsModal';
import { AssignResourceModal } from '@/components/resources/AssignResourceModal';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, AlertNotification } from '@/types';

export default function TacticalMapPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [dispatchIncident, setDispatchIncident] = useState<Incident | null>(null);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadData();
  });

  const loadData = async () => {
    try {
      const [incRes, resRes, alertRes] = await Promise.all([
        incidentService.getIncidents({ limit: 100 }),
        resourceService.getResources(),
        notificationService.getNotifications({ limit: 20 }),
      ]);
      setIncidents(incRes.items || []);
      setResources(resRes || []);
      setAlerts(alertRes || []);
    } catch (e) {
      console.error('Error fetching tactical map data:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableResources = resources.filter((r) => r.status === 'AVAILABLE');
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length}
        criticalIncidentsCount={criticalIncidents.length}
        availableResourcesCount={availableResources.length}
        unreadAlertsCount={unreadAlerts.length}
      />

      <main className="relative flex-1 p-4 overflow-hidden">
        <DynamicMapView
          incidents={incidents}
          resources={resources}
          selectedIncident={selectedIncident}
          onSelectIncident={(inc) => {
            setSelectedIncident(inc);
            setIsDetailsModalOpen(true);
          }}
          onAssignResource={() => {
            if (activeIncidents.length > 0) {
              setDispatchIncident(activeIncidents[0]);
              setIsDispatchModalOpen(true);
            }
          }}
          className="h-full w-full rounded-lg shadow-xs border border-slate-200"
        />
      </main>

      <IncidentDetailsModal
        incident={selectedIncident}
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        onOpenDispatch={(inc) => {
          setIsDetailsModalOpen(false);
          setDispatchIncident(inc);
          setIsDispatchModalOpen(true);
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
        onAssigned={() => {
          loadData();
        }}
      />
    </div>
  );
}
