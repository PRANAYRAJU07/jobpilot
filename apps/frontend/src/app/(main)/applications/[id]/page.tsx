'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationsApi } from '@/lib/api/applications';
import Link from 'next/link';
import { format } from 'date-fns';
import { ArrowLeft, CheckCircle, Clock, XCircle } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  CONFIRMED: 'bg-green-100 text-green-700',
  SUBMITTED: 'bg-blue-100 text-blue-700',
  REVIEW_REQUIRED: 'bg-yellow-100 text-yellow-700',
  OTP_REQUIRED: 'bg-orange-100 text-orange-700',
  ERROR: 'bg-red-100 text-red-700',
  CANCELLED: 'bg-gray-100 text-gray-500',
};

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: app, isLoading } = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.getApplication(id),
  });

  const { data: events = [], isLoading: eventsLoading } = useQuery({
    queryKey: ['application-events', id],
    queryFn: () => applicationsApi.getEvents(id),
    enabled: !!app,
  });

  const approveMutation = useMutation({
    mutationFn: () => applicationsApi.approve(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', id] }),
  });

  const cancelMutation = useMutation({
    mutationFn: () => applicationsApi.cancel(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', id] }),
  });

  if (isLoading) {
    return (
      <div className="max-w-3xl animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-24" />
        <div className="h-10 bg-gray-200 rounded w-2/3" />
        <div className="h-64 bg-gray-100 rounded-xl" />
      </div>
    );
  }

  if (!app) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">Application not found.</p>
        <Link href="/applications" className="mt-4 inline-block text-blue-600 hover:underline">← Back to Applications</Link>
      </div>
    );
  }

  const canApprove = app.status === 'REVIEW_REQUIRED';
  const canCancel = !['CONFIRMED', 'CANCELLED', 'SUBMITTED'].includes(app.status);

  return (
    <div className="max-w-3xl space-y-6">
      <Link href="/applications" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 font-medium">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        Back to Applications
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Application Detail</h1>
            <p className="text-sm text-gray-500 font-mono mt-1">{app.id}</p>
            <div className="mt-3">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${STATUS_COLORS[app.status] || 'bg-gray-100 text-gray-600'}`}>
                {app.status.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          <div className="flex space-x-2">
            {canApprove && (
              <button
                onClick={() => approveMutation.mutate()}
                disabled={approveMutation.isPending}
                className="flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                <CheckCircle className="h-4 w-4 mr-1.5" />
                Approve
              </button>
            )}
            {canCancel && (
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="flex items-center px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-lg hover:bg-red-200 disabled:opacity-50 transition-colors"
              >
                <XCircle className="h-4 w-4 mr-1.5" />
                Cancel
              </button>
            )}
          </div>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd className="font-medium mt-0.5">{format(new Date(app.created_at), 'MMM d, yyyy h:mm a')}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Updated</dt>
            <dd className="font-medium mt-0.5">{format(new Date(app.updated_at), 'MMM d, yyyy h:mm a')}</dd>
          </div>
        </dl>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-100">Application Timeline</h2>
        {eventsLoading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3].map(i => <div key={i} className="h-10 bg-gray-100 rounded-lg" />)}
          </div>
        ) : events.length === 0 ? (
          <p className="text-sm text-gray-400">No events recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {events.map((event, i) => (
              <div key={event.id} className="flex items-start space-x-3">
                <div className={`mt-1 flex-shrink-0 w-2 h-2 rounded-full ${i === 0 ? 'bg-blue-500' : 'bg-gray-300'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-800">
                      <span className="text-gray-400">{event.previous_state}</span>
                      <span className="mx-2 text-gray-300">→</span>
                      <span>{event.new_state}</span>
                    </p>
                    <span className="text-xs text-gray-400 flex-shrink-0 ml-3">
                      {format(new Date(event.timestamp), 'MMM d, h:mm a')}
                    </span>
                  </div>
                  {event.reason && (
                    <p className="text-xs text-gray-500 mt-0.5">{event.reason}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
