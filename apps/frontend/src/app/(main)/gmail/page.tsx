'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { gmailApi } from '@/lib/api/sources';
import { Mail, CheckCircle, AlertCircle, ExternalLink, RefreshCw, LogOut } from 'lucide-react';
import { format } from 'date-fns';
import { useSearchParams } from 'next/navigation';
import { useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';

export default function GmailPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const connected = searchParams.get('connected');
  const error = searchParams.get('error');

  // Refetch on redirect back from Google
  useEffect(() => {
    if (connected === 'true') {
      queryClient.invalidateQueries({ queryKey: ['gmail-connection'] });
    }
  }, [connected, queryClient]);

  const { data: connection, isLoading } = useQuery({
    queryKey: ['gmail-connection'],
    queryFn: gmailApi.getConnection,
  });

  const { data: authUrlData, isLoading: authLoading } = useQuery({
    queryKey: ['gmail-auth-url'],
    queryFn: gmailApi.getAuthUrl,
    enabled: !connection,
    retry: false,
  });

  const disconnectMutation = useMutation({
    mutationFn: gmailApi.disconnect,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gmail-connection'] }),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Gmail Integration</h1>
        <p className="text-sm text-gray-500 mt-1">Connect your Gmail to track application emails automatically</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          <strong>Authorization error:</strong> {decodeURIComponent(error)}
        </div>
      )}

      {connected === 'true' && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-700">
          ✓ Gmail connected successfully!
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        {isLoading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-6 bg-gray-200 rounded w-1/2" />
            <div className="h-4 bg-gray-100 rounded w-3/4" />
          </div>
        ) : connection ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-6 w-6 text-green-500" />
                <div>
                  <p className="font-semibold text-gray-900">Connected</p>
                  <p className="text-sm text-gray-500">{connection.email}</p>
                </div>
              </div>
              <button
                onClick={() => disconnectMutation.mutate()}
                disabled={disconnectMutation.isPending}
                className="flex items-center text-sm text-red-600 hover:text-red-700 px-3 py-1.5 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-3.5 w-3.5 mr-1.5" />
                Disconnect
              </button>
            </div>

            {connection.last_sync_at && (
              <p className="text-sm text-gray-600 flex items-center">
                <RefreshCw className="h-3.5 w-3.5 mr-1.5 text-gray-400" />
                Last sync: {format(new Date(connection.last_sync_at), 'MMM d, yyyy h:mm a')}
              </p>
            )}

            <div className="pt-3 border-t border-gray-100">
              <p className="text-xs text-gray-400">
                Your Gmail is connected. JobPilot monitors for job-related emails: confirmations, rejections, interview invitations, and assessments.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900">Gmail not connected</p>
                <p className="text-sm text-gray-500 mt-1">Connect your Gmail account to enable automatic email tracking and intelligence.</p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 space-y-2">
              <p className="font-medium text-gray-700">What this enables:</p>
              <ul className="space-y-1 list-disc list-inside text-gray-600">
                <li>Application confirmation tracking</li>
                <li>Rejection detection</li>
                <li>Interview invitation alerts</li>
                <li>Assessment deadline tracking</li>
                <li>Offer letter detection</li>
              </ul>
            </div>

            {authLoading ? (
              <div className="text-sm text-gray-400">Loading authorization URL...</div>
            ) : authUrlData?.url ? (
              <a
                href={authUrlData.url}
                className="inline-flex items-center px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Mail className="h-4 w-4 mr-2" />
                Connect Gmail
                <ExternalLink className="h-3.5 w-3.5 ml-2" />
              </a>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                Gmail OAuth is not configured on the backend. Please check server environment variables.
              </div>
            )}

            <p className="text-xs text-gray-400">
              JobPilot requests read-only access to your Gmail. We only classify job-related emails. Your credentials are stored securely.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
