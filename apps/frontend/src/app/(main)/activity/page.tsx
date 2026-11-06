'use client';

import { useEffect, useRef, useState } from 'react';
import { format } from 'date-fns';
import { Activity, Wifi, WifiOff, Loader2 } from 'lucide-react';

interface ActivityEvent {
  id: string;
  type: string;
  data: unknown;
  timestamp: string;
}

const EVENT_COLORS: Record<string, string> = {
  JOB_DISCOVERED: 'border-blue-400 bg-blue-50',
  JOB_UPDATED: 'border-indigo-400 bg-indigo-50',
  APPLICATION_STARTED: 'border-purple-400 bg-purple-50',
  APPLICATION_EVENT: 'border-orange-400 bg-orange-50',
  NOTIFICATION_CREATED: 'border-yellow-400 bg-yellow-50',
  EMAIL_RECEIVED: 'border-green-400 bg-green-50',
  INTERVIEW_DETECTED: 'border-emerald-400 bg-emerald-50',
  ASSESSMENT_DETECTED: 'border-teal-400 bg-teal-50',
};

export default function ActivityPage() {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws';

    const connect = () => {
      setStatus('connecting');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (evt) => {
        try {
          const parsed = JSON.parse(evt.data);
          const entry: ActivityEvent = {
            id: Math.random().toString(36).slice(2),
            type: parsed.type || 'SYSTEM',
            data: parsed,
            timestamp: new Date().toISOString(),
          };
          setEvents(prev => [entry, ...prev].slice(0, 100));
        } catch {
          // raw text message
          const entry: ActivityEvent = {
            id: Math.random().toString(36).slice(2),
            type: 'SYSTEM',
            data: evt.data,
            timestamp: new Date().toISOString(),
          };
          setEvents(prev => [entry, ...prev].slice(0, 100));
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        reconnectAttempts.current++;
        const delay = Math.min(5000 * reconnectAttempts.current, 30000);
        retryRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Live Activity</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time events from the JobPilot system</p>
        </div>
        <div className={`flex items-center space-x-2 text-sm px-3 py-1.5 rounded-full border ${
          status === 'connected' ? 'bg-green-50 border-green-200 text-green-700' :
          status === 'connecting' ? 'bg-yellow-50 border-yellow-200 text-yellow-700' :
          'bg-red-50 border-red-200 text-red-700'
        }`}>
          {status === 'connected' ? (
            <><Wifi className="h-4 w-4" /><span>Connected</span></>
          ) : status === 'connecting' ? (
            <><Loader2 className="h-4 w-4 animate-spin" /><span>Connecting...</span></>
          ) : (
            <><WifiOff className="h-4 w-4" /><span>Disconnected — Retrying</span></>
          )}
        </div>
      </div>

      {/* Events */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        {events.length === 0 ? (
          <div className="py-20 text-center">
            <Activity className="h-10 w-10 mx-auto text-gray-200 mb-3" />
            <p className="text-gray-500 font-medium">No activity yet</p>
            <p className="text-sm text-gray-400 mt-1">
              {status === 'connected'
                ? 'Events will appear here in real-time as they occur.'
                : 'Waiting for WebSocket connection...'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {events.map((event) => (
              <div key={event.id} className={`px-5 py-4 border-l-4 ${EVENT_COLORS[event.type] || 'border-gray-300 bg-white'}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      {event.type.replace(/_/g, ' ')}
                    </span>
                    <p className="text-sm text-gray-700 mt-0.5 font-mono">
                      {typeof event.data === 'string'
                        ? event.data
                        : JSON.stringify(event.data, null, 0).slice(0, 200)}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0 ml-4">
                    {format(new Date(event.timestamp), 'h:mm:ss a')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
