import React from 'react';

interface DashboardCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string | number;
    isPositive?: boolean;
    label?: string;
  };
  variant?: 'default' | 'critical' | 'warning' | 'info' | 'success';
  className?: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
}

export function DashboardCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
  className = '',
  children,
  action,
}: DashboardCardProps) {
  const variantStyles = {
    default: 'border-slate-200 bg-white shadow-2xs',
    critical: 'border-red-200 bg-red-50/50 shadow-2xs',
    warning: 'border-amber-200 bg-amber-50/50 shadow-2xs',
    info: 'border-blue-200 bg-blue-50/50 shadow-2xs',
    success: 'border-emerald-200 bg-emerald-50/50 shadow-2xs',
  };

  const textAccent = {
    default: 'text-slate-600 bg-slate-100',
    critical: 'text-red-700 bg-red-100',
    warning: 'text-amber-700 bg-amber-100',
    info: 'text-blue-700 bg-blue-100',
    success: 'text-emerald-700 bg-emerald-100',
  };

  return (
    <div
      className={`relative overflow-hidden rounded-lg border p-3.5 transition-all duration-200 hover:shadow-xs ${variantStyles[variant]} ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {icon && <div className={`p-1.5 rounded-md ${textAccent[variant]}`}>{icon}</div>}
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{title}</p>
        </div>
        {action && <div>{action}</div>}
      </div>

      {value !== undefined && (
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold tracking-tight text-slate-900">{value}</span>
          {trend && (
            <span
              className={`text-xs font-semibold ${
                trend.isPositive ? 'text-emerald-700' : 'text-red-700'
              }`}
            >
              {trend.isPositive ? '↑' : '↓'} {trend.value} {trend.label}
            </span>
          )}
        </div>
      )}

      {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}

      {children && <div className="mt-2">{children}</div>}
    </div>
  );
}

export default DashboardCard;
