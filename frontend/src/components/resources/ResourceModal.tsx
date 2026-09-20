'use client';

import React, { useState, useEffect } from 'react';
import { Resource } from '@/types';
import { resourceService, CreateResourcePayload } from '@/services/resourceService';
import {
  X,
  Truck,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Save,
  Loader2,
  Shield,
  Layers,
} from 'lucide-react';

interface ResourceModalProps {
  isOpen: boolean;
  mode: 'create' | 'edit' | 'view';
  resource?: Resource | null;
  onClose: () => void;
  onSaved?: (resource: Resource) => void;
  onSave?: (resourceData: any) => Promise<void> | void;
  onReleased?: (resourceId: string) => void;
}

const DEFAULT_CAPABILITIES = [
  'advanced_life_support',
  'basic_life_support',
  'fire_suppression',
  'high_rise_ladder',
  'hazmat_containment',
  'water_rescue',
  'heavy_extrication',
  'aerial_recon',
  'thermal_imaging',
  'traffic_control',
];

export function ResourceModal({
  isOpen,
  mode,
  resource,
  onClose,
  onSaved,
  onSave,
  onReleased,
}: ResourceModalProps) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('AMBULANCE');
  const [status, setStatus] = useState('AVAILABLE');
  const [capacity, setCapacity] = useState(4);
  const [latitude, setLatitude] = useState<number | string>(23.0225);
  const [longitude, setLongitude] = useState<number | string>(72.5714);
  const [address, setAddress] = useState('Central Emergency Depot, Ahmedabad');
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([
    'advanced_life_support',
  ]);
  const [customCapability, setCustomCapability] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (resource && (mode === 'edit' || mode === 'view')) {
      setName(resource.name || '');
      setCategory(resource.category || 'AMBULANCE');
      setStatus(resource.status || 'AVAILABLE');
      setCapacity(resource.capacity || 4);
      setSelectedCapabilities(resource.capabilities || []);
      setAddress(resource.location?.address || 'Ahmedabad Sector Depot');
      if (resource.location?.coordinates && resource.location.coordinates.length >= 2) {
        setLongitude(resource.location.coordinates[0]);
        setLatitude(resource.location.coordinates[1]);
      }
    } else if (mode === 'create') {
      setName('');
      setCategory('AMBULANCE');
      setStatus('AVAILABLE');
      setCapacity(4);
      setLatitude(23.0225);
      setLongitude(72.5714);
      setAddress('Central Emergency Depot, Ahmedabad');
      setSelectedCapabilities(['advanced_life_support']);
    }
  }, [resource, mode, isOpen]);

  if (!isOpen) return null;

  const toggleCapability = (cap: string) => {
    if (mode === 'view') return;
    if (selectedCapabilities.includes(cap)) {
      setSelectedCapabilities(selectedCapabilities.filter((c) => c !== cap));
    } else {
      setSelectedCapabilities([...selectedCapabilities, cap]);
    }
  };

  const handleAddCustomCapability = () => {
    if (customCapability.trim() && !selectedCapabilities.includes(customCapability.trim())) {
      setSelectedCapabilities([...selectedCapabilities, customCapability.trim()]);
      setCustomCapability('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'view') return;
    setIsLoading(true);

    try {
      const payload: any = {
        name,
        category,
        capabilities: selectedCapabilities,
        status,
        capacity: Number(capacity),
        location: {
          latitude: Number(latitude),
          longitude: Number(longitude),
          address,
        },
      };

      if (onSave) {
        await onSave(payload);
      } else if (mode === 'create') {
        const created = await resourceService.createResource(payload);
        onSaved?.(created);
      } else if (mode === 'edit' && resource) {
        const updated = await resourceService.updateResource(resource.resource_id, payload);
        onSaved?.(updated);
      }
      onClose();
    } catch (err: any) {
      console.error('Failed to save resource:', err);
      alert('Error saving resource: ' + (err.message || 'Please check inputs.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRelease = async () => {
    if (!resource) return;
    setIsLoading(true);
    try {
      await resourceService.releaseResource(resource.resource_id, 'Command Center');
      onReleased?.(resource.resource_id);
      onClose();
    } catch (err: any) {
      console.error('Failed to release resource:', err);
      alert('Error releasing resource: ' + (err.message || 'Failed.'));
    } finally {
      setIsLoading(false);
    }
  };

  const isView = mode === 'view';

  return (
    <div className="fixed inset-0 z-[2500] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden my-6 flex flex-col max-h-[90vh] text-xs text-slate-800">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-600 text-white shadow-xs">
              <Truck className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 leading-tight">
                {mode === 'create'
                  ? 'Register Tactical Emergency Unit'
                  : mode === 'edit'
                  ? `Edit Unit: ${resource?.name || resource?.resource_id}`
                  : `Unit Profile: ${resource?.name || resource?.resource_id}`}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Fleet dispatcher registry and capability indexing
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-4">
          {/* Unit Name & Category */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-bold text-[11px] mb-1">
                Unit Call Sign / Name *
              </label>
              <input
                type="text"
                required
                disabled={isView}
                placeholder="E.g., 108 Ambulance Unit - Paldi"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-red-500 focus:bg-white focus:outline-none disabled:opacity-70"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-bold text-[11px] mb-1">
                Unit Category *
              </label>
              <select
                disabled={isView}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-red-500 focus:bg-white focus:outline-none disabled:opacity-70"
              >
                <option value="AMBULANCE">Ambulance</option>
                <option value="FIRE_TRUCK">Fire Truck</option>
                <option value="POLICE">Police Patrol</option>
                <option value="HAZMAT">Hazmat Team</option>
                <option value="RESCUE_BOAT">Rescue Boat</option>
                <option value="HEAVY_RESCUE">Heavy Rescue / Crane</option>
                <option value="DRONE">Drone Recon</option>
                <option value="HELICOPTER">Helicopter</option>
                <option value="OTHER">Other Support Unit</option>
              </select>
            </div>
          </div>

          {/* Operational Status & Capacity */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-bold text-[11px] mb-1">
                Readiness Status
              </label>
              <select
                disabled={isView}
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-red-500 focus:bg-white focus:outline-none disabled:opacity-70"
              >
                <option value="AVAILABLE">AVAILABLE (Armed & Ready)</option>
                <option value="BUSY">BUSY (Dispatched on Scene)</option>
                <option value="EN_ROUTE">EN_ROUTE (Transit to Incident)</option>
                <option value="OFFLINE">OFFLINE (Off Shift / Standby)</option>
                <option value="MAINTENANCE">MAINTENANCE (Depot Repair)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 font-bold text-[11px] mb-1">
                Crew / Transport Capacity
              </label>
              <input
                type="number"
                min={1}
                max={50}
                disabled={isView}
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-red-500 focus:bg-white focus:outline-none disabled:opacity-70"
              />
            </div>
          </div>

          {/* Location & Depot */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-2.5">
            <span className="text-[11px] font-bold text-slate-800 flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-red-500" />
              <span>Base Station & Geospatial Coordinates</span>
            </span>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-500 text-[10px] font-semibold mb-0.5">Latitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  disabled={isView}
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none disabled:opacity-70"
                />
              </div>

              <div>
                <label className="block text-slate-500 text-[10px] font-semibold mb-0.5">Longitude</label>
                <input
                  type="number"
                  step="any"
                  required
                  disabled={isView}
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none disabled:opacity-70"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-500 text-[10px] font-semibold mb-0.5">Station / Address</label>
              <input
                type="text"
                disabled={isView}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none disabled:opacity-70"
              />
            </div>
          </div>

          {/* Capabilities Selector */}
          <div>
            <label className="block text-slate-700 font-bold text-[11px] mb-1.5">
              Certified Unit Capabilities
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {DEFAULT_CAPABILITIES.map((cap) => {
                const isSelected = selectedCapabilities.includes(cap);
                return (
                  <button
                    key={cap}
                    type="button"
                    disabled={isView}
                    onClick={() => toggleCapability(cap)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                      isSelected
                        ? 'bg-red-50 text-red-700 border border-red-200 font-bold'
                        : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
                    }`}
                  >
                    {isSelected ? '✓ ' : '+ '}
                    {cap.replace(/_/g, ' ')}
                  </button>
                );
              })}
            </div>

            {!isView && (
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add custom capability..."
                  value={customCapability}
                  onChange={(e) => setCustomCapability(e.target.value)}
                  className="flex-1 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddCustomCapability}
                  className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold"
                >
                  Add
                </button>
              </div>
            )}
          </div>

          {/* Current Assignment Callout if applicable */}
          {resource?.current_incident_id && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 flex items-center justify-between text-xs">
              <div>
                <span className="text-amber-800 font-bold block">Currently Dispatched</span>
                <span className="text-slate-600 font-mono">Incident ID: #{resource.current_incident_id}</span>
              </div>
              <button
                type="button"
                onClick={handleRelease}
                disabled={isLoading}
                className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs transition-colors"
              >
                Release Unit Now
              </button>
            </div>
          )}

          {/* Modal Footer Controls */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold"
              >
                {isView ? 'Close' : 'Cancel'}
              </button>

              {resource && resource.status !== 'AVAILABLE' && (
                <button
                  type="button"
                  onClick={handleRelease}
                  disabled={isLoading}
                  className="px-3.5 py-2 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-semibold border border-amber-200 transition-colors"
                >
                  Release to Pool
                </button>
              )}
            </div>

            {!isView && (
              <button
                type="submit"
                disabled={isLoading}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs transition-all shadow-xs disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-3.5 w-3.5" />
                    <span>{mode === 'create' ? 'Register Unit' : 'Save Changes'}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

export default ResourceModal;
