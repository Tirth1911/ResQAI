import React from 'react';
import { IncidentPriority } from '@/types';

interface PriorityBadgeProps {
  priority: IncidentPriority | string;
  className?: string;
}

export function PriorityBadge({ priority, className = '' }: PriorityBadgeProps) {
  const norm = (priority || 'P3').toUpperCase();

  const styles: Record<string, { bg: string; text: string; border: string }> = {
    P1: {
      bg: 'bg-rose-500/20',
      text: 'text-rose-400 font-bold',
      border: 'border-rose-500/50',
    },
    P2: {
      bg: 'bg-amber-500/20',
      text: 'text-amber-400 font-semibold',
      border: 'border-amber-500/50',
    },
    P3: {
      bg: 'bg-sky-500/20',
      text: 'text-sky-300 font-medium',
      border: 'border-sky-500/40',
    },
    P4: {
      bg: 'bg-slate-800',
      text: 'text-slate-400 font-medium',
      border: 'border-slate-700',
    },
  };

  const current = styles[norm] || styles.P3;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border uppercase tracking-wider ${current.bg} ${current.text} ${current.border} ${className}`}
    >
      {norm}
    </span>
  );
}

export default PriorityBadge;
