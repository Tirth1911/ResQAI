'use client';

import React from 'react';
import { useWebSocketContext, ToastMessage } from '@/context/WebSocketContext';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  X,
  Radio,
} from 'lucide-react';

export function ToastContainer() {
  const { toasts, dismissToast } = useWebSocketContext();

  if (!toasts || toasts.length === 0) return null;

  const severityStyles: Record<
    ToastMessage['severity'],
    { border: string; bg: string; text: string; icon: React.ReactNode }
  > = {
    CRITICAL: {
      border: 'border-red-600/80',
      bg: 'bg-gradient-to-r from-red-950/90 to-slate-950/95 shadow-2xl shadow-red-950/50',
      text: 'text-red-400',
      icon: <AlertOctagon className="h-5 w-5 text-red-400 animate-pulse shrink-0" />,
    },
    WARNING: {
      border: 'border-amber-600/80',
      bg: 'bg-gradient-to-r from-amber-950/90 to-slate-950/95 shadow-2xl shadow-amber-950/50',
      text: 'text-amber-400',
      icon: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />,
    },
    INFO: {
      border: 'border-cyan-600/80',
      bg: 'bg-gradient-to-r from-cyan-950/90 to-slate-950/95 shadow-2xl shadow-cyan-950/50',
      text: 'text-cyan-400',
      icon: <Radio className="h-5 w-5 text-cyan-400 shrink-0 animate-ping" />,
    },
    SUCCESS: {
      border: 'border-emerald-600/80',
      bg: 'bg-gradient-to-r from-emerald-950/90 to-slate-950/95 shadow-2xl shadow-emerald-950/50',
      text: 'text-emerald-400',
      icon: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />,
    },
  };

  return (
    <div className="fixed bottom-5 right-5 z-[3000] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none font-mono">
      {toasts.map((toast) => {
        const style = severityStyles[toast.severity] || severityStyles.INFO;

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto relative overflow-hidden rounded-xl border p-3.5 backdrop-blur-md transition-all duration-300 animate-in slide-in-from-bottom-5 fade-in ${style.border} ${style.bg}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5">{style.icon}</div>
                <div>
                  <div className="flex items-center gap-2">
                    <h5 className="font-bold text-white text-xs tracking-wide">
                      {toast.title}
                    </h5>
                    <span className="text-[10px] text-slate-400">
                      {toast.timestamp}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-300 font-sans leading-relaxed">
                    {toast.message}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => dismissToast(toast.id)}
                className="text-slate-400 hover:text-white transition-colors p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Glowing bottom telemetry accent */}
            <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${style.text.replace('text-', 'bg-')}`} />
          </div>
        );
      })}
    </div>
  );
}

export default ToastContainer;
