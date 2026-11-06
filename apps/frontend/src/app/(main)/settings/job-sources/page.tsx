'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sourcesApi, type JobSource } from '@/lib/api/sources';
import { format } from 'date-fns';
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  ToggleLeft,
  ToggleRight,
  Plus,
} from 'lucide-react';
import { useState } from 'react';

const STATUS_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  ACTIVE: { label: 'Active', color: 'text-green-700 bg-green-50 border-green-200', dot: 'bg-green-500' },
  PENDING: { label: 'Pending', color: 'text-yellow-700 bg-yellow-50 border-yellow-200', dot: 'bg-yellow-500' },
  ERROR: { label: 'Error', color: 'text-red-700 bg-red-50 border-red-200', dot: 'bg-red-500' },
  UNSUPPORTED: { label: 'Unsupported', color: 'text-gray-600 bg-gray-50 border-gray-200', dot: 'bg-gray-400' },
  MANUAL_CONFIGURATION_REQUIRED: {
    label: 'Manual Config Required',
    color: 'text-orange-700 bg-orange-50 border-orange-200',
    dot: 'bg-orange-400',
  },
};

function SourceCard({ source }: { source: JobSource }) {
  const queryClient = useQueryClient();
  const [scanning, setScanning] = useState(false);

  const scanMutation = useMutation({
    mutationFn: () => sourcesApi.triggerScan(source.id),
    onMutate: () => setScanning(true),
    onSettled: () => {
      setScanning(false);
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['sources'] }), 2000);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: () => sourcesApi.toggleSource(source.id, !source.enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sources'] }),
  });

  const cfg = STATUS_CONFIG[source.status] || STATUS_CONFIG.PENDING;

  return (
    <div
      className={`bg-white rounded-xl border ${
        source.enabled ? 'border-gray-200' : 'border-gray-100 opacity-75'
      } shadow-sm p-5`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            {source.company.charAt(0)}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">{source.company}</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {source.source_type} · {source.external_company_id}
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.color}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          <span>{cfg.label}</span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500">Jobs Found</p>
          <p className="text-xl font-bold text-gray-900 mt-0.5">{source.jobs_found ?? 0}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500">Scan Interval</p>
          <p className="text-lg font-bold text-gray-900 mt-0.5">{source.scan_interval_minutes}m</p>
        </div>
      </div>

      <div className="space-y-1.5 mb-4 text-xs text-gray-500">
        {source.last_scan_at && (
          <p className="flex items-center">
            <Clock className="h-3 w-3 mr-1.5" />
            Last scan: {format(new Date(source.last_scan_at), 'MMM d, h:mm a')}
          </p>
        )}
        {source.last_success_at && (
          <p className="flex items-center text-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1.5" />
            Last success: {format(new Date(source.last_success_at), 'MMM d, h:mm a')}
          </p>
        )}
        {source.last_error && (
          <p className="flex items-start text-red-500">
            <XCircle className="h-3 w-3 mr-1.5 flex-shrink-0 mt-0.5" />
            <span className="truncate">{source.last_error}</span>
          </p>
        )}
      </div>

      <div className="flex space-x-2 pt-3 border-t border-gray-100">
        {source.enabled && (
          <button
            onClick={() => scanMutation.mutate()}
            disabled={scanning || scanMutation.isPending}
            className="flex items-center px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
          >
            {scanning ? <Loader2 className="h-3 w-3 mr-1.5 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1.5" />}
            Scan Now
          </button>
        )}
        <button
          onClick={() => toggleMutation.mutate()}
          disabled={toggleMutation.isPending}
          className={`flex items-center px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors disabled:opacity-50 ${
            source.enabled
              ? 'text-gray-600 bg-gray-50 border-gray-200 hover:bg-gray-100'
              : 'text-green-700 bg-green-50 border-green-200 hover:bg-green-100'
          }`}
        >
          {source.enabled ? <ToggleRight className="h-3 w-3 mr-1.5" /> : <ToggleLeft className="h-3 w-3 mr-1.5" />}
          {source.enabled ? 'Disable' : 'Enable'}
        </button>
      </div>
    </div>
  );
}

