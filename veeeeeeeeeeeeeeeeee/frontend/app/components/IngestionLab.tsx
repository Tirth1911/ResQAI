'use client';

import React, { useState } from 'react';
import { Incident, ReportSource, IncidentType, IncidentSeverity } from '../types';
import { checkDuplicateReport } from '../utils';
import { Sparkles, Radio, Send, CheckCircle2, AlertCircle, Copy, Layers, Zap } from 'lucide-react';

interface IngestionLabProps {
  incidents: Incident[];
  onAddNewIncident: (newInc: Incident) => void;
  onMergeReportToIncident: (incidentId: string, rawText: string, source: ReportSource, reporter: string, lat: number, lng: number) => void;
}

export default function IngestionLab({
  incidents,
  onAddNewIncident,
  onMergeReportToIncident
}: IngestionLabProps) {
  const [source, setSource] = useState<ReportSource>('citizen');
  const [reporter, setReporter] = useState<string>('Citizen Hotline Caller');
  const [rawText, setRawText] = useState<string>('');
  const [lat, setLat] = useState<number>(23.0360);
  const [lng, setLng] = useState<number>(72.5650);
  const [address, setAddress] = useState<string>('Near Commerce Six Roads, Navrangpura, Ahmedabad');

  const [triageResult, setTriageResult] = useState<{
    merged: boolean;
    incidentId?: string;
    incidentTitle?: string;
    actionMessage: string;
    severity?: IncidentSeverity;
    type?: IncidentType;
    confidence?: number;
    reasoning?: string;
  } | null>(null);

  const loadPreset = (presetType: 'chemical' | 'fire' | 'accident' | 'flood') => {
    if (presetType === 'chemical') {
      setSource('iot_sensor');
      setReporter('IoT Sensor #ODH-410');
      setRawText('CRITICAL: High concentration toxic chlorine gas detected (52 ppm). Chemical storage vessel leak at Odhav GIDC phase 3.');
      setLat(23.0282);
      setLng(72.6515);
      setAddress('Phase 3, Odhav GIDC Industrial Estate, Ahmedabad');
    } else if (presetType === 'fire') {
      setSource('citizen');
      setReporter('Sunil Varma');
      setRawText('Flames and heavy black smoke breaking out of rooftop restaurant on CG Road near Municipal market!');
      setLat(23.0345);
      setLng(72.5572);
      setAddress('CG Road, Opp Municipal Market, Navrangpura');
    } else if (presetType === 'accident') {
      setSource('hotline');
      setReporter('112 Dispatch Operator');
      setRawText('Multi-vehicle crash reported on SG Highway near Iskcon Flyover. Overturned SUV blocking lane 2.');
      setLat(23.0262);
      setLng(72.5072);
      setAddress('SG Highway, Iskcon Flyover, Vastrapur');
    } else if (presetType === 'flood') {
      setSource('field_officer');
      setReporter('Constable R. Solanki');
      setRawText('Rapid waterlogging under Subhash Bridge underpass. 2 vehicles submerged with drivers on roof.');
      setLat(23.0605);
      setLng(72.5805);
      setAddress('Subhash Bridge Underpass, Ahmedabad');
    }
  };

  const handleRunTriage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;

    const existingIncident = checkDuplicateReport(lat, lng, incidents);

    if (existingIncident) {
      onMergeReportToIncident(existingIncident.id, rawText, source, reporter, lat, lng);
      setTriageResult({
        merged: true,
        incidentId: existingIncident.id,
        incidentTitle: existingIncident.title,
        actionMessage: `Spatio-Temporal Deduplication Match found! Merged call into active incident ${existingIncident.id} (Distance < 2.5km).`,
        severity: existingIncident.severity,
        type: existingIncident.type,
        confidence: 0.95,
        reasoning: `Matched location coordinates (${lat.toFixed(4)}, ${lng.toFixed(4)}) to active cluster. Incremented call count to ${existingIncident.report_count + 1}.`
      });
    } else {
      const textLower = rawText.toLowerCase();
      let type: IncidentType = 'other';
      let severity: IncidentSeverity = 'medium';

      if (textLower.includes('chlorine') || textLower.includes('chemical') || textLower.includes('gas') || textLower.includes('hazmat')) {
        type = 'industrial';
        severity = 'critical';
      } else if (textLower.includes('fire') || textLower.includes('flame') || textLower.includes('smoke')) {
        type = 'fire';
        severity = 'high';
      } else if (textLower.includes('crash') || textLower.includes('accident') || textLower.includes('highway') || textLower.includes('collision')) {
        type = 'accident';
        severity = 'high';
      } else if (textLower.includes('flood') || textLower.includes('water') || textLower.includes('submerged')) {
        type = 'flood';
        severity = 'medium';
      }

      const newInc: Incident = {
        id: `inc-${Date.now().toString().slice(-4)}`,
        title: rawText.slice(0, 55) + '...',
        description: rawText,
        type,
        severity,
        priority: severity === 'critical' ? 95 : severity === 'high' ? 80 : 60,
        status: 'open',
        lat,
        lng,
        address,
        source,
        report_count: 1,
        reports: [
          {
            id: `rep-${Date.now()}`,
            source,
            reporter,
            raw_text: rawText,
            lat,
            lng,
            reported_at: new Date().toISOString()
          }
        ],
        ai_confidence: 0.94,
        ai_reasoning: `Extracted emergency signals from report text. Triaged incident type as ${type.toUpperCase()} with ${severity.toUpperCase()} severity. Recommended immediate unit dispatch.`,
        classified_by: 'ai',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        assignments: []
      };

      onAddNewIncident(newInc);
      setTriageResult({
        merged: false,
        incidentId: newInc.id,
        incidentTitle: newInc.title,
        actionMessage: `New Unique Incident Created & Triaged! Added to Live Command Grid.`,
        severity: newInc.severity,
        type: newInc.type,
        confidence: 0.94,
        reasoning: newInc.ai_reasoning
      });
    }
  };

  return (
    <div className="max-w-[1700px] mx-auto p-6 space-y-6 text-[#1F2933] font-sans">
      
      {/* Header Banner */}
      <div className="bg-white border border-[#DED8CC] p-5 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[#FDECEC] text-[#B42318] rounded-xl border border-[#FCA5A5]">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1F2933] flex items-center gap-2">
              <span>Multi-Source AI Ingestion & Deduplication Lab</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-[#F5F1E8] text-[#667085] border border-[#DED8CC] rounded-full">
                PIPELINE TESTER
              </span>
            </h2>
            <p className="text-xs text-[#667085]">Simulate incoming citizen calls, hotline reports, and IoT sensors to observe real-time AI triage & spatio-temporal merging</p>
          </div>
        </div>

        {/* Preset Buttons */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#667085] font-semibold">PRESETS:</span>
          <button
            onClick={() => loadPreset('chemical')}
            className="px-3 py-1.5 bg-[#F5F1E8] hover:bg-[#EDE8DD] border border-[#DED8CC] text-[#1F2933] rounded-lg transition-colors font-medium"
          >
            ☣️ Toxic Gas Leak
          </button>
          <button
            onClick={() => loadPreset('fire')}
            className="px-3 py-1.5 bg-[#F5F1E8] hover:bg-[#EDE8DD] border border-[#DED8CC] text-[#1F2933] rounded-lg transition-colors font-medium"
          >
            🔥 CG Road Fire
          </button>
          <button
            onClick={() => loadPreset('accident')}
            className="px-3 py-1.5 bg-[#F5F1E8] hover:bg-[#EDE8DD] border border-[#DED8CC] text-[#1F2933] rounded-lg transition-colors font-medium"
          >
            🚗 SG Highway Crash
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Ingestion Form */}
        <form onSubmit={handleRunTriage} className="bg-white border border-[#DED8CC] p-6 rounded-xl space-y-4 shadow-xs">
          <h3 className="text-xs font-bold text-[#667085] uppercase tracking-wider flex items-center gap-2 border-b border-[#DED8CC] pb-3">
            <Radio className="w-4 h-4 text-[#B42318]" />
            Report Ingestion Form
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-[#667085] font-medium">Report Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value as ReportSource)}
                className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:ring-2 focus:ring-[#B42318]"
              >
                <option value="citizen">Citizen Mobile App</option>
                <option value="hotline">112 Emergency Hotline</option>
                <option value="iot_sensor">IoT Environmental Sensor</option>
                <option value="field_officer">Field Officer Report</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-[#667085] font-medium">Reporter Name / ID</label>
              <input
                type="text"
                value={reporter}
                onChange={(e) => setReporter(e.target.value)}
                className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:ring-2 focus:ring-[#B42318]"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-[#667085] font-medium">Report Description / Transcript</label>
            <textarea
              rows={4}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Enter citizen call transcript or sensor alert details..."
              className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933] focus:ring-2 focus:ring-[#B42318] placeholder-[#667085]"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-[#667085] font-medium">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#667085] font-medium">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={lng}
                onChange={(e) => setLng(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#667085] font-medium">Location Label</label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full px-3 py-2 bg-[#F5F1E8] border border-[#DED8CC] rounded-lg text-xs text-[#1F2933]"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-[#B42318] hover:bg-[#911E14] text-white font-bold rounded-lg text-xs shadow-xs transition-colors flex items-center justify-center gap-2 uppercase tracking-wider"
          >
            <Zap className="w-4 h-4" />
            <span>Process AI Triage & Deduplication</span>
          </button>
        </form>

        {/* Triage Output Console */}
        <div className="bg-white border border-[#DED8CC] p-6 rounded-xl flex flex-col justify-between space-y-4 shadow-xs">
          <h3 className="text-xs font-bold text-[#667085] uppercase tracking-wider flex items-center gap-2 border-b border-[#DED8CC] pb-3">
            <Layers className="w-4 h-4 text-[#16803C]" />
            AI Pipeline Analytics Console
          </h3>

          {!triageResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-[#667085] text-xs gap-3 p-8 border border-dashed border-[#DED8CC] rounded-xl">
              <Sparkles className="w-8 h-8 text-[#667085]" />
              <span>Awaiting incoming report trigger...</span>
              <span className="text-[11px] text-[#667085] text-center">Select one of the presets above or enter custom report text to test AI triage.</span>
            </div>
          ) : (
            <div className="space-y-4 flex-1">
              
              <div className={`p-4 rounded-xl border space-y-2 ${
                triageResult.merged 
                  ? 'bg-[#EFF6FF] border-[#BFDBFE] text-[#2563EB]' 
                  : 'bg-[#EAF6ED] border-[#A7F3D0] text-[#16803C]'
              }`}>
                <div className="flex items-center gap-2 font-bold text-sm">
                  {triageResult.merged ? <Copy className="w-5 h-5 text-[#2563EB]" /> : <CheckCircle2 className="w-5 h-5 text-[#16803C]" />}
                  <span>{triageResult.merged ? 'DUPLICATE REPORT MERGED' : 'NEW INCIDENT CLUSTER CREATED'}</span>
                </div>
                <p className="text-xs leading-relaxed opacity-90">{triageResult.actionMessage}</p>
              </div>

              <div className="bg-[#F5F1E8] p-4 rounded-xl border border-[#DED8CC] space-y-2 text-xs text-[#1F2933]">
                <div>Target Incident ID: <strong className="text-[#1F2933]">{triageResult.incidentId}</strong></div>
                <div>Classified Type: <strong className="text-[#B42318] uppercase">{triageResult.type}</strong></div>
                <div>Severity Rating: <strong className="text-[#B42318] uppercase">{triageResult.severity}</strong></div>
                <div>AI Confidence: <strong className="text-[#16803C]">{((triageResult.confidence || 0.9) * 100).toFixed(0)}%</strong></div>
                <div className="pt-2 border-t border-[#DED8CC] text-[11px] text-[#667085]">
                  <span className="text-[#1F2933] font-bold">Reasoning: </span>
                  {triageResult.reasoning}
                </div>
              </div>

              <div className="p-3 bg-[#F5F1E8] rounded-lg border border-[#DED8CC] text-[11px] text-[#667085]">
                ✨ GIS Map and response unit dispatch rankings updated automatically.
              </div>

            </div>
          )}

        </div>

      </div>

    </div>
  );
}
