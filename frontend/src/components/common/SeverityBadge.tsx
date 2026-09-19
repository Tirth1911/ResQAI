import React from 'react';
import { IncidentSeverity } from '@/types';

interface SeverityBadgeProps {
  severity: IncidentSeverity | string;
  className?: string;
  showPulse?: boolean;
}

export function SeverityBadge({
  severity,
  className = '',
  showPulse = true,
}: SeverityBadgeProps) {
  const norm = (severity || 'LOW').toUpperCase();

  const styles: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    CRITICAL: {
      bg: 'bg-red-50',
      text: 'text-red-700 font-bold',
      border: 'border-red-200',
      dot: 'bg-red-600',
    },
    HIGH: {
      bg: 'bg-orange-50',
      text: 'text-orange-700 font-bold',
      border: 'border-orange-200',
      dot: 'bg-orange-500',
    },
    MEDIUM: {
      bg: 'bg-amber-50',
      text: 'text-amber-700 font-semibold',
      border: 'border-amber-200',
      dot: 'bg-amber-500',
    },
    LOW: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-700 font-semibold',
      border: 'border-emerald-200',
      dot: 'bg-emerald-500',
    },
  };

  const current = styles[norm] || styles.LOW;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs border tracking-wide uppercase ${current.bg} ${current.text} ${current.border} ${className}`}
    >
      <span className="relative flex h-2 w-2">
        {showPulse && (norm === 'CRITICAL' || norm === 'HIGH') && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${current.dot}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${current.dot}`} />
      </span>
      {norm}
    </span>
  );
}

export default SeverityBadge;
