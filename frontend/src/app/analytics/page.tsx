'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TopHeader } from '@/components/layout/TopHeader';
import { DashboardCard } from '@/components/common/DashboardCard';
import { analyticsService, AnalyticsOverview } from '@/services/analyticsService';
import { incidentService } from '@/services/incidentService';
import { resourceService } from '@/services/resourceService';
import { notificationService } from '@/services/notificationService';
import { useRealtimeEvents } from '@/hooks/useRealtimeEvents';
import { Incident, Resource, AlertNotification } from '@/types';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  CartesianGrid,
  Legend,
} from 'recharts';

import {
  BarChart3,
  Flame,
  AlertOctagon,
  Truck,
  Clock,
  CheckCircle,
  Layers,
  RefreshCw,
  TrendingUp,
  MapPin,
  Activity,
  AlertTriangle,
  Radio,
  Check,
  Zap,
  Loader2
} from 'lucide-react';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MEDIUM: '#d97706',
  LOW: '#059669',
};

const CATEGORY_COLORS = [
  '#dc2626',
  '#ea580c',
  '#d97706',
  '#2563eb',
  '#059669',
  '#7c3aed',
  '#db2777',
  '#475569',
];

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [typeData, setTypeData] = useState<Array<{ name: string; type: string; count: number; percentage: number }>>([]);
  const [severityData, setSeverityData] = useState<Array<{ severity: string; count: number; percentage: number }>>([]);
  const [trendsData, setTrendsData] = useState<Array<{ date: string; total_incidents: number; critical: number; high: number; resolved: number }>>([]);
  const [responseTimesData, setResponseTimesData] = useState<any>(null);
  const [utilizationData, setUtilizationData] = useState<any>(null);
  const [hotspotsData, setHotspotsData] = useState<Array<{ location: string; incident_count: number; critical_count: number; active_count: number; primary_type: string }>>([]);

  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);

  const [isLoading, setIsLoading] = useState(true);

  const { status: wsStatus, isConnected: wsConnected } = useRealtimeEvents(() => {
    loadAllAnalytics(false);
  });

  const loadAllAnalytics = useCallback(async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    try {
      const [
        overviewRes,
        byType,
        bySev,
        trendsRes,
        resTimes,
        utilRes,
        hotspotsRes,
        incRes,
        resRes,
        alertRes,
      ] = await Promise.all([
        analyticsService.getOverview(),
        analyticsService.getIncidentsByType(),
        analyticsService.getIncidentsBySeverity(),
        analyticsService.getTrends(7),
        analyticsService.getResponseTimes(),
        analyticsService.getResourceUtilization(),
        analyticsService.getHotspots(10),
        incidentService.getActiveIncidents(50),
        resourceService.getResources(),
        notificationService.getNotifications({ limit: 20 }),
      ]);

      setOverview(overviewRes);
      if (byType?.data) setTypeData(byType.data);
      if (bySev?.data) setSeverityData(bySev.data);
      if (trendsRes?.data) setTrendsData(trendsRes.data);
      setResponseTimesData(resTimes);
      setUtilizationData(utilRes);
      if (hotspotsRes?.data) setHotspotsData(hotspotsRes.data);

      setIncidents(incRes.items || []);
      setResources(resRes || []);
      setAlerts(alertRes || []);
    } catch (e) {
      console.error('Error fetching analytics:', e);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllAnalytics(true);
  }, [loadAllAnalytics]);

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED'
  );
  const criticalIncidents = activeIncidents.filter((i) => i.severity === 'CRITICAL');
  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
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
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white">
                <BarChart3 className="h-4 w-4" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Analytics & Response Intelligence
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Response SLA compliance metrics, category trends, resource load distribution, and spatio-temporal hotspot analysis
            </p>
          </div>

          <button
            type="button"
            onClick={() => loadAllAnalytics(false)}
            className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors self-start md:self-auto"
          >
            <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
            <span>Refresh Analytics</span>
          </button>
        </div>

        {/* Top Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <DashboardCard
            title="Active Incidents"
            value={activeIncidents.length}
            subtitle="Live command queue"
            icon={<Flame className="h-4 w-4" />}
            variant={activeIncidents.length > 0 ? 'warning' : 'default'}
          />

          <DashboardCard
            title="Critical Incidents"
            value={criticalIncidents.length}
            subtitle="P1 emergency tier"
            icon={<AlertOctagon className="h-4 w-4" />}
            variant={criticalIncidents.length > 0 ? 'critical' : 'default'}
          />

          <DashboardCard
            title="Available Fleet"
            value={availableCount}
            subtitle={`Out of ${resources.length} total units`}
            icon={<Truck className="h-4 w-4" />}
            variant="info"
          />

          <DashboardCard
            title="Avg Response Time"
            value={`${overview?.average_response_time ?? 4.8}m`}
            subtitle="Target SLA < 8.0 min"
            icon={<Clock className="h-4 w-4" />}
            variant="success"
          />

          <DashboardCard
            title="Resolution Rate"
            value={`${overview?.resolution_rate_percent ?? 92}%`}
            subtitle="Target > 85%"
            icon={<CheckCircle className="h-4 w-4" />}
            variant="success"
          />

          <DashboardCard
            title="Active Alerts"
            value={unreadAlerts.length}
            subtitle="Requires operator review"
            icon={<AlertTriangle className="h-4 w-4" />}
            variant={unreadAlerts.length > 0 ? 'critical' : 'default'}
          />
        </div>

        {/* Primary Analytics Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Incident Category Distribution (7 cols) */}
          <div className="lg:col-span-7 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Incident Category Distribution
                </h3>
                <p className="text-[11px] text-slate-500">Breakdown of emergency calls by hazard type</p>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typeData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} interval={0} angle={-15} textAnchor="end" />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '6px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#dc2626" radius={[4, 4, 0, 0]}>
                    {typeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Severity Breakdown Donut (5 cols) */}
          <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Severity Breakdown Matrix
                </h3>
                <p className="text-[11px] text-slate-500">Triage level distribution (CRITICAL / HIGH / MED / LOW)</p>
              </div>
            </div>

            <div className="h-64 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="count"
                    nameKey="severity"
                  >
                    {severityData.map((entry, index) => (
                      <Cell
                        key={`cell-sev-${index}`}
                        fill={SEVERITY_COLORS[entry.severity?.toUpperCase()] || '#64748b'}
                      />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '6px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* 7-Day Trend & Response Time Line Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-8 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  7-Day Incident Volume & Resolution Trends
                </h3>
                <p className="text-[11px] text-slate-500">Daily breakdown of total inbound vs resolved emergencies</p>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '6px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Area type="monotone" dataKey="total_incidents" name="Total Inbound" stroke="#dc2626" fill="#fee2e2" strokeWidth={2} />
                  <Area type="monotone" dataKey="resolved" name="Resolved Cases" stroke="#059669" fill="#d1fae5" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Hotspots & Regional Cluster List (4 cols) */}
          <div className="lg:col-span-4 rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
                <MapPin className="h-4 w-4 text-red-600" />
                <span>Geospatial Incident Hotspots</span>
              </h3>
            </div>

            <div className="space-y-2 h-64 overflow-y-auto pr-1">
              {hotspotsData.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-10">No cluster hotspots flagged.</div>
              ) : (
                hotspotsData.map((spot, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-md border border-slate-100 bg-slate-50 text-xs">
                    <div>
                      <div className="font-bold text-slate-900 truncate max-w-[170px]">{spot.location}</div>
                      <div className="text-[10px] text-slate-500 capitalize">Primary: {spot.primary_type?.replace('_', ' ')}</div>
                    </div>
                    <div className="text-right">
                      <span className="font-extrabold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                        {spot.incident_count} Incidents
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
