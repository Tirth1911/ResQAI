'use client';

import React, { useEffect, useState } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { DynamicMapView } from '@/components/Map/DynamicMapView';
import { RightCommandPanel } from '@/components/dashboard/RightCommandPanel';
import { AssignResourceModal } from '@/components/resources/AssignResourceModal';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { hospitalService } from '@/services/hospitalService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, Hospital, AlertNotification } from '@/types';

export default function TacticalMapPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [dispatchIncident, setDispatchIncident] = useState<Incident | null>(null);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);

  // Tactical Routing & Simulation Interactive States
  const [hoveredUnitId, setHoveredUnitId] = useState<string | null>(null);
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [liveTelemetry, setLiveTelemetry] = useState<Record<string, { distanceKm: number; etaMin: number; arrived: boolean }>>({});

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadData();
  });

  const loadData = async () => {
    try {
      const [incRes, resRes, hospRes, alertRes] = await Promise.all([
        incidentService.getIncidents({ limit: 100 }),
        resourceService.getResources(),
        hospitalService.getHospitals(),
        notificationService.getNotifications({ limit: 20 }),
      ]);
      const fetchedIncidents = incRes.items || [];
      setIncidents(fetchedIncidents);
      setResources(resRes || []);
      setHospitals(hospRes || []);
      setAlerts(alertRes || []);

      // Sync selected incident with latest server data (e.g. updated assigned_resources)
      if (fetchedIncidents.length > 0) {
        setSelectedIncident((prev) => {
          if (!prev) {
            return fetchedIncidents.find((i) => i.incident_id === 'inc-001') || fetchedIncidents[0];
          }
          const fresh = fetchedIncidents.find(
            (i) => i.incident_id === prev.incident_id || i.id === prev.id || (i as any)._id === (prev as any)._id
          );
          return fresh || prev;
        });
      }
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
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-100 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length || 5}
        criticalIncidentsCount={criticalIncidents.length || 1}
        availableResourcesCount={availableResources.length || 1}
        unreadAlertsCount={unreadAlerts.length || 2}
        onSimulate={() => setIsSimulating((prev) => !prev)}
        isSimulating={isSimulating}
      />

      <main className="relative flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left: Leaflet Tactical Map */}
        <div className="flex-1 h-full relative overflow-hidden bg-slate-100">
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
            className="h-full w-full"
          />
        </div>

        {/* Right: Incident Detail & Dispatch Panel (Matching Screenshot 1 & 2) */}
        <RightCommandPanel
          selectedIncident={selectedIncident}
          onSelectIncident={(inc) => {
            setSelectedIncident(inc);
            setSelectedUnitId(null);
          }}
          resources={resources}
          hospitals={hospitals}
          onIncidentUpdated={loadData}
          hoveredUnitId={hoveredUnitId}
          selectedUnitId={selectedUnitId}
          onHoverUnit={(uId) => setHoveredUnitId(uId)}
          onSelectUnit={(uId) => setSelectedUnitId(uId)}
          liveTelemetry={liveTelemetry}
          className="w-full lg:w-[420px] shrink-0 h-full border-l border-slate-200"
        />
      </main>

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
