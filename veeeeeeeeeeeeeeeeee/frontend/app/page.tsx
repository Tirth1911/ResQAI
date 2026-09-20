'use client';

import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MapWrapper from './components/MapWrapper';
import IncidentBoard from './components/IncidentBoard';
import FleetGrid from './components/FleetGrid';
import IngestionLab from './components/IngestionLab';
import AnalyticsPanel from './components/AnalyticsPanel';
import AlertsSidebar from './components/AlertsSidebar';

import { Incident, Resource, Alert, ResourceStatus, ReportSource } from './types';
import { INITIAL_INCIDENTS, INITIAL_RESOURCES, INITIAL_ALERTS } from './mockData';
import { getDispatchRecommendations, calculateDistanceKm, estimateEtaMin } from './utils';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'map' | 'incidents' | 'fleet' | 'ingestion' | 'analytics'>('map');
  
  const [incidents, setIncidents] = useState<Incident[]>(INITIAL_INCIDENTS);
  const [resources, setResources] = useState<Resource[]>(INITIAL_RESOURCES);
  const [alerts, setAlerts] = useState<Alert[]>(INITIAL_ALERTS);

  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(INITIAL_INCIDENTS[0] || null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isAlertsOpen, setIsAlertsOpen] = useState<boolean>(false);

  // Attempt backend API fetch on mount with fallback
  useEffect(() => {
    async function fetchBackendData() {
      try {
        const res = await fetch('http://localhost:8000/incidents', { signal: AbortSignal.timeout(2000) });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setIncidents(data);
          }
        }
      } catch (e) {
        // Fallback to initial dataset
      }
    }
    fetchBackendData();
  }, []);

  // Live simulation ticker effect
  useEffect(() => {
    if (!isSimulating) return;

    const interval = setInterval(() => {
      const presetEvents = [
        {
          title: 'Submerged Vehicle on Ashram Road Underpass',
          desc: 'Flash flooding underpass near Ashram Road. SUV trapped in 3ft water.',
          type: 'flood' as const,
          severity: 'medium' as const,
          lat: 23.0390,
          lng: 72.5710,
          address: 'Ashram Road Underpass, Ahmedabad'
        },
        {
          title: 'Commercial Transformer Fire',
          desc: 'High voltage transformer exploded near Satellite road market. Electrical fire spreading.',
          type: 'fire' as const,
          severity: 'high' as const,
          lat: 23.0290,
          lng: 72.5290,
          address: 'Satellite Road, Ahmedabad'
        }
      ];

      const event = presetEvents[Math.floor(Math.random() * presetEvents.length)];
      const newInc: Incident = {
        id: `inc-sim-${Date.now().toString().slice(-4)}`,
        title: event.title,
        description: event.desc,
        type: event.type,
        severity: event.severity,
        priority: event.severity === 'high' ? 82 : 60,
        status: 'open',
        lat: event.lat + (Math.random() - 0.5) * 0.005,
        lng: event.lng + (Math.random() - 0.5) * 0.005,
        address: event.address,
        source: 'citizen',
        report_count: 1,
        reports: [
          {
            id: `rep-sim-${Date.now()}`,
            source: 'citizen',
            reporter: 'Live Citizen Stream',
            raw_text: event.desc,
            lat: event.lat,
            lng: event.lng,
            reported_at: new Date().toISOString()
          }
        ],
        ai_confidence: 0.93,
        ai_reasoning: `Real-time simulated telemetry ingestion. Auto-assigned priority score ${event.severity === 'high' ? 82 : 60}.`,
        classified_by: 'ai',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        assignments: []
      };

      setIncidents(prev => [newInc, ...prev]);
    }, 12000);

    return () => clearInterval(interval);
  }, [isSimulating]);

  // Dispatch Unit Action Handler
  const handleDispatchUnit = (incidentId: string, resourceId: string) => {
    const inc = incidents.find(i => i.id === incidentId);
    const res = resources.find(r => r.id === resourceId);
    if (!inc || !res) return;

    const dist = calculateDistanceKm(inc.lat, inc.lng, res.lat, res.lng);
    const eta = estimateEtaMin(dist);

    const newAssignment = {
      id: `asgn-${Date.now()}`,
      incident_id: incidentId,
      resource_id: resourceId,
      resource_name: res.name,
      resource_kind: res.kind,
      status: 'en_route' as const,
      score: 95.0,
      distance_km: dist,
      eta_min: eta,
      assigned_at: new Date().toISOString()
    };

    setIncidents(prev =>
      prev.map(i => {
        if (i.id === incidentId) {
          const updatedAssignments = [...(i.assignments || []), newAssignment];
          return {
            ...i,
            status: 'dispatched',
            assignments: updatedAssignments,
            updated_at: new Date().toISOString()
          };
        }
        return i;
      })
    );

    setResources(prev =>
      prev.map(r => {
        if (r.id === resourceId) {
          return {
            ...r,
            status: 'dispatched',
            updated_at: new Date().toISOString()
          };
        }
        return r;
      })
    );

    if (selectedIncident?.id === incidentId) {
      setSelectedIncident(prev => prev ? {
        ...prev,
        status: 'dispatched',
        assignments: [...(prev.assignments || []), newAssignment]
      } : null);
    }
  };

  const handleToggleResourceStatus = (resourceId: string, newStatus: ResourceStatus) => {
    setResources(prev =>
      prev.map(r => r.id === resourceId ? { ...r, status: newStatus, updated_at: new Date().toISOString() } : r)
    );
  };

  const handleMergeReportToIncident = (
    incidentId: string,
    rawText: string,
    source: ReportSource,
    reporter: string,
    lat: number,
    lng: number
  ) => {
    setIncidents(prev =>
      prev.map(i => {
        if (i.id === incidentId) {
          const newReport = {
            id: `rep-${Date.now()}`,
            source,
            reporter,
            raw_text: rawText,
            lat,
            lng,
            reported_at: new Date().toISOString()
          };
          return {
            ...i,
            report_count: i.report_count + 1,
            reports: [newReport, ...i.reports],
            updated_at: new Date().toISOString()
          };
        }
        return i;
      })
    );
  };

  const handleAddNewIncident = (newInc: Incident) => {
    setIncidents(prev => [newInc, ...prev]);
    setSelectedIncident(newInc);
  };

  const handleResolveAlert = (alertId: string) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, resolved: true } : a));
  };

  const activeIncidentsCount = incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').length;
  const availableFleetCount = resources.filter(r => r.status === 'available').length;
  const unresolvedAlertCount = alerts.filter(a => !a.resolved).length;

  const currentRecommendations = selectedIncident 
    ? getDispatchRecommendations(selectedIncident, resources) 
    : [];

  return (
    <div className="min-h-screen bg-[#F5F1E8] flex flex-col font-sans text-[#1F2933] antialiased">
      
      {/* Header Bar */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        unresolvedAlertCount={unresolvedAlertCount}
        openAlertsModal={() => setIsAlertsOpen(true)}
        isSimulating={isSimulating}
        setIsSimulating={setIsSimulating}
        activeIncidentsCount={activeIncidentsCount}
        availableFleetCount={availableFleetCount}
      />

      {/* Main View Container */}
      <main className="flex-1 relative bg-[#F5F1E8]">
        {activeTab === 'map' && (
          <MapWrapper
            incidents={incidents}
            resources={resources}
            selectedIncident={selectedIncident}
            onSelectIncident={setSelectedIncident}
            onDispatchUnit={handleDispatchUnit}
            recommendations={currentRecommendations}
          />
        )}

        {activeTab === 'incidents' && (
          <IncidentBoard
            incidents={incidents}
            resources={resources}
            onDispatchUnit={handleDispatchUnit}
            onSelectIncidentOnMap={(inc) => {
              setSelectedIncident(inc);
              setActiveTab('map');
            }}
          />
        )}

        {activeTab === 'fleet' && (
          <FleetGrid
            resources={resources}
            onToggleStatus={handleToggleResourceStatus}
          />
        )}

        {activeTab === 'ingestion' && (
          <IngestionLab
            incidents={incidents}
            onAddNewIncident={handleAddNewIncident}
            onMergeReportToIncident={handleMergeReportToIncident}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsPanel
            incidents={incidents}
            resources={resources}
          />
        )}
      </main>

      {/* Alerts Drawer */}
      <AlertsSidebar
        alerts={alerts}
        isOpen={isAlertsOpen}
        onClose={() => setIsAlertsOpen(false)}
        onResolveAlert={handleResolveAlert}
      />

    </div>
  );
}
