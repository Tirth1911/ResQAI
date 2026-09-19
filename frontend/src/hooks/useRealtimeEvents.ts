'use client';

import { useEffect, useRef } from 'react';
import { useWebSocketContext } from '@/context/WebSocketContext';
import { WebSocketEventPayload } from '@/types';

export function useRealtimeEvents(
  onEvent?: (payload: WebSocketEventPayload) => void
) {
  const { status, isConnected, lastEvent, send, toasts, dismissToast, subscribe } =
    useWebSocketContext();

  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!onEventRef.current) return;

    const unsubscribe = subscribe((payload) => {
      onEventRef.current?.(payload);
    });

    return () => {
      unsubscribe();
    };
  }, [subscribe]);

  return {
    status,
    isConnected,
    lastEvent,
    send,
    toasts,
    dismissToast,
  };
}

export default useRealtimeEvents;
