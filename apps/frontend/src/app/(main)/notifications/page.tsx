'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api/sources';
import { Bell, CheckCheck, Check } from 'lucide-react';
import { format } from 'date-fns';

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: 'border-l-red-500 bg-red-50',
  HIGH: 'border-l-orange-400 bg-orange-50',
  NORMAL: 'border-l-blue-400 bg-blue-50',
  LOW: 'border-l-gray-300 bg-white',
};

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data: notifications = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.getNotifications,
    refetchInterval: 30000,
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const unread = notifications.filter(n => !n.read);

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          <p className="text-sm text-gray-500 mt-1">{unread.length} unread</p>
        </div>
        {unread.length > 0 && (
          <button
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
            className="flex items-center px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <CheckCheck className="h-4 w-4 mr-1.5" />
            Mark all read
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-20 text-center">
          <Bell className="h-10 w-10 mx-auto text-gray-200 mb-3" />
          <p className="text-gray-500 font-medium">You&apos;re all caught up!</p>
          <p className="text-sm text-gray-400 mt-1">Notifications will appear here as your applications progress.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map(n => (
            <div
              key={n.id}
              className={`bg-white rounded-xl border-l-4 border border-gray-200 p-4 transition-opacity ${PRIORITY_STYLES[n.priority] || 'border-l-gray-300'} ${n.read ? 'opacity-70' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-0.5">
                    {!n.read && <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />}
                    <p className="text-sm font-semibold text-gray-900 truncate">{n.title}</p>
                  </div>
                  <p className="text-sm text-gray-600">{n.body}</p>
                  <p className="text-xs text-gray-400 mt-1.5">
                    {n.category} · {format(new Date(n.created_at), 'MMM d, h:mm a')}
                  </p>
                </div>
                {!n.read && (
                  <button
                    onClick={() => markReadMutation.mutate(n.id)}
                    className="ml-3 flex-shrink-0 p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Mark as read"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
