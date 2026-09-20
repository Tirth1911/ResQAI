'use client';

import React, { useState } from 'react';
import { Resource, ResourceKind, ResourceStatus } from '../types';
import { Truck, Shield, Flame, Activity, Anchor, Radio, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface FleetGridProps {
  resources: Resource[];
  onToggleStatus: (resourceId: string, newStatus: ResourceStatus) => void;
}

export default function FleetGrid({ resources, onToggleStatus }: FleetGridProps) {
  const [kindFilter, setKindFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredResources = resources.filter(res => {
    if (kindFilter !== 'all' && res.kind !== kindFilter) return false;
    if (statusFilter !== 'all' && res.status !== statusFilter) return false;
    return true;
  });

  const getKindBadge = (kind: ResourceKind) => {
    switch (kind) {
      case 'fire_truck':
        return <span className="flex items-center gap-1 text-[#B42318] bg-[#FDECEC] px-2 py-0.5 rounded font-semibold">🚒 Fire Engine</span>;
      case 'ambulance':
        return <span className="flex items-center gap-1 text-[#16803C] bg-[#EAF6ED] px-2 py-0.5 rounded font-semibold">🚑 108 ALS Ambulance</span>;
      case 'police_van':
        return <span className="flex items-center gap-1 text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded font-semibold">🚓 PCR Patrol</span>;
      case 'hazmat_unit':
        return <span className="flex items-center gap-1 text-[#7C3AED] bg-[#F3E8FF] px-2 py-0.5 rounded font-semibold">☣️ HAZMAT Decon</span>;
      case 'rescue_boat':
        return <span className="flex items-center gap-1 text-[#0284C7] bg-[#E0F2FE] px-2 py-0.5 rounded font-semibold">🚤 Rescue Boat</span>;
      case 'ndrf_team':
        return <span className="flex items-center gap-1 text-[#D97706] bg-[#FEF3C7] px-2 py-0.5 rounded font-semibold">🛟 NDRF Team</span>;
      case 'drone':
        return <span className="flex items-center gap-1 text-[#0891B2] bg-[#CFFAFE] px-2 py-0.5 rounded font-semibold">🛸 Recon Drone</span>;
      default:
        return <span>Emergency Asset</span>;
    }
  };

  return (
    <div className="max-w-[1700px] mx-auto p-6 space-y-6 text-[#1F2933] font-sans">
      
      {/* Fleet Header Controls */}
      <div className="bg-white border border-[#DED8CC] p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-[#FDECEC] text-[#B42318] rounded-xl border border-[#FCA5A5]">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1F2933]">Emergency Response Fleet Grid</h2>
            <p className="text-xs text-[#667085]">Gujarat Sector Tactical Grid • {resources.length} Monitored Units</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-[#667085] font-semibold">
            <span>ASSET CLASS:</span>
          </div>
          <select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318]"
          >
            <option value="all">All Asset Classes</option>
            <option value="fire_truck">Fire Truck / Foam Tender</option>
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
            className="px-3 py-1.5 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:outline-none focus:ring-2 focus:ring-[#B42318]"
          >
            <option value="all">All Statuses</option>
            <option value="available">Available</option>
            <option value="dispatched">Dispatched / En Route</option>
            <option value="on_scene">On Scene</option>
            <option value="maintenance">Maintenance</option>
          </select>
        </div>
      </div>

      {/* Resource Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredResources.map((res) => (
          <div
            key={res.id}
            className="bg-white border border-[#DED8CC] p-5 rounded-xl shadow-xs flex flex-col justify-between gap-4 transition-all hover:border-[#B42318]/40"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px]">
                  {getKindBadge(res.kind)}
                </span>
                <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full ${
                  res.status === 'available' ? 'bg-[#EAF6ED] text-[#16803C] border border-[#A7F3D0]' :
                  res.status === 'dispatched' ? 'bg-[#FEF6E7] text-[#C47A00] border border-[#FDE68A]' :
                  'bg-[#F5F1E8] text-[#667085]'
                }`}>
                  {res.status}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-[#1F2933] text-sm leading-snug">{res.name}</h3>
                <p className="text-[#667085] text-xs">{res.station}</p>
              </div>

              <div className="bg-[#F5F1E8] p-3 rounded-lg border border-[#DED8CC] text-[11px] space-y-1.5 text-[#1F2933]">
                <div className="flex justify-between">
                  <span className="text-[#667085]">Personnel Capacity:</span>
                  <span className="font-bold">{res.capacity} Responders</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#667085]">Coordinates:</span>
                  <span className="font-mono">{res.lat.toFixed(4)}, {res.lng.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#667085]">Capabilities:</span>
                  <span className="text-[#B42318] uppercase font-bold">{res.capabilities.join(', ')}</span>
                </div>
              </div>
            </div>

            {/* Quick Status Action Buttons */}
            <div className="pt-2 border-t border-[#DED8CC] flex items-center justify-between text-xs">
              <span className="text-[10px] text-[#667085]">Action:</span>
              
              {res.status === 'available' ? (
                <button
                  onClick={() => onToggleStatus(res.id, 'maintenance')}
                  className="px-3 py-1.5 bg-[#F5F1E8] hover:bg-[#EDE8DD] text-[#1F2933] rounded-lg text-xs font-semibold border border-[#DED8CC]"
                >
                  Mark Maintenance
                </button>
              ) : (
                <button
                  onClick={() => onToggleStatus(res.id, 'available')}
                  className="px-3 py-1.5 bg-[#16803C] hover:bg-[#126730] text-white rounded-lg text-xs font-bold transition-colors"
                >
                  Set Available
                </button>
              )}
            </div>

          </div>
        ))}
      </div>

    </div>
  );
}
