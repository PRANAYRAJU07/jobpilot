'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job } from '@/lib/api/jobs';
import Link from 'next/link';
import { format } from 'date-fns';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Building2,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  Loader2,
  Clock,
} from 'lucide-react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';

const SOURCES = ['GREENHOUSE', 'LEVER', 'ASHBY', 'LINKEDIN', 'INTERNSHALA', 'NAUKRI', 'DIRECT_CAREER'];
const DOMAINS = [
  { value: 'AI_ML', label: 'AI / Machine Learning' },
  { value: 'DATA_SCIENCE', label: 'Data Science & Analytics' },
  { value: 'BACKEND_ENGINEERING', label: 'Backend & APIs' },
  { value: 'FULL_STACK', label: 'Full-Stack / Web' },
  { value: 'SOFTWARE_ENGINEERING', label: 'Software Engineering' },
  { value: 'DEVOPS_CLOUD', label: 'Cloud / DevOps / MLOps' },
];

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;
  const color =
    score >= 70
      ? 'bg-green-100 text-green-700 border border-green-200'
      : score >= 50
      ? 'bg-yellow-100 text-yellow-700 border border-yellow-200'
      : 'bg-gray-100 text-gray-600';
  return <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${color}`}>{score}% match</span>;
}

export default function JobsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState(searchParams.get('q') || '');
  const [source, setSource] = useState(searchParams.get('source') || '');
  const [domain, setDomain] = useState(searchParams.get('domain') || '');
  const [freshOnly, setFreshOnly] = useState(false);
  const [internshipsOnly, setInternshipsOnly] = useState(false);
  const [minScore, setMinScore] = useState<string>('');
  const [page, setPage] = useState(0);
  const limit = 24;

  const applyFilters = useCallback(() => {
    const params = new URLSearchParams();
    if (search) params.set('q', search);
    if (source) params.set('source', source);
    if (domain) params.set('domain', domain);
    router.push(`${pathname}?${params.toString()}`);
    setPage(0);
  }, [search, source, domain, pathname, router]);

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: [
      'jobs',
      {
        q: search,
        source,
        domain,
        fresh_only: freshOnly || undefined,
        is_internship: internshipsOnly ? true : undefined,
        min_score: minScore ? parseInt(minScore, 10) : undefined,
        skip: page * limit,
        limit,
      },
    ],
    queryFn: () =>
      jobsApi.getJobs({
        q: search || undefined,
        source: source || undefined,
        domain: domain || undefined,
        fresh_only: freshOnly || undefined,
        is_internship: internshipsOnly ? true : undefined,
        min_score: minScore ? parseInt(minScore, 10) : undefined,
        genuine_only: true,
        skip: page * limit,
        limit,
      }),
    placeholderData: (prev) => prev,
  });

  const scanMutation = useMutation({
    mutationFn: () => jobsApi.triggerSearch(),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['jobs'] }), 2000);
    },
  });

  const jobs: Job[] = data?.jobs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Verified Jobs & Internships</h1>
          <p className="text-sm text-gray-500 mt-1">
            {total.toLocaleString()} genuine openings cross-validated across Career Pages, LinkedIn, Internshala & Naukri
          </p>
        </div>

        <button
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {scanMutation.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Discover Fresh Jobs Now
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search role, skill (PyTorch, FastAPI), company, city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={source}
            onChange={(e) => { setSource(e.target.value); setPage(0); }}
            className="py-2 px-3 text-sm border border-gray-200 rounded-lg bg-white"
          >
            <option value="">All Platforms / Sources</option>
            {SOURCES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={domain}
            onChange={(e) => { setDomain(e.target.value); setPage(0); }}
            className="py-2 px-3 text-sm border border-gray-200 rounded-lg bg-white"
          >
            <option value="">All Domains</option>
            {DOMAINS.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>

          <select
            value={minScore}
            onChange={(e) => { setMinScore(e.target.value); setPage(0); }}
            className="py-2 px-3 text-sm border border-gray-200 rounded-lg bg-white"
          >
            <option value="">Any Match Score</option>
            <option value="50">≥ 50% Skill Match</option>
            <option value="60">≥ 60% Skill Match</option>
            <option value="70">≥ 70% High Match</option>
            <option value="80">≥ 80% Top Match</option>
          </select>

          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Filter className="h-4 w-4 inline mr-1.5" />
            Apply
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-gray-100 text-xs text-gray-700">
          <label className="inline-flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={freshOnly}
              onChange={(e) => { setFreshOnly(e.target.checked); setPage(0); }}
              className="rounded text-blue-600"
            />
            <span className="font-medium flex items-center">
              <Clock className="h-3.5 w-3.5 mr-1 text-green-600" />
              Freshly Posted Only (≤ 72h)
            </span>
          </label>

          <label className="inline-flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={internshipsOnly}
              onChange={(e) => { setInternshipsOnly(e.target.checked); setPage(0); }}
              className="rounded text-blue-600"
            />
            <span className="font-medium">Internships Only</span>
          </label>

          {(search || source || domain || freshOnly || internshipsOnly || minScore) && (
            <button
              onClick={() => {
                setSearch('');
                setSource('');
                setDomain('');
                setFreshOnly(false);
                setInternshipsOnly(false);
                setMinScore('');
                setPage(0);
                router.push(pathname);
              }}
              className="text-blue-600 hover:underline ml-auto"
            >
              Reset All Filters
            </button>
          )}
        </div>
      </div>

      {/* Results Grid */}
      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-600">
          Failed to load jobs. Please check your connection and try again.
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse h-44" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 text-center">
          <Building2 className="h-10 w-10 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 font-medium">No matching jobs found</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your filters or click &ldquo;Discover Fresh Jobs Now&rdquo;</p>
        </div>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 ${isFetching ? 'opacity-70' : ''} transition-opacity`}>
          {jobs.map((job) => {
            const matchAnalysis = job.raw_jd?.match_analysis || {};
            const matchScore = matchAnalysis?.relevance_score as number | null;
            const matchedSkills: string[] = matchAnalysis?.matched_skills || [];
            const domainCat = job.domain_category || matchAnalysis?.domain_category;

            return (
              <Link
                key={job.id}
                href={`/jobs/${job.id}`}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-200 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        {job.company?.charAt(0) || 'J'}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 text-sm group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">
                          {job.title}
                        </h3>
                        <p className="text-xs text-gray-500 mt-0.5">{job.company}</p>
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 space-y-1 mb-3">
                    {job.location && <p className="truncate">📍 {job.location}</p>}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {job.is_fresh && (
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full text-[11px] font-medium">
                          Fresh
                        </span>
                      )}
                      {job.is_internship && (
                        <span className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full text-[11px] font-medium">
                          Internship
                        </span>
                      )}
                      {domainCat && domainCat !== 'NON_TECH_OTHER' && (
                        <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-[11px] font-medium">
                          {domainCat.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                  </div>

                  {matchedSkills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {matchedSkills.slice(0, 4).map((sk) => (
                        <span key={sk} className="text-[11px] bg-green-50 text-green-700 px-2 py-0.5 rounded">
                          ✓ {sk}
                        </span>
                      ))}
                      {matchedSkills.length > 4 && (
                        <span className="text-[11px] text-gray-400">+{matchedSkills.length - 4} more</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center space-x-2">
                    <ScoreBadge score={matchScore} />
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-50 text-blue-600">
                      {job.source}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400 flex items-center">
                    <ShieldCheck className="h-3.5 w-3.5 text-green-600 mr-1" />
                    {job.posted_at
                      ? format(new Date(job.posted_at), 'MMM d')
                      : job.created_at
                      ? format(new Date(job.created_at), 'MMM d')
                      : ''}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total.toLocaleString()} jobs
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-600">
              Page {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
