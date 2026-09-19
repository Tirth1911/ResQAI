'use client';

import React from 'react';
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
  CartesianGrid,
  Legend,
} from 'recharts';

interface ChartDataPoint {
  name: string;
  value?: number;
  count?: number;
  [key: string]: any;
}

interface AnalyticsChartProps {
  title: string;
  type: 'bar' | 'pie' | 'line' | 'donut';
  data: ChartDataPoint[];
  dataKey?: string;
  nameKey?: string;
  colors?: string[];
  height?: number;
  subtitle?: string;
}

const DEFAULT_COLORS = ['#ef4444', '#f97316', '#eab308', '#06b6d4', '#10b981', '#8b5cf6', '#ec4899'];

export function AnalyticsChart({
  title,
  type,
  data,
  dataKey = 'count',
  nameKey = 'name',
  colors = DEFAULT_COLORS,
  height = 240,
  subtitle,
}: AnalyticsChartProps) {
  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border border-slate-700 bg-slate-900/95 p-2.5 shadow-xl backdrop-blur-md text-xs font-mono">
          <p className="font-semibold text-white mb-1">{payload[0]?.payload?.[nameKey] || label}</p>
          <p className="text-cyan-400">
            {payload[0].name || dataKey}: <span className="font-bold">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 backdrop-blur-md">
      <div className="mb-3">
        <h4 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
          {title}
        </h4>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div style={{ width: '100%', height }}>
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-xs text-slate-500 font-mono">
            No telemetry data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {type === 'bar' ? (
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey={nameKey}
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip content={customTooltip} />
                <Bar dataKey={dataKey} fill="#06b6d4" radius={[4, 4, 0, 0]}>
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Bar>
              </BarChart>
            ) : type === 'pie' || type === 'donut' ? (
              <PieChart>
                <Tooltip content={customTooltip} />
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={type === 'donut' ? 45 : 0}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey={dataKey}
                  nameKey={nameKey}
                >
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Legend
                  wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
                  iconSize={8}
                />
              </PieChart>
            ) : (
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey={nameKey} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip content={customTooltip} />
                <Line
                  type="monotone"
                  dataKey={dataKey}
                  stroke="#06b6d4"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#06b6d4' }}
                  activeDot={{ r: 5, fill: '#38bdf8' }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default AnalyticsChart;
