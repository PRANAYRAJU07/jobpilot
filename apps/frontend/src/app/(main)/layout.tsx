'use client';

import Sidebar from '@/components/Sidebar';
import { Bell, Search, Wifi, WifiOff } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws';
    let ws: WebSocket;
    let retryTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsStatus('connected');
      ws.onclose = () => {
        setWsStatus('disconnected');
        retryTimeout = setTimeout(connect, 5000);
      };
      ws.onerror = () => setWsStatus('disconnected');
    };

    connect();
    return () => {
      clearTimeout(retryTimeout);
      ws?.close();
    };
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs, applications..."
                className="w-full pl-10 pr-4 py-1.5 text-sm bg-gray-100 border border-transparent rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-colors"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const q = (e.target as HTMLInputElement).value;
                    window.location.href = `/jobs?q=${encodeURIComponent(q)}`;
                  }
                }}
              />
            </div>
          </div>

          <div className="flex items-center space-x-4 ml-4">
            {/* Connection status */}
            <div className="flex items-center space-x-1.5 text-xs">
              {wsStatus === 'connected' ? (
                <>
                  <Wifi className="h-3.5 w-3.5 text-green-500" />
                  <span className="text-green-600 font-medium">Live</span>
                </>
              ) : wsStatus === 'connecting' ? (
                <>
                  <div className="h-3.5 w-3.5 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
                  <span className="text-yellow-600 font-medium">Connecting</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-3.5 w-3.5 text-red-500" />
                  <span className="text-red-600 font-medium">Offline</span>
                </>
              )}
            </div>

            <Link href="/notifications" className="relative p-1.5 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
              <Bell className="h-5 w-5" />
            </Link>

            <Link href="/profile" className="flex items-center space-x-2 text-sm text-gray-700 hover:text-gray-900">
              <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">P</div>
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