export default function JobSourcesPage() {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [newSource, setNewSource] = useState({
    company: '',
    source_type: 'LINKEDIN',
    external_company_id: 'AI Machine Learning Intern|Hyderabad, India',
    career_url: 'https://www.linkedin.com/jobs/',
    scan_interval_minutes: 30,
  });

  const { data: sources = [], isLoading, error } = useQuery({
    queryKey: ['sources'],
    queryFn: sourcesApi.getSources,
    refetchInterval: 30000,
  });

  const scanAllMutation = useMutation({
    mutationFn: () => sourcesApi.scanAll(),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['sources'] }), 2000);
    },
  });

  const createMutation = useMutation({
    mutationFn: () => sourcesApi.createSource(newSource),
    onSuccess: () => {
      setShowAdd(false);
      setNewSource({
        company: '',
        source_type: 'LINKEDIN',
        external_company_id: '',
        career_url: '',
        scan_interval_minutes: 30,
      });
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  const activeSources = sources.filter((s) => s.enabled && s.status === 'ACTIVE');
  const totalJobs = sources.reduce((sum, s) => sum + (s.jobs_found || 0), 0);

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job & Internship Discovery Sources</h1>
          <p className="text-sm text-gray-500 mt-1">
            {activeSources.length} active sources across Direct Company Career Pages, LinkedIn, Internshala, Naukri, Greenhouse, Lever & Ashby
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="inline-flex items-center px-3.5 py-2 bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Add Source
          </button>
          <button
            onClick={() => scanAllMutation.mutate()}
            disabled={scanAllMutation.isPending}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {scanAllMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Scan All Sources Now
          </button>
        </div>
      </div>

      {showAdd && (
        <div className="bg-white rounded-xl border border-blue-200 shadow-sm p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-900">Add New Career Page or Platform Search Source</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Source Name / Company</label>
              <input
                type="text"
                placeholder="e.g. LinkedIn AI Interns or OpenAI Careers"
                value={newSource.company}
                onChange={(e) => setNewSource((s) => ({ ...s, company: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Platform / Connector Type</label>
              <select
                value={newSource.source_type}
                onChange={(e) => setNewSource((s) => ({ ...s, source_type: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
              >
                <option value="LINKEDIN">LINKEDIN (Fresh Jobs & Internships)</option>
                <option value="INTERNSHALA">INTERNSHALA (Internships & Fresher Roles)</option>
                <option value="NAUKRI">NAUKRI (India Jobs & Internships)</option>
                <option value="GREENHOUSE">GREENHOUSE (Direct Company Career Board)</option>
                <option value="LEVER">LEVER (Direct Company Career Board)</option>
                <option value="ASHBY">ASHBY (Direct Company Career Board)</option>
                <option value="DIRECT_CAREER">DIRECT_CAREER (Workday / SmartRecruiters / JSON-LD Career Page)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Board Slug or Query (e.g. `AI Intern|Hyderabad` or `machine-learning-internship` or `openai`)
              </label>
              <input
                type="text"
                value={newSource.external_company_id}
                onChange={(e) => setNewSource((s) => ({ ...s, external_company_id: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Career Page / Platform URL</label>
              <input
                type="url"
                placeholder="https://..."
                value={newSource.career_url}
                onChange={(e) => setNewSource((s) => ({ ...s, career_url: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2"
              />
            </div>
          </div>
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => setShowAdd(false)}
              className="px-4 py-2 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !newSource.company || !newSource.external_company_id}
              className="px-4 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Save Source
            </button>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{activeSources.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Active Sources</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{totalJobs.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-0.5">Total Jobs Discovered</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{sources.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Configured Sources</p>
        </div>
      </div>

      {/* Sources Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse h-48" />
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-600 text-center">
          Failed to load sources. Please try again.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {sources.map((source) => (
            <SourceCard key={source.id} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
