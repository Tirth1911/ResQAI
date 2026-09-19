'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import { getWsBaseUrl } from '@/lib/constants';
import { WebSocketEventPayload } from '@/types';
import { WebSocketStatus } from '@/components/common/ConnectionStatus';

export interface ToastMessage {
  id: string;
  title: string;
  message: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'SUCCESS';
  timestamp: string;
  event: string;
}

interface WebSocketContextType {
  status: WebSocketStatus;
  isConnected: boolean;
  lastEvent: WebSocketEventPayload | null;
  send: (message: string | object) => void;
  toasts: ToastMessage[];
  dismissToast: (id: string) => void;
  subscribe: (handler: (payload: WebSocketEventPayload) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

function normalizeWsUrl(): string {
  let url = getWsBaseUrl();
  
  // In browser environments loaded via HTTPS, ensure wss:// is used for remote backend URLs
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    if (url.startsWith('ws://') && !url.includes('localhost') && !url.includes('127.0.0.1')) {
      url = url.replace('ws://', 'wss://');
    }
  }

  if (url.endsWith('/ws/dashboard') || url.endsWith('/ws')) {
    return url;
  }
  return `${url.replace(/\/+$/, '')}/ws/dashboard`;
}

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<WebSocketStatus>('DISCONNECTED');
  const [lastEvent, setLastEvent] = useState<WebSocketEventPayload | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const listenersRef = useRef<Set<(payload: WebSocketEventPayload) => void>>(new Set());
  const reconnectAttemptsRef = useRef(0);

  const addToast = useCallback((toast: Omit<ToastMessage, 'id' | 'timestamp'>) => {
    const newToast: ToastMessage = {
      ...toast,
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      timestamp: new Date().toLocaleTimeString(),
    };

    setToasts((prev) => [newToast, ...prev.slice(0, 4)]); // Keep max 5 toasts

    // Auto-dismiss after 6 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== newToast.id));
    }, 6000);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const handleEventNotifications = useCallback((payload: WebSocketEventPayload) => {
    const evt = payload.event;
    const data = payload.data || {};

    if (evt === 'INCIDENT_CREATED') {
      addToast({
        title: '🚨 New Incident Logged',
        message: data.title || payload.incident_id || 'Emergency call ingested',
        severity: data.severity === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
        event: evt,
      });
    } else if (evt === 'INCIDENT_ESCALATED') {
      addToast({
        title: '⚡ Incident Escalated',
        message: `${payload.incident_id || 'Incident'} escalated to CRITICAL priority`,
        severity: 'CRITICAL',
        event: evt,
      });
    } else if (evt === 'INCIDENT_CLASSIFIED') {
      addToast({
        title: '🤖 AI Incident Classified',
        message: `${payload.incident_id || 'Incident'}: ${data.incident_type || 'Assessed'} (${data.severity || 'Triage'})`,
        severity: 'INFO',
        event: evt,
      });
    } else if (evt === 'INCIDENT_DUPLICATED' || evt === 'INCIDENT_DUPLICATE_MERGED') {
      addToast({
        title: '🔗 Duplicate Report Merged',
        message: `Linked duplicate report to ${payload.incident_id || 'incident'} via NLP/Geospatial match`,
        severity: 'INFO',
        event: evt,
      });
    } else if (evt === 'RESOURCE_ASSIGNED') {
      addToast({
        title: '🚒 Unit Dispatched',
        message: `Unit ${payload.resource_id || ''} assigned to ${payload.incident_id || 'Incident'}`,
        severity: 'SUCCESS',
        event: evt,
      });
    } else if (evt === 'RESOURCE_RELEASED') {
      addToast({
        title: '✅ Unit Released',
        message: `Unit ${payload.resource_id || ''} is now AVAILABLE in pool`,
        severity: 'SUCCESS',
        event: evt,
      });
    } else if (evt === 'RESOURCE_SHORTAGE') {
      addToast({
        title: '⚠️ Resource Shortage Alert',
        message: `Shortage detected for required emergency capabilities`,
        severity: 'CRITICAL',
        event: evt,
      });
    } else if (evt === 'NOTIFICATION_CREATED' || evt === 'ALERT_TRIGGERED') {
      addToast({
        title: '📢 Operational Alert',
        message: data.message || 'System notification received',
        severity: data.severity === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
        event: evt,
      });
    }
  }, [addToast]);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const targetUrl = normalizeWsUrl();
      console.log(`[ResQAI WebSocket] Connecting to: ${targetUrl}`);
      setStatus(reconnectAttemptsRef.current > 0 ? 'RECONNECTING' : 'DISCONNECTED');

      const ws = new WebSocket(targetUrl);

      ws.onopen = () => {
        console.log('[ResQAI WebSocket] Connection established successfully.');
        setStatus('CONNECTED');
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as WebSocketEventPayload;
          setLastEvent(payload);

          // Trigger toast notifications
          handleEventNotifications(payload);

          // Broadcast to all active subscribers
          listenersRef.current.forEach((listener) => {
            try {
              listener(payload);
            } catch (err) {
              console.error('[WebSocket Subscriber Error]', err);
            }
          });
        } catch (err) {
          console.warn('[ResQAI WebSocket] Could not parse packet:', err);
        }
      };

      ws.onclose = () => {
        console.warn('[ResQAI WebSocket] Connection closed. Scheduling automatic reconnect...');
        setStatus('RECONNECTING');
        wsRef.current = null;

        const backoffMs = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 10000);
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, backoffMs);
      };

      ws.onerror = (e) => {
        console.warn('[ResQAI WebSocket] Connection encountered an error:', e);
        ws.close();
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[ResQAI WebSocket] Exception initiating socket:', err);
      setStatus('DISCONNECTED');
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    }
  }, [handleEventNotifications]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((message: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const raw = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(raw);
    }
  }, []);

  const subscribe = useCallback((handler: (payload: WebSocketEventPayload) => void) => {
    listenersRef.current.add(handler);
    return () => {
      listenersRef.current.delete(handler);
    };
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        status,
        isConnected: status === 'CONNECTED',
        lastEvent,
        send,
        toasts,
        dismissToast,
        subscribe,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}
