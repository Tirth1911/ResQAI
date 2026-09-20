'use client';

import React from 'react';
import { Resource } from '@/types';
import { Truck, MapPin, CheckCircle, Clock, AlertTriangle, Shield, Activity } from 'lucide-react';

interface ResourceCardProps {
  resource: Resource;
  onAssign?: (resource: Resource) => void;
  onRelease?: (resource: Resource) => void;
  onSelect?: (resource: Resource) => void;
  onEdit?: (resource: Resource) => void;
  onStatusChange?: (status: string) => void | Promise<void>;
  isSelected?: boolean;
}

const CATEGORY_ICONS: Record<string, string> = {
  AMBULANCE: '🚑',
  ambulance: '🚑',
  FIRE_TRUCK: '🚒',
  fire_truck: '🚒',
  POLICE: '🚓',
  police: '🚓',
  RESCUE_BOAT: '🚤',
  rescue_boat: '🚤',
  rescue_team: '🚤',
  HAZMAT: '☣️',
  hazmat: '☣️',
  HEAVY_RESCUE: '🏗️',
  DRONE: '🛸',
  drone: '🛸',
  HELICOPTER: '🚁',
  OTHER: '🚚',
};

export function ResourceCard({
  resource,
  onAssign,
  onRelease,
  onSelect,
  onEdit,
  isSelected = false,
}: ResourceCardProps) {
  const categoryKey = (resource.category || (resource as any).type || 'OTHER').toUpperCase();
  const icon = CATEGORY_ICONS[resource.category] || CATEGORY_ICONS[categoryKey] || '🚚';
  const status = (resource.status || 'AVAILABLE').toUpperCase();

  const isAvailable = status === 'AVAILABLE';
  const isBusy = status === 'BUSY' || status === 'EN_ROUTE' || status === 'ON_SCENE';
  const isOffline = status === 'OFFLINE' || status === 'MAINTENANCE';

  return (
    <div
      onClick={() => onSelect?.(resource)}
      className={`rounded-xl border bg-white p-4 transition-all duration-200 cursor-pointer shadow-xs hover:shadow-md hover:border-slate-300 ${
        isSelected ? 'border-red-500 ring-2 ring-red-100' : 'border-slate-200'
      }`}
    >
      {/* Top row: Icon, Name, Status */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-xl border border-slate-200 shrink-0">
            {icon}
          </div>
          <div>
            <h4 className="font-bold text-slate-900 text-sm leading-tight">{resource.name}</h4>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="font-mono text-[10px] font-bold text-slate-400">
                #{resource.resource_id}
              </span>
              <span className="text-[11px] text-slate-500 capitalize">
                {(resource.category || (resource as any).type || '').replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${
            isAvailable
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : isBusy
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-slate-100 text-slate-600 border-slate-200'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isAvailable ? 'bg-emerald-500 animate-pulse' : isBusy ? 'bg-amber-500' : 'bg-slate-400'
            }`}
          />
          {status}
        </span>
      </div>

      {/* Capabilities */}
      <div className="mt-3 flex flex-wrap gap-1">
        {(resource.capabilities || []).slice(0, 4).map((cap, i) => (
          <span
            key={i}
            className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-medium"
          >
            {cap.replace(/_/g, ' ')}
          </span>
        ))}
        {(resource.capabilities || []).length > 4 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-slate-50 text-slate-400 font-medium">
            +{(resource.capabilities || []).length - 4}
          </span>
        )}
      </div>

      {/* Location / Station Info */}
      <div className="mt-2.5 flex items-center gap-1.5 text-[11px] text-slate-500">
        <MapPin className="h-3 w-3 text-red-400 shrink-0" />
        <span className="truncate">{resource.location?.address || 'Sector 1 Command Station'}</span>
      </div>

      {/* Footer / Assignment Info & Action Buttons */}
      <div className="mt-3.5 flex items-center justify-between border-t border-slate-100 pt-2.5 text-xs">
        {resource.current_incident_id || (resource as any).assigned_incident_id ? (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 text-[11px]">Assigned:</span>
            <span className="font-mono text-red-600 text-[11px] font-bold bg-red-50 px-1.5 py-0.5 rounded border border-red-200">
              #{resource.current_incident_id || (resource as any).assigned_incident_id}
            </span>
          </div>
        ) : (
          <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Ready for dispatch
          </span>
        )}

        <div className="flex items-center gap-1.5">
          {onEdit && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(resource);
              }}
              className="text-[11px] font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Edit
            </button>
          )}

          {isBusy && onRelease && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRelease(resource);
              }}
              className="text-[11px] font-bold px-2.5 py-1 rounded bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 transition-colors"
            >
              Release
            </button>
          )}

          {isAvailable && onAssign && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onAssign(resource);
              }}
              className="text-[11px] font-bold px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white transition-colors shadow-2xs"
            >
              Dispatch
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResourceCard;
