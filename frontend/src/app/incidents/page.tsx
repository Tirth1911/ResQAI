'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { SeverityBadge } from '@/components/common/SeverityBadge';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { StatusBadge } from '@/components/StatusBadge';
import { IncidentDetailsModal } from '@/components/incidents/IncidentDetailsModal';
import { AssignResourceModal } from '@/components/resources/AssignResourceModal';
import { ReportIncidentModal } from '@/components/ReportModal/ReportIncidentModal';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, AlertNotification } from '@/types';

import {
  Flame,
  Search,
  Filter,
  RefreshCw,
  Plus,
  Sparkles,
  Send,
  CheckCircle,
  Eye,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RotateCcw,
  MapPin,
  Clock,
  Radio,
  FileText
} from 'lucide-react';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Pagination state
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(12);
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sourceFilter, setSourceFilter] = useState('ALL');

  // Modals & Selected states
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [dispatchIncident, setDispatchIncident] = useState<Incident | null>(null);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // In-flight action loading states
  const [analyzingIncidentId, setAnalyzingIncidentId] = useState<string | null>(null);
  const [verifyingIncidentId, setVerifyingIncidentId] = useState<string | null>(null);
  const [resolvingIncidentId, setResolvingIncidentId] = useState<string | null>(null);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadData(false);
  });

  const loadData = useCallback(
    async (showLoading = true) => {
      if (showLoading) setIsLoading(true);
      try {
        const queryParams: any = {
          page,
          limit,
        };

        if (severityFilter !== 'ALL') queryParams.severity = severityFilter;
        if (priorityFilter !== 'ALL') queryParams.priority = priorityFilter;
        if (typeFilter !== 'ALL') queryParams.type = typeFilter;
        if (statusFilter !== 'ALL') queryParams.status = statusFilter;
        if (sourceFilter !== 'ALL') queryParams.source = sourceFilter;
        if (searchTerm.trim()) queryParams.search = searchTerm.trim();

        const [incRes, resRes, alertRes] = await Promise.all([
          incidentService.getIncidents(queryParams),
          resourceService.getResources(),
          notificationService.getNotifications({ limit: 20 }),
        ]);

        setIncidents(incRes.items || []);
        setTotalIncidents(incRes.total || 0);
        setTotalPages(incRes.total_pages || Math.ceil((incRes.total || 1) / limit));
        setResources(resRes || []);
        setAlerts(alertRes || []);
      } catch (e) {
        console.error('Error fetching incidents:', e);
      } finally {
        if (showLoading) setIsLoading(false);
      }
    },
    [page, limit, severityFilter, priorityFilter, typeFilter, statusFilter, sourceFilter, searchTerm]
  );

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  // Actions
  const handleAnalyze = async (incident: Incident) => {
    setAnalyzingIncidentId(incident.incident_id);
    try {
      await incidentService.analyzeIncident(incident.incident_id, true);
      const updated = await incidentService.getIncidentById(incident.incident_id);
      setIncidents((prev) =>
        prev.map((i) => (i.incident_id === incident.incident_id ? updated : i))
      );
      setSelectedIncident(updated);
      setIsDetailsModalOpen(true);
    } catch (e) {
      console.error('Error running AI triage:', e);
    } finally {
      setAnalyzingIncidentId(null);
    }
  };

  const handleVerify = async (incident: Incident) => {
    setVerifyingIncidentId(incident.incident_id);
    try {
      const res = await incidentService.verifyIncident(incident.incident_id, 'Command Dispatcher');
      setIncidents((prev) =>
        prev.map((i) => (i.incident_id === incident.incident_id ? res : i))
      );
    } catch (e) {
      console.error('Failed to verify incident:', e);
    } finally {
      setVerifyingIncidentId(null);
    }
  };

  const handleResolve = async (incident: Incident) => {
    setResolvingIncidentId(incident.incident_id);
    try {
      const res = await incidentService.resolveIncident(incident.incident_id, 'Command Dispatcher');
      setIncidents((prev) =>
        prev.map((i) => (i.incident_id === incident.incident_id ? res : i))
      );
    } catch (e) {
      console.error('Failed to resolve incident:', e);
    } finally {
      setResolvingIncidentId(null);
    }
  };

  const handleResetFilters = () => {
    setSearchTerm('');
    setSeverityFilter('ALL');
    setPriorityFilter('ALL');
    setTypeFilter('ALL');
    setStatusFilter('ALL');
    setSourceFilter('ALL');
    setPage(1);
  };

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = incidents.filter((i) => i.severity === 'CRITICAL');
  const availableResources = resources.filter((r) => r.status === 'AVAILABLE');
  const unreadAlerts = alerts.filter((a) => !a.read);

  const typeIcons: Record<string, string> = {
    fire: '🔥',
    flood: '🌊',
    road_accident: '🚗',
    medical_emergency: '🚑',
    industrial_hazard: '☢️',
    building_collapse: '🏚️',
    gas_leak: '💨',
    earthquake: '🌋',
    other: '⚠️',
  };

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
        onOpenNewIncidentModal={() => setIsReportModalOpen(true)}
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Page Title & Main Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white">
                <Flame className="h-4 w-4" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Incident Command Center
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Active emergency triage queue, AI incident classification, and multi-agency dispatch management
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
              onClick={() => setIsReportModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-red-600 hover:bg-red-700 px-4 py-1.5 text-xs font-bold text-white shadow-xs transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>Log New Incident</span>
            </button>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by ID, keyword, description, or location..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-red-500 focus:bg-white focus:outline-none"
              />
            </div>

            {(severityFilter !== 'ALL' ||
              priorityFilter !== 'ALL' ||
              typeFilter !== 'ALL' ||
              statusFilter !== 'ALL' ||
              sourceFilter !== 'ALL' ||
              searchTerm) && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="text-xs text-red-600 hover:underline flex items-center gap-1 font-semibold shrink-0"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 pt-2 border-t border-slate-100 text-xs">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Severity
              </label>
              <select
                value={severityFilter}
                onChange={(e) => {
                  setSeverityFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Priority
              </label>
              <select
                value={priorityFilter}
                onChange={(e) => {
                  setPriorityFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Priorities</option>
                <option value="P1">P1 - Immediate</option>
                <option value="P2">P2 - High</option>
                <option value="P3">P3 - Medium</option>
                <option value="P4">P4 - Low</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Incident Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Types</option>
                <option value="fire">Fire</option>
                <option value="flood">Flood</option>
                <option value="road_accident">Road Accident</option>
                <option value="medical_emergency">Medical Emergency</option>
                <option value="industrial_hazard">Industrial Hazard</option>
                <option value="building_collapse">Building Collapse</option>
                <option value="gas_leak">Gas Leak</option>
                <option value="earthquake">Earthquake</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="REPORTED">Reported</option>
                <option value="VERIFIED">Verified</option>
                <option value="DISPATCHED">Dispatched</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-500 mb-1">
                Source
              </label>
              <select
                value={sourceFilter}
                onChange={(e) => {
                  setSourceFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:border-red-500 focus:outline-none"
              >
                <option value="ALL">All Sources</option>
                <option value="citizen_call">Citizen Call</option>
                <option value="iot_sensor">IoT Sensor</option>
                <option value="field_report">Field Report</option>
                <option value="hospital_alert">Hospital Alert</option>
              </select>
            </div>
          </div>
        </div>

        {/* Incidents Grid Cards */}
        {isLoading ? (
          <div className="flex h-64 w-full items-center justify-center rounded-lg border border-slate-200 bg-white">
            <div className="flex flex-col items-center gap-2 text-slate-500">
              <Loader2 className="h-6 w-6 animate-spin text-red-600" />
              <span className="text-xs font-semibold">Loading Incident Command Database...</span>
            </div>
          </div>
        ) : incidents.length === 0 ? (
          <div className="flex h-64 w-full flex-col items-center justify-center rounded-lg border border-slate-200 bg-white p-6 text-center">
            <Flame className="h-8 w-8 text-slate-400 mb-2" />
            <h3 className="text-sm font-bold text-slate-900">No Incidents Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              No emergency reports match the selected filters. Reset filters or log a new incident.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {incidents.map((inc) => {
              const icon = typeIcons[inc.type] || '🚨';
              const isAnalyzing = analyzingIncidentId === inc.incident_id;
              const isVerifying = verifyingIncidentId === inc.incident_id;
              const isResolving = resolvingIncidentId === inc.incident_id;

              return (
                <div
                  key={inc.incident_id || inc.id || inc._id}
                  className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-2xs hover:shadow-xs transition-all"
                >
                  <div className="space-y-2.5">
                    {/* Top Row: Type, Title, Badges */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{icon}</span>
                        <div>
                          <span className="text-[10px] font-bold text-slate-400 uppercase font-mono block">
                            #{inc.incident_id}
                          </span>
                          <h3 className="text-sm font-bold text-slate-900 line-clamp-1 leading-snug">
                            {inc.title}
                          </h3>
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        <PriorityBadge priority={inc.priority} />
                        <SeverityBadge severity={inc.severity} showPulse={false} />
                      </div>
                    </div>

                    {/* Status & Source Row */}
                    <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-100">
                      <StatusBadge type="status" value={inc.status} />
                      <div className="flex items-center gap-1 text-slate-500 text-[11px]">
                        <Radio className="h-3 w-3 text-slate-400" />
                        <span className="capitalize">{inc.source || 'Citizen Call'}</span>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed bg-slate-50 p-2 rounded border border-slate-100">
                      {inc.description}
                    </p>

                    {/* Location & Time */}
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <div className="flex items-center gap-1 text-slate-700 truncate max-w-[200px]">
                        <MapPin className="h-3 w-3 text-red-600 shrink-0" />
                        <span className="truncate">{inc.address || 'Ahmedabad Sector'}</span>
                      </div>
                      <div className="flex items-center gap-1 font-medium text-slate-400">
                        <Clock className="h-3 w-3" />
                        <span>{new Date(inc.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons Row */}
                  <div className="grid grid-cols-3 gap-1.5 pt-3 mt-3 border-t border-slate-100 text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedIncident(inc);
                        setIsDetailsModalOpen(true);
                      }}
                      className="flex items-center justify-center gap-1 rounded bg-slate-100 hover:bg-slate-200 py-1.5 text-[11px] font-semibold text-slate-700 transition-colors"
                    >
                      <Eye className="h-3 w-3 text-slate-500" />
                      <span>Details</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleAnalyze(inc)}
                      disabled={isAnalyzing}
                      className="flex items-center justify-center gap-1 rounded bg-red-50 hover:bg-red-100 border border-red-200 py-1.5 text-[11px] font-bold text-red-700 transition-colors disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <Loader2 className="h-3 w-3 animate-spin text-red-600" />
                      ) : (
                        <Sparkles className="h-3 w-3 text-red-600" />
                      )}
                      <span>AI Triage</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setDispatchIncident(inc);
                        setIsDispatchModalOpen(true);
                      }}
                      disabled={inc.status === 'RESOLVED' || inc.status === 'CLOSED'}
                      className="flex items-center justify-center gap-1 rounded bg-red-600 hover:bg-red-700 py-1.5 text-[11px] font-bold text-white transition-colors disabled:opacity-40"
                    >
                      <Send className="h-3 w-3" />
                      <span>Dispatch</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 shadow-xs text-xs font-semibold text-slate-700">
            <span>
              Showing Page {page} of {totalPages} ({totalIncidents} total incidents)
            </span>

            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="flex items-center gap-1 rounded border border-slate-200 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Previous</span>
              </button>

              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                className="flex items-center gap-1 rounded border border-slate-200 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Dialog Modals */}
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
          loadData(false);
        }}
      />

      <ReportIncidentModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onCreated={(newInc) => {
          loadData(false);
          setSelectedIncident(newInc);
          setIsDetailsModalOpen(true);
        }}
      />
    </div>
  );
}
