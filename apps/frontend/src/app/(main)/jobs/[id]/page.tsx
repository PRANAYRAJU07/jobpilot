'use client';

import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { jobsApi } from '@/lib/api/jobs';
import Link from 'next/link';
import { format } from 'date-fns';
import {
  ArrowLeft,
  ExternalLink,
  CheckCircle2,
  XCircle,
  MapPin,
  Calendar,
  Tag,
  BarChart2,
  ShieldCheck,
  Send,
  Loader2,
  MessageSquare,
} from 'lucide-react';
import { useState } from 'react';

function sanitizeHtml(html: string) {
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [alertStatus, setAlertStatus] = useState<any | null>(null);

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobsApi.getJob(id),
  });

  const { data: why, isLoading: whyLoading } = useQuery({
    queryKey: ['job-why', id],
    queryFn: () => jobsApi.getWhyJob(id),
    enabled: !!job,
  });

  const notifyMutation = useMutation({
    mutationFn: () => jobsApi.notifyJob(id),
    onSuccess: (data) => {
      setAlertStatus(data.dispatch_result);
    },
  });

  if (jobLoading) {
    return (
      <div className="max-w-5xl space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-3/4" />
        <div className="h-6 bg-gray-100 rounded w-1/3" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">Job not found.</p>
        <Link href="/jobs" className="mt-4 inline-block text-blue-600 hover:underline">
          ← Back to Jobs
        </Link>
      </div>
    );
  }

  const matchAnalysis = job.raw_jd?.match_analysis || {};
  const score = why?.relevance_score ?? matchAnalysis?.relevance_score;
  const matchedReqs: Array<{ skill: string; evidence: string[] }> =
    why?.matched_requirements || matchAnalysis?.matched_requirements || [];
  const missingReqs: string[] = why?.missing_requirements || matchAnalysis?.missing_requirements || [];
  const applyUrl = why?.apply_url || job.apply_url || job.url;
  const genuinenessReasons = why?.genuineness_reasons || matchAnalysis?.genuineness_reasons || [];
  const domainCategory = why?.domain_category || job.domain_category || matchAnalysis?.domain_category;
  const descriptionText = job.description ? sanitizeHtml(job.description) : null;

  const waShareText = encodeURIComponent(
    `🎯 *${job.title}* at *${job.company}* (${score ?? 0}% Skill Match)\n📍 ${job.location || 'India / Remote'}\n🔗 Apply Directly: ${applyUrl}`
  );

  return (
    <div className="max-w-5xl space-y-6">
      <Link href="/jobs" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 font-medium">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        Back to Jobs
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
              {job.company?.charAt(0) || 'J'}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                  <ShieldCheck className="h-3.5 w-3.5 mr-1" />
                  Verified Genuine ({why?.genuineness_score ?? job.genuineness_score ?? 100}%)
                </span>
                {domainCategory && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
                    Domain: {domainCategory.replace('_', ' ')}
                  </span>
                )}
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                  {job.source}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
              <p className="text-lg text-gray-600 mt-0.5">{job.company}</p>
              <div className="flex flex-wrap gap-3 mt-2">
                {job.location && (
                  <span className="flex items-center text-sm text-gray-500">
                    <MapPin className="h-3.5 w-3.5 mr-1" />
                    {job.location}
                  </span>
                )}
                {job.employment_type && job.employment_type !== 'None' && (
                  <span className="flex items-center text-sm text-gray-500">
                    <Tag className="h-3.5 w-3.5 mr-1" />
                    {job.employment_type}
                  </span>
                )}
                {job.posted_at && (
                  <span className="flex items-center text-sm text-gray-500">
                    <Calendar className="h-3.5 w-3.5 mr-1" />
                    Posted {format(new Date(job.posted_at), 'MMM d, yyyy')}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end space-y-2">
            {score != null && (
              <div
                className={`text-center px-4 py-2 rounded-xl border ${
                  score >= 70 ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <p className={`text-2xl font-bold ${score >= 70 ? 'text-green-600' : 'text-gray-700'}`}>{score}%</p>
                <p className="text-xs text-gray-500">Resume Skill Match</p>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {applyUrl && (
                <a
                  href={applyUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Apply on Original Page</span>
                </a>
              )}

              <button
                onClick={() => notifyMutation.mutate()}
                disabled={notifyMutation.isPending}
                className="flex items-center space-x-1.5 px-3.5 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 text-sm font-medium rounded-lg hover:bg-indigo-100 transition-colors"
              >
                {notifyMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                <span>Send Link to Email & WhatsApp</span>
              </button>

              {applyUrl && (
                <a
                  href={`https://wa.me/?text=${waShareText}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
                >
                  <MessageSquare className="h-4 w-4" />
                  <span>WhatsApp</span>
                </a>
              )}
            </div>
          </div>
        </div>

        {alertStatus && (
          <div className="mt-4 p-3.5 bg-green-50 border border-green-200 rounded-lg text-xs text-green-900 flex items-center justify-between">
            <span>
              ✓ Application link sent! Email: <strong>{alertStatus.channels?.email?.status}</strong> · WhatsApp:{' '}
              <strong>{alertStatus.channels?.whatsapp?.status}</strong>
            </span>
            {alertStatus.channels?.whatsapp?.whatsapp_url && (
              <a
                href={alertStatus.channels.whatsapp.whatsapp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-700 font-semibold underline ml-4"
              >
                Open in WhatsApp →
              </a>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Cross-Validation & Description */}
        <div className="lg:col-span-2 space-y-6">
          {/* Skill Cross-Validation Breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-100 flex items-center">
              <BarChart2 className="h-5 w-5 mr-2 text-blue-500" />
              Resume vs. Job Requirement Cross-Validation
            </h2>
            {whyLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-10 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : matchedReqs.length === 0 && missingReqs.length === 0 ? (
              <p className="text-sm text-gray-400">
                Upload your resume on the Resume page to run automatic skill-by-skill cross-validation.
              </p>
            ) : (
              <div className="space-y-4">
                {matchedReqs.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-green-700 mb-2 flex items-center">
                      <CheckCircle2 className="h-4 w-4 mr-1.5" />
                      Verified Skills Matched on Your Resume ({matchedReqs.length})
                    </h3>
                    <div className="space-y-2">
                      {matchedReqs.map((req, i) => (
                        <div key={i} className="flex items-start justify-between bg-green-50 rounded-lg px-4 py-2.5">
                          <span className="text-sm font-medium text-green-800">{req.skill}</span>
                          <div className="ml-4 flex flex-wrap gap-1 justify-end">
                            {req.evidence.map((ev, j) => (
                              <span key={j} className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                                {ev}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {missingReqs.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-red-600 mb-2 flex items-center">
                      <XCircle className="h-4 w-4 mr-1.5" />
                      Missing / Unverified Skills ({missingReqs.length})
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {missingReqs.map((req, i) => (
                        <span
                          key={i}
                          className="text-sm bg-red-50 text-red-700 px-3 py-1 rounded-full border border-red-100"
                        >
                          {req}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Job Description */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-100">
              Full Job Description
            </h2>
            {descriptionText ? (
              <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {descriptionText.length > 5000 ? descriptionText.slice(0, 5000) + '...' : descriptionText}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No description text available.</p>
            )}
          </div>
        </div>

        {/* Right: Metadata & Genuineness Verification */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="font-semibold text-gray-900 mb-4 text-sm">Original Source & Genuineness</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500 text-xs uppercase tracking-wide mb-0.5">Platform / ATS</dt>
                <dd className="font-medium text-gray-800">{job.source}</dd>
              </div>
              <div>
                <dt className="text-gray-500 text-xs uppercase tracking-wide mb-0.5">Cross-Validation Status</dt>
                <dd>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      job.status === 'MATCHED' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {job.status}
                  </span>
                </dd>
              </div>
              {genuinenessReasons.length > 0 && (
                <div>
                  <dt className="text-gray-500 text-xs uppercase tracking-wide mb-1">Authenticity Checks</dt>
                  <dd className="space-y-1 text-xs text-green-700">
                    {genuinenessReasons.map((r: string, idx: number) => (
                      <p key={idx}>✓ {r}</p>
                    ))}
                  </dd>
                </div>
              )}
              {applyUrl && (
                <div>
                  <dt className="text-gray-500 text-xs uppercase tracking-wide mb-0.5">Direct Application URL</dt>
                  <dd>
                    <a
                      href={applyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline break-all text-xs"
                    >
                      {applyUrl}
                    </a>
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
