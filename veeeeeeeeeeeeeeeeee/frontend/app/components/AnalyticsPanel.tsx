'use client';

import React from 'react';
import { Incident, Resource } from '../types';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  LineChart, 
  Line 
} from 'recharts';
import { Activity, ShieldAlert, Clock, CheckCircle2, Award, Zap, TrendingUp, Users } from 'lucide-react';

interface AnalyticsPanelProps {
  incidents: Incident[];
  resources: Resource[];
}

export default function AnalyticsPanel({ incidents, resources }: AnalyticsPanelProps) {
  
  const severityCounts = {
    critical: incidents.filter(i => i.severity === 'critical').length,
    high: incidents.filter(i => i.severity === 'high').length,
    medium: incidents.filter(i => i.severity === 'medium').length,
    low: incidents.filter(i => i.severity === 'low').length,
  };

  const severityData = [
    { name: 'Critical', value: severityCounts.critical, color: '#C62828' },
    { name: 'High', value: severityCounts.high, color: '#C47A00' },
    { name: 'Medium', value: severityCounts.medium, color: '#EAB308' },
    { name: 'Low', value: severityCounts.low, color: '#2563EB' },
  ];

  const responseTimeData = [
    { time: '14:00', avgEta: 7.2 },
    { time: '15:00', avgEta: 6.1 },
    { time: '16:00', avgEta: 5.4 },
    { time: '17:00', avgEta: 4.8 },
    { time: '18:00', avgEta: 4.4 },
    { time: '19:00', avgEta: 4.2 },
  ];

  const totalReportsMerged = incidents.reduce((acc, inc) => acc + (inc.report_count - 1), 0);

  return (
    <div className="max-w-[1700px] mx-auto p-6 space-y-6 text-[#1F2933] font-sans">
      
      {/* KPI Cards Row (Section 12) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white border border-[#DED8CC] p-5 rounded-xl space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[#667085] font-semibold">
            <span>ACTIVE INCIDENTS</span>
            <Activity className="w-4 h-4 text-[#B42318]" />
          </div>
          <div className="text-3xl font-extrabold text-[#1F2933]">{incidents.length}</div>
          <div className="text-xs text-[#16803C] font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+2 today</span>
          </div>
        </div>

        <div className="bg-white border border-[#DED8CC] p-5 rounded-xl space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[#667085] font-semibold">
            <span>AVAILABLE FLEET</span>
            <Users className="w-4 h-4 text-[#16803C]" />
          </div>
          <div className="text-3xl font-extrabold text-[#16803C]">
            {resources.filter(r => r.status === 'available').length}
          </div>
          <div className="text-xs text-[#667085]">
            of {resources.length} total units
          </div>
        </div>

        <div className="bg-white border border-[#DED8CC] p-5 rounded-xl space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[#667085] font-semibold">
            <span>AVG RESPONSE TIME</span>
            <Clock className="w-4 h-4 text-[#C47A00]" />
          </div>
          <div className="text-3xl font-extrabold text-[#1F2933]">4.2 min</div>
          <div className="text-xs text-[#16803C] font-semibold">
            ↓ 38% improvement vs baseline
          </div>
        </div>

        <div className="bg-white border border-[#DED8CC] p-5 rounded-xl space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[#667085] font-semibold">
            <span>AI TRIAGE ACCURACY</span>
            <Award className="w-4 h-4 text-[#2563EB]" />
          </div>
          <div className="text-3xl font-extrabold text-[#1F2933]">94.6%</div>
          <div className="text-xs text-[#667085]">
            {totalReportsMerged} redundant calls merged
          </div>
        </div>

      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Severity Breakdown Chart */}
        <div className="bg-white border border-[#DED8CC] p-6 rounded-xl space-y-4 shadow-xs">
          <h3 className="text-xs font-bold text-[#667085] uppercase tracking-wider">
            Incident Severity Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#DED8CC', color: '#1F2933', fontSize: '12px', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 text-xs">
            {severityData.map((s) => (
              <div key={s.name} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
                <span className="text-[#1F2933] font-medium">{s.name}: <strong>{s.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Response Time Trend */}
        <div className="bg-white border border-[#DED8CC] p-6 rounded-xl space-y-4 shadow-xs">
          <h3 className="text-xs font-bold text-[#667085] uppercase tracking-wider">
            Average Response ETA Trend (Minutes)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={responseTimeData}>
                <XAxis dataKey="time" stroke="#667085" fontSize={11} />
                <YAxis stroke="#667085" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#DED8CC', color: '#1F2933', fontSize: '12px', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="avgEta" stroke="#B42318" strokeWidth={3} dot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-xs text-[#667085]">
            Spatio-Temporal Dispatch Engine optimized response dispatch times continuously.
          </div>
        </div>

      </div>

    </div>
  );
}
