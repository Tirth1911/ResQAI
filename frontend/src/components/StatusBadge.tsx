import React from 'react';
import { IncidentSeverity, IncidentPriority, IncidentStatus, ResourceStatus } from '@/types';

interface StatusBadgeProps {
  type: 'severity' | 'priority' | 'status' | 'resource';
  value: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value }) => {
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  if (type === 'severity') {
    switch (value?.toUpperCase() as IncidentSeverity) {
      case 'CRITICAL':
        colorClasses = 'bg-red-50 text-red-700 border-red-200 font-bold';
        break;
      case 'HIGH':
        colorClasses = 'bg-orange-50 text-orange-700 border-orange-200 font-bold';
        break;
      case 'MEDIUM':
        colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
        break;
      case 'LOW':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium';
        break;
    }
  } else if (type === 'priority') {
    switch (value?.toUpperCase() as IncidentPriority) {
      case 'P1':
        colorClasses = 'bg-red-50 text-red-800 border-red-200 font-bold';
        break;
      case 'P2':
        colorClasses = 'bg-orange-50 text-orange-800 border-orange-200 font-semibold';
        break;
      case 'P3':
        colorClasses = 'bg-amber-50 text-amber-800 border-amber-200 font-medium';
        break;
      case 'P4':
        colorClasses = 'bg-slate-100 text-slate-600 border-slate-200';
        break;
    }
  } else if (type === 'resource') {
    switch (value?.toUpperCase() as ResourceStatus) {
      case 'AVAILABLE':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium';
        break;
      case 'BUSY':
        colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
        break;
      case 'EN_ROUTE':
        colorClasses = 'bg-blue-50 text-blue-700 border-blue-200 font-medium';
        break;
      case 'OFFLINE':
      case 'MAINTENANCE':
        colorClasses = 'bg-slate-100 text-slate-600 border-slate-200';
        break;
    }
  } else if (type === 'status') {
    switch (value?.toUpperCase() as IncidentStatus) {
      case 'REPORTED':
        colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
        break;
      case 'VERIFIED':
        colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
        break;
      case 'DISPATCHED':
        colorClasses = 'bg-purple-50 text-purple-700 border-purple-200';
        break;
      case 'IN_PROGRESS':
        colorClasses = 'bg-indigo-50 text-indigo-700 border-indigo-200';
        break;
      case 'RESOLVED':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
        break;
      case 'CLOSED':
        colorClasses = 'bg-slate-100 text-slate-600 border-slate-200';
        break;
    }
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${colorClasses}`}>
      {value}
    </span>
  );
};

export default StatusBadge;
