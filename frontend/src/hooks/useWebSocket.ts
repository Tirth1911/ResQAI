'use client';

import { useRealtimeEvents } from './useRealtimeEvents';
import { WebSocketEventPayload } from '@/types';

/**
 * Legacy wrapper that delegates to the singleton `useRealtimeEvents` hook,
 * preventing duplicate WebSocket connections.
 */
export function useWebSocket(onEvent?: (payload: WebSocketEventPayload) => void) {
  const { isConnected, send, status, lastEvent } = useRealtimeEvents(onEvent);
  return { isConnected, send, status, lastEvent };
}

