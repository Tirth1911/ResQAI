import React from 'react';

export type WebSocketStatus = 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED';

interface ConnectionStatusProps {
  status?: WebSocketStatus;
  isConnected?: boolean;
  serverUrl?: string;
  className?: string;
}

export function ConnectionStatus({
  status,
  isConnected,
  serverUrl,
  className = '',
}: ConnectionStatusProps) {
  // Normalize status if boolean is passed
  const currentStatus: WebSocketStatus =
    status || (isConnected ? 'CONNECTED' : 'DISCONNECTED');

  const statusConfig: Record<
    WebSocketStatus,
    { text: string; bg: string; border: string; textColor: string; dotColor: string; pulse: boolean }
  > = {
    CONNECTED: {
      text: 'LIVE WS',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      textColor: 'text-emerald-700 font-semibold',
      dotColor: 'bg-emerald-500',
      pulse: true,
    },
    RECONNECTING: {
      text: 'RECONNECTING',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      textColor: 'text-amber-700 font-semibold',
      dotColor: 'bg-amber-500',
      pulse: true,
    },
    DISCONNECTED: {
      text: 'DISCONNECTED',
      bg: 'bg-slate-100',
      border: 'border-slate-200',
      textColor: 'text-slate-600 font-medium',
      dotColor: 'bg-slate-400',
      pulse: false,
    },
  };

  const config = statusConfig[currentStatus] || statusConfig.DISCONNECTED;

  return (
    <div
      className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-mono font-bold border backdrop-blur-md transition-all ${config.bg} ${config.border} ${config.textColor} ${className}`}
      title={serverUrl ? `WebSocket Target: ${serverUrl}` : undefined}
    >
      <span className="relative flex h-2 w-2">
        {config.pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${config.dotColor}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dotColor}`} />
      </span>
      <span>{config.text}</span>
    </div>
  );
}

export default ConnectionStatus;
