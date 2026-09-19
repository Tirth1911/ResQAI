'use client';

import React, { useState } from 'react';
import { Hospital } from '@/types';
import { Building2, Search, Activity, Phone, Bed, AlertCircle } from 'lucide-react';

interface HospitalPanelProps {
  hospitals: Hospital[];
}

export const HospitalPanel: React.FC<HospitalPanelProps> = ({ hospitals }) => {
  const [search, setSearch] = useState('');

  const filteredHospitals = hospitals.filter((h) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        h.name.toLowerCase().includes(q) ||
        h.hospital_id.toLowerCase().includes(q) ||
        h.address.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalAvailableBeds = hospitals.reduce((acc, h) => acc + (h.available_beds || 0), 0);
  const totalICUBeds = hospitals.reduce((acc, h) => acc + (h.icu_available || 0), 0);

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Building2 className="h-5 w-5 text-blue-400" />
            <h2 className="font-bold text-white text-base">Emergency Medical & Trauma Radar</h2>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded font-semibold">
              {totalAvailableBeds} Beds Free
            </span>
            <span className="bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded font-semibold">
              {totalICUBeds} ICU Free
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search trauma centers, hospitals..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filteredHospitals.length === 0 ? (
          <div className="col-span-full text-center py-12 text-slate-500 text-xs font-mono">
            No hospital centers match query.
          </div>
        ) : (
          filteredHospitals.map((h) => {
            const occupancyPct = Math.round(
              ((h.total_beds - h.available_beds) / Math.max(h.total_beds, 1)) * 100
            );

            return (
              <div
                key={h.hospital_id}
                className="p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-xl space-y-3 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-blue-400">
                      {h.hospital_id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        h.status === 'OPEN'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {h.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-white">{h.name}</h3>
                    <p className="text-[11px] text-slate-400">{h.address}</p>
                  </div>

                  {/* Bed Capacity Metrics */}
                  <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-2 rounded-lg border border-slate-800 text-xs font-mono">
                    <div>
                      <div className="text-[10px] text-slate-500">Available Beds</div>
                      <div className="text-sm font-bold text-emerald-400">
                        {h.available_beds} <span className="text-[10px] text-slate-500">/ {h.total_beds}</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">ICU Available</div>
                      <div className="text-sm font-bold text-cyan-400">{h.icu_available}</div>
                    </div>
                  </div>

                  {/* Capabilities Tags */}
                  <div className="flex flex-wrap gap-1">
                    {h.has_trauma_center && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-800 font-mono">
                        Level 1 Trauma
                      </span>
                    )}
                    {h.has_burn_unit && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-950/80 text-orange-300 border border-orange-800 font-mono">
                        Burn Unit
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-900 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <div className="flex items-center space-x-1 text-[11px]">
                    <Phone className="h-3 w-3 text-slate-500" />
                    <span>{h.contact_phone}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{occupancyPct}% Occupancy</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
