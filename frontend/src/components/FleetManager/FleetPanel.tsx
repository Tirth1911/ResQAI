'use client';

import React, { useState, useMemo } from 'react';
import { Resource, ResourceCategory, ResourceStatus } from '@/types';
import { StatusBadge } from '@/components/StatusBadge';
import { resourceService } from '@/services/resourceService';
import {
  Truck,
  Ambulance,
  Shield,
  Search,
  CheckCircle2,
  RefreshCw,
  Send,
  Zap,
} from 'lucide-react';

interface FleetPanelProps {
  resources: Resource[];
  onResourceUpdated: () => void;
  onSelectResource?: (resource: Resource) => void;
}

export const FleetPanel: React.FC<FleetPanelProps> = ({
  resources,
  onResourceUpdated,
  onSelectResource,
}) => {
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [search, setSearch] = useState('');
  const [releasingId, setReleasingId] = useState<string | null>(null);

  const filteredResources = useMemo(() => {
    return resources.filter((res) => {
      if (categoryFilter !== 'ALL' && res.category !== categoryFilter) return false;
      if (statusFilter !== 'ALL' && res.status !== statusFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchesName = res.name?.toLowerCase().includes(q);
        const matchesId = res.resource_id?.toLowerCase().includes(q);
        const matchesCat = res.category?.toLowerCase().includes(q);
        return matchesName || matchesId || matchesCat;
      }
      return true;
    });
  }, [resources, categoryFilter, statusFilter, search]);

  const handleRelease = async (resourceId: string) => {
    try {
      setReleasingId(resourceId);
      await resourceService.releaseResource(resourceId, 'Command Fleet Dispatcher');
      onResourceUpdated();
    } catch (err) {
      console.error('Failed to release resource:', err);
    } finally {
      setReleasingId(null);
    }
  };

  const availableCount = resources.filter((r) => r.status === 'AVAILABLE').length;
  const busyCount = resources.filter((r) => r.status === 'BUSY' || r.status === 'EN_ROUTE').length;

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Truck className="h-5 w-5 text-emerald-400" />
            <h2 className="font-bold text-white text-base">Fleet & Emergency Units</h2>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-semibold">
              {availableCount} Available
            </span>
            <span className="bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded font-semibold">
              {busyCount} Active
            </span>
          </div>
        </div>

        {/* Search & Category Filter Bar */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter unit by name or ID..."
              className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="p-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Categories</option>
            <option value="AMBULANCE">Ambulance</option>
            <option value="FIRE_TRUCK">Fire Truck</option>
            <option value="POLICE">Police</option>
            <option value="HAZMAT">Hazmat</option>
            <option value="RESCUE_BOAT">Rescue Boat</option>
            <option value="HEAVY_RESCUE">Heavy Rescue</option>
            <option value="DRONE">Drone Recon</option>
          </select>
        </div>
      </div>

      {/* Grid of Resources */}
      <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filteredResources.length === 0 ? (
          <div className="col-span-full text-center py-12 text-slate-500 text-xs font-mono">
            No emergency resources match the selected filter.
          </div>
        ) : (
          filteredResources.map((res) => {
            const isReleasing = releasingId === res.resource_id;
            const isAvailable = res.status === 'AVAILABLE';

            return (
              <div
                key={res.resource_id}
                className="p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-xl space-y-2.5 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-emerald-400">
                      {res.resource_id}
                    </span>
                    <StatusBadge type="resource" value={res.status} />
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-white">{res.name}</h3>
                    <p className="text-[11px] text-slate-400 font-mono">{res.category}</p>
                  </div>

                  {res.current_incident_id && (
                    <div className="text-[10px] font-mono text-amber-400 bg-amber-950/60 p-1.5 rounded border border-amber-900/80">
                      Assigned to: <strong className="text-white">{res.current_incident_id}</strong>
                    </div>
                  )}

                  {res.capabilities && res.capabilities.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {res.capabilities.map((cap, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-900 flex items-center justify-between text-xs">
                  <span className="text-[10px] font-mono text-slate-500">
                    Cap: {res.capacity} crew
                  </span>

                  {!isAvailable && (
                    <button
                      onClick={() => handleRelease(res.resource_id)}
                      disabled={isReleasing}
                      className="px-2.5 py-1 bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-700 rounded text-[11px] font-medium transition-all"
                    >
                      {isReleasing ? 'Releasing...' : 'Release to Pool'}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
