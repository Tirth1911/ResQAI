'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { ResourceModal } from '@/components/resources/ResourceModal';
import { resourceService } from '@/services/resourceService';
import { incidentService } from '@/services/incidentService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { useWebSocketContext } from '@/context/WebSocketContext';
import { Resource, Incident, AlertNotification, ResourceStatus } from '@/types';
import {
  Truck,
  Shield,
  Flame,
  Activity,
  Radio,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
  Plus,
  RefreshCw,
} from 'lucide-react';

export default function ResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters matching reference screenshot
  const [kindFilter, setKindFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Resource Modal state (for creating or editing units)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);

  const handleWebSocketEvent = useCallback((payload: any) => {
    const ev = payload.event;
    const data = (payload.data || {}) as any;

    if (ev === 'RESOURCE_UPDATED') {
      const resId = data.resource_id || payload.resource_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) => (r.resource_id === resId ? { ...r, ...data } : r))
        );
      }
    } else if (ev === 'RESOURCE_DISPATCHED' || ev === 'RESOURCE_ASSIGNED') {
      const resId = data.resource_id || payload.resource_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) =>
            r.resource_id === resId
              ? {
                  ...r,
                  ...data,
                  status: 'BUSY' as ResourceStatus,
                  current_incident_id: data.incident_id || payload.incident_id,
                }
              : r
          )
        );
      }
    } else if (ev === 'RESOURCE_AVAILABLE' || ev === 'RESOURCE_RELEASED') {
      const resId = data.resource_id || payload.resource_id;
      if (resId) {
        setResources((prev) =>
          prev.map((r) =>
            r.resource_id === resId
              ? {
                  ...r,
                  ...data,
                  status: 'AVAILABLE' as ResourceStatus,
                  current_incident_id: undefined,
                }
              : r
          )
        );
      }
    } else if (ev === 'RESOURCE_CREATED') {
      const newRes = data as Resource;
      if (newRes && newRes.resource_id) {
        setResources((prev) => {
          if (prev.some((r) => r.resource_id === newRes.resource_id)) {
            return prev.map((r) => (r.resource_id === newRes.resource_id ? { ...r, ...newRes } : r));
          }
          return [newRes, ...prev];
        });
      }
    } else if (ev === 'NEW_INCIDENT' || ev === 'INCIDENT_CREATED') {
      const newInc = data as Incident;
      if (newInc && newInc.incident_id) {
        setIncidents((prev) => [newInc, ...prev.filter((i) => i.incident_id !== newInc.incident_id)]);
      }
    } else if (ev === 'INCIDENT_RESOLVED' || ev === 'INCIDENT_CLOSED') {
      const incId = data.incident_id || payload.incident_id;
      if (incId) {
        setIncidents((prev) =>
          prev.map((i) => (i.incident_id === incId ? { ...i, status: 'RESOLVED' as any } : i))
        );
      }
    } else if (ev === 'INCIDENT_UPDATED') {
      const incId = data.incident_id || payload.incident_id;
      if (incId) {
        setIncidents((prev) =>
          prev.map((i) => (i.incident_id === incId ? { ...i, ...data } : i))
        );
      }
    } else if (ev === 'ALERT_CREATED' || ev === 'NOTIFICATION_CREATED') {
      const newAlert = data as AlertNotification;
      setAlerts((prev) => [newAlert, ...prev]);
    }
  }, []);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(handleWebSocketEvent);
  const { reconnectCount } = useWebSocketContext();

  const loadData = async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    try {
      const [resList, incList, alertList] = await Promise.all([
        resourceService.getResources(),
        incidentService.getActiveIncidents(50),
        notificationService.getNotifications({ limit: 20 }),
      ]);
      setResources(resList || []);
      setIncidents(incList.items || []);
      setAlerts(alertList || []);
    } catch (e) {
      console.error('Error loading resources:', e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
  }, []);

  useEffect(() => {
    if (reconnectCount > 0) {
      console.log('[ResourcesPage] Reconnected to server. Refreshing latest fleet state...');
      loadData(false);
    }
  }, [reconnectCount]);

  // Update status with real backend API
  const handleStatusChange = async (resourceId: string, newStatus: string) => {
    try {
      // Optimistic update
      setResources((prev) =>
        prev.map((r) =>
          r.resource_id === resourceId
            ? { ...r, status: newStatus as ResourceStatus }
            : r
        )
      );
      await resourceService.updateResourceStatus(resourceId, newStatus);
      await loadData(false);
    } catch (e) {
      console.error('Error updating resource status:', e);
      await loadData(false);
    }
  };

  const handleSaveResourceModal = async (resourceData: any) => {
    try {
      if (modalMode === 'create') {
        await resourceService.createResource(resourceData);
      } else if (modalMode === 'edit' && selectedResource) {
        const id = selectedResource.resource_id || selectedResource.id || selectedResource._id;
        if (id) {
          await resourceService.updateResource(id, resourceData);
        }
      }
      setIsModalOpen(false);
      await loadData(false);
    } catch (e) {
      console.error('Error saving resource:', e);
    }
  };

  // Helper to categorize resources into visual Asset Classes
  const getResourceKind = (res: Resource): string => {
    const cat = (res.category || '').toUpperCase();
    const type = ((res as any).type || (res as any).kind || '').toUpperCase();
    const name = res.name.toLowerCase();
    const caps = (res.capabilities || []).map((c) => c.toUpperCase());

    if (cat.includes('FIRE') || type.includes('FIRE') || name.includes('fire') || name.includes('tender') || caps.some((c) => c.includes('FIRE'))) {
      return 'fire_truck';
    }
    if (cat.includes('AMBULANCE') || type.includes('AMBULANCE') || name.includes('ambulance') || name.includes('trauma') || caps.some((c) => c.includes('AMBULANCE') || c.includes('ALS'))) {
      return 'ambulance';
    }
    if (cat.includes('POLICE') || type.includes('POLICE') || name.includes('police') || name.includes('patrol') || name.includes('interceptor')) {
      return 'police_van';
    }
    if (cat.includes('HAZMAT') || type.includes('HAZMAT') || name.includes('hazmat') || name.includes('decon') || caps.some((c) => c.includes('HAZMAT') || c.includes('DECONTAMINATION'))) {
      return 'hazmat_unit';
    }
    if (cat.includes('BOAT') || type.includes('BOAT') || name.includes('boat') || caps.some((c) => c.includes('BOAT') || c.includes('DIVING'))) {
      return 'rescue_boat';
    }
    if (cat.includes('DISASTER') || name.includes('ndrf') || name.includes('heavy rescue') || caps.some((c) => c.includes('HEAVY_RESCUE') || c.includes('NDRF'))) {
      return 'ndrf_team';
    }
    if (cat.includes('DRONE') || name.includes('drone') || caps.some((c) => c.includes('DRONE') || c.includes('RECON'))) {
      return 'drone';
    }
    return 'emergency_unit';
  };

  // Badge rendering matching Screenshot 2
  const getKindBadge = (res: Resource) => {
    const kind = getResourceKind(res);
    switch (kind) {
      case 'fire_truck':
        return (
          <span className="flex items-center gap-1 text-[#B42318] bg-[#FDECEC] px-2 py-0.5 rounded font-semibold text-xs border border-[#FCA5A5]/40">
            🚒 Fire Engine
          </span>
        );
      case 'ambulance':
        return (
          <span className="flex items-center gap-1 text-[#16803C] bg-[#EAF6ED] px-2 py-0.5 rounded font-semibold text-xs border border-[#A7F3D0]/50">
            🚑 108 ALS Ambulance
          </span>
        );
      case 'police_van':
        return (
          <span className="flex items-center gap-1 text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded font-semibold text-xs border border-[#BFDBFE]/50">
            🚓 PCR Patrol
          </span>
        );
      case 'hazmat_unit':
        return (
          <span className="flex items-center gap-1 text-[#7C3AED] bg-[#F3E8FF] px-2 py-0.5 rounded font-semibold text-xs border border-[#DDD6FE]/50">
            ☣️ HAZMAT Decon
          </span>
        );
      case 'rescue_boat':
        return (
          <span className="flex items-center gap-1 text-[#0284C7] bg-[#E0F2FE] px-2 py-0.5 rounded font-semibold text-xs border border-[#BAE6FD]/50">
            🚤 Rescue Boat
          </span>
        );
      case 'ndrf_team':
        return (
          <span className="flex items-center gap-1 text-[#D97706] bg-[#FEF3C7] px-2 py-0.5 rounded font-semibold text-xs border border-[#FDE68A]/50">
            🛟 NDRF Team
          </span>
        );
      case 'drone':
        return (
          <span className="flex items-center gap-1 text-[#0891B2] bg-[#CFFAFE] px-2 py-0.5 rounded font-semibold text-xs border border-[#A5F3FC]/50">
            🛸 Recon Drone
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[#B42318] bg-[#FDECEC] px-2 py-0.5 rounded font-semibold text-xs border border-[#FCA5A5]/40">
            🚨 Response Unit
          </span>
        );
    }
  };

  // Filter resources using real state
  const filteredResources = resources.filter((res) => {
    const kind = getResourceKind(res);
    if (kindFilter !== 'all' && kind !== kindFilter) return false;

    if (statusFilter !== 'all') {
      const s = (res.status || '').toUpperCase();
      if (statusFilter === 'available' && s !== 'AVAILABLE') return false;
      if (statusFilter === 'dispatched' && s !== 'BUSY' && s !== 'EN_ROUTE') return false;
      if (statusFilter === 'on_scene' && s !== 'BUSY') return false;
      if (statusFilter === 'maintenance' && s !== 'OFFLINE' && s !== 'MAINTENANCE') return false;
    }
    return true;
  });

  // Calculate metrics
  const availableCount = resources.filter((r) => (r.status || '').toUpperCase() === 'AVAILABLE').length;
  const activeIncidents = incidents.filter((i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED');
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="min-h-screen w-screen flex flex-col bg-[#FAF8F5] text-[#1F2933] font-sans antialiased selection:bg-[#B42318] selection:text-white">
      {/* Retain top navbar intact */}
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length || 5}
        criticalIncidentsCount={criticalIncidents.length || 1}
        availableResourcesCount={availableCount}
        unreadAlertsCount={unreadAlerts.length || 2}
      />

      <main className="flex-1 max-w-[1700px] w-full mx-auto p-6 space-y-6 overflow-y-auto">
        {/* Fleet Header Controls matching Screenshot 2 */}
        <div className="bg-white border border-[#DED8CC] p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#FDECEC] text-[#B42318] rounded-xl border border-[#FCA5A5] flex items-center justify-center">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#1F2933] leading-snug">Emergency Response Fleet Grid</h2>
              <p className="text-xs text-[#667085] mt-0.5">
                Gujarat Sector Tactical Grid • {filteredResources.length} Monitored Units
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 text-[#667085] font-semibold">
              <span>ASSET CLASS:</span>
            </div>
            <select
              value={kindFilter}
              onChange={(e) => setKindFilter(e.target.value)}
              className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs font-medium text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318] cursor-pointer"
            >
              <option value="all">All Asset Classes</option>
              <option value="fire_truck">Fire Engine / Water Tender</option>
              <option value="ambulance">108 ALS Ambulance</option>
              <option value="police_van">PCR Police Patrol</option>
              <option value="hazmat_unit">HAZMAT Decon Unit</option>
              <option value="rescue_boat">Rescue Boat</option>
              <option value="ndrf_team">NDRF Heavy Rescue</option>
              <option value="drone">Recon Thermal Drone</option>
            </select>

            <div className="flex items-center gap-1.5 text-[#667085] font-semibold ml-2">
              <span>STATUS:</span>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs font-medium text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318] cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="available">Available</option>
              <option value="dispatched">Dispatched / Busy</option>
              <option value="on_scene">On Scene</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </div>
        </div>

        {/* Resource Cards Grid matching 4-column layout in Screenshot 2 */}
        {isLoading ? (
          <div className="flex h-72 w-full items-center justify-center rounded-xl border border-[#DED8CC] bg-white">
            <div className="flex flex-col items-center gap-2 text-[#667085]">
              <Loader2 className="h-6 w-6 animate-spin text-[#B42318]" />
              <span className="text-xs font-semibold">Loading Fleet Telemetry Database...</span>
            </div>
          </div>
        ) : filteredResources.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-xl border border-[#DED8CC] text-[#667085] text-sm">
            No response units match the current filter selection.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredResources.map((res) => {
              const statusUpper = (res.status || '').toUpperCase();
              const isAvailable = statusUpper === 'AVAILABLE';
              const isDispatched = statusUpper === 'BUSY' || statusUpper === 'EN_ROUTE';

              // Coordinates
              const lng = res.location?.coordinates?.[0] ?? 72.585;
              const lat = res.location?.coordinates?.[1] ?? 23.033;

              // Station / location label
              const stationLabel =
                (res as any).location_name ||
                (res as any).address ||
                res.location?.address ||
                ((res as any).station) ||
                'Command HQ Station';

              // Filter capabilities for concise clean display
              const cleanedCapabilities = (res.capabilities || [])
                .map((c) =>
                  c
                    .replace(/_TRUCK/g, '')
                    .replace(/_TEAM/g, '')
                    .replace(/PARAMEDIC/g, 'MEDICAL')
                )
                .filter((c) => c !== 'AMBULANCE' && c !== 'POLICE' && c !== '108');

              const displayCapabilities =
                cleanedCapabilities.length > 0
                  ? cleanedCapabilities.slice(0, 3).join(', ')
                  : 'GENERAL RESPONSE';

              return (
                <div
                  key={res.resource_id || res.id || (res as any)._id}
                  className="bg-white border border-[#DED8CC] p-5 rounded-xl shadow-xs flex flex-col justify-between gap-4 transition-all hover:border-[#B42318]/40"
                >
                  <div className="space-y-3">
                    {/* Top Badges Row */}
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[10px]">{getKindBadge(res)}</span>

                      <span
                        className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full ${
                          isAvailable
                            ? 'bg-[#EAF6ED] text-[#16803C] border border-[#A7F3D0]'
                            : isDispatched
                            ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]'
                            : 'bg-[#F5F1E8] text-[#667085] border border-[#DED8CC]'
                        }`}
                      >
                        {isDispatched ? 'DISPATCHED' : res.status}
                      </span>
                    </div>

                    {/* Unit Name & Station */}
                    <div>
                      <h3 className="font-bold text-[#1F2933] text-sm leading-snug line-clamp-1">
                        {res.name}
                      </h3>
                      <p className="text-[#667085] text-xs line-clamp-1 mt-0.5">
                        {stationLabel}
                      </p>
                    </div>

                    {/* Information Box inside card */}
                    <div className="bg-[#F5F1E8] p-3 rounded-lg border border-[#DED8CC] text-[11px] space-y-1.5 text-[#1F2933]">
                      <div className="flex justify-between items-center">
                        <span className="text-[#667085]">Personnel Capacity:</span>
                        <span className="font-bold text-[#1F2933]">
                          {res.capacity || 4} Responders
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[#667085]">Coordinates:</span>
                        <span className="font-mono text-[#1F2933]">
                          {lat.toFixed(4)}, {lng.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[#667085]">Capabilities:</span>
                        <span className="text-[#B42318] uppercase font-bold text-[10px] truncate max-w-[150px]">
                          {displayCapabilities}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Action Row matching screenshot */}
                  <div className="pt-2 border-t border-[#DED8CC] flex items-center justify-between text-xs mt-auto">
                    <span className="text-[10px] text-[#667085]">Action:</span>

                    {isAvailable ? (
                      <button
                        type="button"
                        onClick={() => handleStatusChange(res.resource_id, 'BUSY')}
                        className="px-3.5 py-1.5 bg-[#16803C] hover:bg-[#126730] active:scale-95 text-white rounded-lg text-xs font-bold transition-all shadow-2xs cursor-pointer"
                      >
                        Dispatch Unit
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleStatusChange(res.resource_id, 'AVAILABLE')}
                        className="px-3.5 py-1.5 bg-[#16803C] hover:bg-[#126730] active:scale-95 text-white rounded-lg text-xs font-bold transition-all shadow-2xs cursor-pointer"
                      >
                        Set Available
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Preserve modal for adding or editing resources */}
      {isModalOpen && (
        <ResourceModal
          isOpen={isModalOpen}
          mode={modalMode}
          resource={selectedResource}
          onClose={() => setIsModalOpen(false)}
          onSave={handleSaveResourceModal}
        />
      )}
    </div>
  );
}
