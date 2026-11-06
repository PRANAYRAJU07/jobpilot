'use client';

import { useQuery } from '@tanstack/react-query';
import { applicationsApi } from '@/lib/api/applications';
import Link from 'next/link';
import { format } from 'date-fns';
import { FileText, Clock } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  CONFIRMED: 'bg-green-100 text-green-700',
  SUBMITTED: 'bg-blue-100 text-blue-700',
  REVIEW_REQUIRED: 'bg-yellow-100 text-yellow-700',
  OTP_REQUIRED: 'bg-orange-100 text-orange-700',
  CAPTCHA_REQUIRED: 'bg-orange-100 text-orange-700',
  CANCELLED: 'bg-gray-100 text-gray-500',
  ERROR: 'bg-red-100 text-red-700',
  MATCHED: 'bg-indigo-100 text-indigo-700',
};

export default function ApplicationsPage() {
  const { data: apps = [], isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationsApi.getApplications,
  });

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div className="flex justify-between items-start">
              <div className="space-y-2 flex-1">
                <div className="h-5 bg-gray-200 rounded w-2/3" />
                <div className="h-3 bg-gray-100 rounded w-1/3" />
              </div>
              <div className="h-6 bg-gray-200 rounded w-20" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl bg-red-50 border border-red-200 rounded-xl p-6 text-red-600">
        Failed to load applications. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
        <p className="text-sm text-gray-500 mt-1">{apps.length} application{apps.length !== 1 ? 's' : ''} tracked</p>
      </div>

      {apps.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-20 text-center">
          <FileText className="h-10 w-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 font-medium">No applications yet.</p>
          <p className="text-sm text-gray-400 mt-1 max-w-sm mx-auto">
            Applications will appear here once the automated system begins submitting. You currently have 2,468 discovered jobs ready for matching.
          </p>
          <Link href="/jobs" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
            View discovered jobs →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map((app) => (
            <Link
              key={app.id}
              href={`/applications/${app.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-200 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-800">
                    Application <span className="font-mono text-xs text-gray-400">{app.id.slice(0, 8)}</span>
                  </p>
                  <div className="flex items-center text-xs text-gray-500 space-x-3">
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {app.created_at ? format(new Date(app.created_at), 'MMM d, yyyy h:mm a') : '-'}
                    </span>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[app.status] || 'bg-gray-100 text-gray-600'}`}>
                  {app.status.replace(/_/g, ' ')}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
