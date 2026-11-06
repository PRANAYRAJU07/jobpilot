'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { jobsApi } from '@/lib/api/jobs';
import { applicationsApi } from '@/lib/api/applications';
import { notificationsApi } from '@/lib/api/sources';
import { Briefcase, FileText, CheckCircle, AlertTriangle, Search, TrendingUp, Clock, Zap } from 'lucide-react';
import Link from 'next/link';
import { useEffect } from 'react';
import { format } from 'date-fns';

function StatCard({ title, value, icon: Icon, color, href }: {
  title: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  href?: string;
}) {
  const inner = (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4 ${href ? 'hover:shadow-md transition-shadow cursor-pointer' : ''}`}>
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500 mt-0.5">{title}</p>
      </div>
    </div>
  );
  if (href) return <Link href={href}>{inner}</Link>;
  return inner;
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4 animate-pulse">
      <div className="p-3 rounded-lg bg-gray-200 w-12 h-12" />
      <div className="space-y-2">
        <div className="h-7 w-16 bg-gray-200 rounded" />
        <div className="h-4 w-28 bg-gray-100 rounded" />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['job-stats'],
    queryFn: jobsApi.getStats,
  });
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', { limit: 5 }],
    queryFn: () => jobsApi.getJobs({ limit: 5 }),
  });
  const { data: apps = [], isLoading: appsLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationsApi.getApplications,
  });
  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.getNotifications,
  });

  const recentJobs = jobsData?.jobs || [];
  const submitted = apps.filter((a) => ['SUBMITTED', 'CONFIRMED'].includes(a.status)).length;
  const actionRequired = apps.filter((a) =>
    ['OTP_REQUIRED', 'CAPTCHA_REQUIRED', 'REVIEW_REQUIRED'].includes(a.status)
  ).length;
  const unreadNotifs = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">JobPilot AI — Real-time job discovery & matching</p>
        </div>
        {unreadNotifs > 0 && (
          <Link href="/notifications" className="flex items-center space-x-2 text-sm bg-yellow-50 border border-yellow-200 text-yellow-700 px-3 py-1.5 rounded-lg hover:bg-yellow-100 transition-colors">
            <AlertTriangle className="h-4 w-4" />
            <span>{unreadNotifs} unread notification{unreadNotifs > 1 ? 's' : ''}</span>
          </Link>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <StatCard title="Jobs Discovered" value={stats?.total_jobs ?? 0} icon={Search} color="bg-blue-500" href="/jobs" />
            <StatCard title="High Match (≥70%)" value={stats?.high_match_jobs ?? 0} icon={TrendingUp} color="bg-indigo-500" href="/jobs" />
            <StatCard title="Applications" value={apps.length} icon={FileText} color="bg-purple-500" href="/applications" />
            <StatCard title="Action Required" value={actionRequired} icon={AlertTriangle} color={actionRequired > 0 ? "bg-red-500" : "bg-gray-400"} href="/applications" />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Jobs */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Recently Discovered Jobs</h2>
            <Link href="/jobs" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {jobsLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="px-6 py-4 flex items-center space-x-4 animate-pulse">
                  <div className="w-10 h-10 bg-gray-200 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                  </div>
                </div>
              ))
            ) : recentJobs.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                <Search className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>No jobs have been discovered yet.</p>
              </div>
            ) : (
              recentJobs.map((job) => {
                const matchScore = job.raw_jd?.match_analysis?.relevance_score;
                return (
                  <Link key={job.id} href={`/jobs/${job.id}`} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors group">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                        {job.company?.charAt(0) || 'J'}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">{job.title}</p>
                        <p className="text-xs text-gray-500">{job.company} · {job.location || 'Location not specified'}</p>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0 ml-4">
                      {matchScore != null ? (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${matchScore >= 70 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                          {matchScore}% match
                        </span>
                      ) : null}
                      <p className="text-xs text-gray-400 mt-1">{job.created_at ? format(new Date(job.created_at), 'MMM d') : ''}</p>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>

        {/* Applications */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Applications</h2>
            <Link href="/applications" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              View all →
            </Link>
          </div>
          <div className="px-6 py-4">
            {appsLoading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-1/2" />
              </div>
            ) : apps.length === 0 ? (
              <div className="py-8 text-center text-gray-500">
                <FileText className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">No applications yet.</p>
                <p className="text-xs text-gray-400 mt-1">Applications will appear here once the automation starts.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {apps.slice(0, 6).map((app) => (
                  <Link key={app.id} href={`/applications/${app.id}`} className="flex items-center justify-between text-sm hover:bg-gray-50 -mx-2 px-2 py-1.5 rounded-lg transition-colors">
                    <span className="text-gray-600 truncate">{app.job_id?.slice(0, 8)}...</span>
                    <span className={`ml-2 flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${
                      app.status === 'CONFIRMED' ? 'bg-green-100 text-green-700' :
                      app.status === 'SUBMITTED' ? 'bg-blue-100 text-blue-700' :
                      app.status === 'REVIEW_REQUIRED' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>{app.status}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
