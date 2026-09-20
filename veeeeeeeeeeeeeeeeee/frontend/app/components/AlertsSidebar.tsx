'use client';

import React from 'react';
import { Alert } from '../types';
import { Bell, AlertTriangle, CheckCircle, ShieldAlert, X } from 'lucide-react';

interface AlertsSidebarProps {
  alerts: Alert[];
  isOpen: boolean;
  onClose: () => void;
  onResolveAlert: (alertId: string) => void;
}

export default function AlertsSidebar({
  alerts,
  isOpen,
  onClose,
  onResolveAlert
}: AlertsSidebarProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-md bg-white border-l border-[#DED8CC] h-full p-6 space-y-6 flex flex-col justify-between shadow-xl overflow-y-auto font-sans text-[#1F2933]">
        
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-[#DED8CC] pb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-[#FDECEC] text-[#B42318] rounded-xl border border-[#FCA5A5]">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-[#1F2933]">Tactical Grid Alerts</h2>
                <p className="text-xs text-[#667085]">Automated Escalation Warnings</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-[#667085] hover:text-[#1F2933] rounded-lg hover:bg-[#F5F1E8]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {alerts.length === 0 ? (
            <div className="p-8 text-center text-[#667085] text-xs bg-[#F5F1E8] rounded-xl border border-[#DED8CC]">
              No active warnings or unresolved alerts.
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alt) => (
                <div
                  key={alt.id}
                  className={`p-4 rounded-xl border space-y-2 text-xs transition-all ${
                    alt.resolved
                      ? 'bg-[#F5F1E8] border-[#DED8CC] opacity-60'
                      : alt.level === 'critical'
                      ? 'bg-[#FEEFEF] border-[#FCA5A5]'
                      : 'bg-[#FEF6E7] border-[#FDE68A]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-bold text-[#1F2933] flex items-center gap-1.5">
                      <AlertTriangle className={`w-4 h-4 ${alt.level === 'critical' ? 'text-[#C62828]' : 'text-[#C47A00]'}`} />
                      {alt.title}
                    </span>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                      alt.level === 'critical' ? 'bg-[#C62828] text-white' : 'bg-[#C47A00] text-white'
                    }`}>
                      {alt.level}
                    </span>
                  </div>

                  <p className="text-[#667085] text-xs leading-relaxed">{alt.description}</p>

                  <div className="flex items-center justify-between pt-2 border-t border-[#DED8CC]/60 text-[10px] text-[#667085]">
                    <span>{new Date(alt.created_at).toLocaleTimeString()}</span>
                    
                    {!alt.resolved ? (
                      <button
                        onClick={() => onResolveAlert(alt.id)}
                        className="px-3 py-1 bg-[#16803C] hover:bg-[#126730] text-white font-bold rounded-lg flex items-center gap-1 text-xs"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <span className="text-[#16803C] font-bold">ACKNOWLEDGED ✓</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 bg-[#F5F1E8] hover:bg-[#EDE8DD] text-[#1F2933] rounded-xl font-bold text-xs border border-[#DED8CC]"
        >
          Close Alerts Panel
        </button>

      </div>
    </div>
  );
}
