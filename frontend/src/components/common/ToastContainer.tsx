'use client';

import React from 'react';
import { useWebSocketContext, ToastMessage } from '@/context/WebSocketContext';
import Link from 'next/link';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  X,
  Radio,
  MapPin,
  ExternalLink,
} from 'lucide-react';

export function ToastContainer() {
  // Screen popup toasts disabled — operational alerts are routed to the notification bar
  return null;
}

export default ToastContainer;

