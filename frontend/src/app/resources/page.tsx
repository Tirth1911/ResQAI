'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { ResourceCard } from '@/components/resources/ResourceCard';
import { ResourceModal } from '@/components/resources/ResourceModal';
import { ResourceRecommendation } from '@/components/resources/ResourceRecommendation';
import { DashboardCard } from '@/components/common/DashboardCard';
import { StatusBadge } from '@/components/StatusBadge';
import { resourceService } from '@/services/resourceService';
import { incidentService } from '@/services/incidentService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Resource, Incident, AlertNotification, ResourceRecommendation as RecType } from '@/types';

import {
  Truck,
  Search,
  RefreshCw,
  Plus,
  CheckCircle,
  Activity,
  AlertTriangle,
  RotateCcw,
  LayoutGrid,
  Table as TableIcon,
  Sparkles,
  ArrowRight,
  Edit2,
  Eye,
  Check,
  Radio,
  MapPin,
  Send,
  Loader2
} from 'lucide-react';

export default function ResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // View Layout mode: 'cards' or 'table'
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Resource Modal state (create, edit, view)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);

  // Recommendation matcher state
  const [selectedIncidentForRecs, setSelectedIncidentForRecs] = useState<string>('');
  const [recommendations, setRecommendations] = useState<RecType[]>([]);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [assigningResourceId, setAssigningResourceId] = useState<string | null>(null);

  const handleWebSocketEvent = useCallback((payload: any) => {
    if (
      payload.event === 'RESOURCE_CREATED' ||
      payload.event === 'RESOURCE_UPDATED' ||
      payload.event === 'RESOURCE_ASSIGNED' ||
      payload.event === 'RESOURCE_RELEASED' ||
      payload.event === 'RESOURCE_SHORTAGE' ||
      payload.event === 'INCIDENT_CREATED' ||
      payload.event === 'INCIDENT_UPDATED'
    ) {
      loadData(false);
    }
  }, []);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(handleWebSocketEvent);

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

      if (selectedIncidentForRecs) {
        fetchRecommendationsForIncident(selectedIncidentForRecs);
      } else if (incList.items && incList.items.length > 0) {
        setSelectedIncidentForRecs(incList.items[0].incident_id);
        fetchRecommendationsForIncident(incList.items[0].incident_id);
      }
    } catch (e) {
      console.error('Error loading resources:', e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
  }, []);

  const fetchRecommendationsForIncident = async (incidentId: string) => {
    if (!incidentId) return;
    setIsLoadingRecs(true);
    try {
      const res = await resourceService.getRecommendations(incidentId);
      if (res?.recommendations) {
        setRecommendations(res.recommendations);
      }
    } catch (e) {
      console.error('Error getting recommendations:', e);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  const handleIncidentSelectChange = (incidentId: string) => {
    setSelectedIncidentForRecs(incidentId);
    fetchRecommendationsForIncident(incidentId);
  };

  const handleAssignRecommendation = async (rec: RecType) => {
    if (!selectedIncidentForRecs) return;
    setAssigningResourceId(rec.resource_id);
    try {
      await incidentService.assignResource(
        selectedIncidentForRecs,
        rec.resource_id,
        'Command Dispatcher',
        `Dispatched via Resource Recommendation Console (Match Score: ${(rec.score * 100).toFixed(0)}%)`
      );
      await loadData(false);
    } catch (e) {
      console.error('Failed to assign recommended unit:', e);
    } finally {
      setAssigningResourceId(null);
    }
  };

  const handleCreateResource = () => {
    setSelectedResource(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleEditResource = (res: Resource) => {
    setSelectedResource(res);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  const handleViewResource = (res: Resource) => {
    setSelectedResource(res);
    setModalMode('view');
    setIsModalOpen(true);
  };

  const handleStatusChange = async (resourceId: string, newStatus: string) => {
    try {
      await resourceService.updateResourceStatus(resourceId, newStatus);
      await loadData(false);
    } catch (e) {
      console.error('Error updating resource status:', e);
    }
  };

  const handleReleaseResource = async (res: Resource) => {
    try {
      await resourceService.releaseResource(res.resource_id, 'Command Dispatcher');
      await loadData(false);
    } catch (e) {
      console.error('Error releasing resource:', e);
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

  const handleResetFilters = () => {
    setSearchTerm('');
    setCategoryFilter('ALL');
    setStatusFilter('ALL');
  };

  // Filtered list
  const filteredResources = resources.filter((res) => {
    const matchesSearch =
      !searchTerm ||
      res.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.resource_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (res.category || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      ((res as any).type || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      categoryFilter === 'ALL' ||
      res.category.toLowerCase() === categoryFilter.toLowerCase() ||
      ((res as any).type || '').toLowerCase() === categoryFilter.toLowerCase();

    const matchesStatus =
      statusFilter === 'ALL' || res.status.toUpperCase() === statusFilter.toUpperCase();

    return matchesSearch && matchesCategory && matchesStatus;
  });

  // Metrics
  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
  const busyCount = resources.filter((r) => r.status === 'BUSY' || r.status === 'EN_ROUTE').length;
  const offlineCount = resources.filter((r) => r.status === 'OFFLINE' || r.status === 'MAINTENANCE').length;
  const activeIncidents = incidents.filter((i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED');
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const unreadAlerts = alerts.filter((a) => !a.read);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased selection:bg-red-500 selection:text-white">
      <TopHeader
        wsConnected={wsConnected}
        wsStatus={wsStatus}
        systemStatus="ONLINE"
        activeIncidentsCount={activeIncidents.length}
        criticalIncidentsCount={criticalIncidents.length}
        availableResourcesCount={availableCount}
        unreadAlertsCount={unreadAlerts.length}
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Page Title Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white">
                <Truck className="h-4 w-4" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Fleet & Resource Coordination
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Real-time telemetry tracking, unit availability, automated geospatial matching, and fleet management
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => loadData(false)}
              className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
              <span>Sync</span>
            </button>

            <button
              type="button"
              onClick={handleCreateResource}
              className="flex items-center gap-1.5 rounded-md bg-red-600 hover:bg-red-700 px-4 py-1.5 text-xs font-bold text-white shadow-xs transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>Add Resource Unit</span>
            </button>
          </div>
        </div>

        {/* Fleet KPI Metric Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <DashboardCard
            title="Total Registered Fleet"
            value={resources.length}
            subtitle="Cross-agency fleet units"
            icon={<Truck className="h-4 w-4" />}
            variant="default"
          />

          <DashboardCard
            title="Available & Ready"
            value={availableCount}
            subtitle="Ready for instant dispatch"
            icon={<CheckCircle className="h-4 w-4" />}
            variant="success"
          />

          <DashboardCard
            title="Deployed / Busy"
            value={busyCount}
            subtitle="Actively assigned to incidents"
            icon={<Activity className="h-4 w-4" />}
            variant="warning"
          />

          <DashboardCard
            title="Maintenance / Offline"
            value={offlineCount}
            subtitle="Under service or offline"
            icon={<AlertTriangle className="h-4 w-4" />}
            variant="default"
          />
        </div>

        {/* AI Multi-Criteria Recommendation Matcher Console */}
        <div className="rounded-lg border border-red-200 bg-red-50/40 p-4 shadow-2xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-red-100 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-red-600" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Weighted Multi-Criteria Resource Recommendation Algorithm
                </h3>
                <p className="text-xs text-slate-600">
                  Calculates Proximity (50%), Capability Match (30%), and Unit Availability (20%)
                </p>
              </div>
            </div>

            {/* Target Incident Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-700 shrink-0">Select Active Incident:</span>
              <select
                value={selectedIncidentForRecs}
                onChange={(e) => handleIncidentSelectChange(e.target.value)}
                className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 focus:border-red-500 focus:outline-none shadow-2xs max-w-xs"
              >
                {activeIncidents.length === 0 ? (
                  <option value="">No Active Incidents</option>
                ) : (
                  activeIncidents.map((inc) => (
                    <option key={inc.incident_id} value={inc.incident_id}>
                      #{inc.incident_id} - {inc.title || inc.type} ({inc.severity})
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {/* Recommendations Row */}
          {isLoadingRecs ? (
            <div className="flex h-24 items-center justify-center text-xs font-medium text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin text-red-600 mr-2" />
              <span>Calculating optimal fleet match matrix...</span>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">
              Select an active incident above to view real-time ranked unit recommendations.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {recommendations.slice(0, 3).map((rec, idx) => (
                <div
                  key={rec.resource_id}
                  className="rounded-md border border-slate-200 bg-white p-3 shadow-2xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="flex h-5 w-5 items-center justify-center rounded bg-red-100 text-[10px] font-bold text-red-700">
                        #{idx + 1}
                      </span>
                      <span className="font-bold text-xs text-slate-900">{rec.name || rec.resource_name || 'Unit'}</span>
                    </div>
                    <span className="text-xs font-extrabold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                      {(rec.score * 100).toFixed(0)}% Match
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-1">
                    <div className="flex justify-between">
                      <span>ETA Distance:</span>
                      <span className="font-bold text-slate-900">{rec.distance_km?.toFixed(1) || '1.8'} km</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Category:</span>
                      <span className="capitalize">{(rec.category || rec.resource_type || '').replace('_', ' ')}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleAssignRecommendation(rec)}
                    disabled={assigningResourceId === rec.resource_id}
                    className="w-full flex items-center justify-center gap-1 rounded bg-red-600 hover:bg-red-700 py-1.5 text-xs font-bold text-white transition-colors disabled:opacity-50"
                  >
                    {assigningResourceId === rec.resource_id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Send className="h-3 w-3" />
                    )}
                    <span>Dispatch Recommended Unit</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Search, Filter & Layout Controls */}
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search resources by callsign, ID, capability, or type..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-red-500 focus:bg-white focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center rounded-md border border-slate-200 bg-slate-100 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setViewMode('cards')}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-sm font-semibold transition-colors ${
                    viewMode === 'cards'
                      ? 'bg-white text-slate-900 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  <span>Cards</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('table')}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-sm font-semibold transition-colors ${
                    viewMode === 'table'
                      ? 'bg-white text-slate-900 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <TableIcon className="h-3.5 w-3.5" />
                  <span>Table</span>
                </button>
              </div>

              {(searchTerm || categoryFilter !== 'ALL' || statusFilter !== 'ALL') && (
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="text-xs text-red-600 hover:underline flex items-center gap-1 font-semibold"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Reset</span>
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100 text-xs">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Resource Category / Type
              </label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="ambulance">Ambulance</option>
                <option value="fire_truck">Fire Engine</option>
                <option value="police">Police Patrol</option>
                <option value="rescue_team">Rescue Team</option>
                <option value="hazmat">Hazmat Unit</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Status Filter
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="AVAILABLE">Available</option>
                <option value="BUSY">Deployed / Busy</option>
                <option value="EN_ROUTE">En Route</option>
                <option value="OFFLINE">Offline / Service</option>
              </select>
            </div>
          </div>
        </div>

        {/* Content: Cards or Table View */}
        {isLoading ? (
          <div className="flex h-64 w-full items-center justify-center rounded-lg border border-slate-200 bg-white">
            <Loader2 className="h-6 w-6 animate-spin text-red-600 mr-2" />
            <span className="text-xs font-semibold text-slate-500">Loading Fleet Telemetry Database...</span>
          </div>
        ) : filteredResources.length === 0 ? (
          <div className="flex h-64 w-full flex-col items-center justify-center rounded-lg border border-slate-200 bg-white p-6 text-center">
            <Truck className="h-8 w-8 text-slate-400 mb-2" />
            <h3 className="text-sm font-bold text-slate-900">No Resources Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              No response units match the current filters. Reset search or add a new unit.
            </p>
          </div>
        ) : viewMode === 'cards' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredResources.map((res) => (
              <ResourceCard
                key={res.resource_id || res.id || res._id}
                resource={res}
                onSelect={(r) => handleViewResource(r)}
                onEdit={(r) => handleEditResource(r)}
                onRelease={(r) => handleReleaseResource(r)}
                onStatusChange={(status: any) => handleStatusChange(res.resource_id, status)}
                onAssign={(r) => handleViewResource(r)}
              />
            ))}
          </div>
        ) : (
          /* Table View */
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-xs">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] uppercase font-bold text-slate-500">
                <tr>
                  <th className="px-4 py-3">Resource Name / ID</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Capabilities</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Assigned Incident</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredResources.map((res) => {
                  const isBusy = res.status === 'BUSY' || res.status === 'EN_ROUTE';
                  return (
                    <tr key={res.resource_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-bold text-slate-900">{res.name}</div>
                        <div className="font-mono text-[10px] text-slate-400">#{res.resource_id}</div>
                      </td>
                      <td className="px-4 py-3 capitalize">{(res.category || res.type || '').replace('_', ' ')}</td>
                      <td className="px-4 py-3">
                        <StatusBadge type="resource" value={res.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {res.capabilities?.map((cap, i) => (
                            <span
                              key={i}
                              className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded text-[10px] border border-slate-200"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {res.location?.address || 'Sector 12 Command'}
                      </td>
                      <td className="px-4 py-3">
                        {res.current_incident_id || res.assigned_incident_id ? (
                          <span className="font-mono font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                            #{res.current_incident_id || res.assigned_incident_id}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Unassigned</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {isBusy && (
                            <button
                              type="button"
                              onClick={() => handleReleaseResource(res)}
                              className="px-2 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-700 font-bold text-[11px] border border-amber-200"
                            >
                              Release
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleViewResource(res)}
                            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px]"
                          >
                            View
                          </button>
                          <button
                            type="button"
                            onClick={() => handleEditResource(res)}
                            className="px-2 py-1 rounded bg-red-50 hover:bg-red-100 text-red-700 font-bold text-[11px] border border-red-200"
                          >
                            Edit
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Resource Create / Edit Modal */}
      <ResourceModal
        isOpen={isModalOpen}
        mode={modalMode}
        resource={selectedResource}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveResourceModal}
      />
    </div>
  );
}
