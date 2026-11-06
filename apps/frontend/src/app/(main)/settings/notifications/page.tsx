'use client';

import Link from 'next/link';
import { ArrowLeft, Save, Send, Mail, MessageSquare, CheckCircle2, Loader2, ExternalLink } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api/sources';

export default function NotificationsSettingsPage() {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [testResult, setTestResult] = useState<any | null>(null);

  const { data: prefs, isLoading } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: notificationsApi.getPreferences,
  });

  const [form, setForm] = useState({
    alert_email: '',
    whatsapp_number: '',
    email_enabled: true,
    whatsapp_enabled: true,
    job_match_enabled: true,
    fresh_only_alerts: true,
    min_match_score_threshold: 60,
    application_updates_enabled: true,
    interview_enabled: true,
    assessment_enabled: true,
    action_required_enabled: true,
    daily_summary_enabled: false,
  });

  useEffect(() => {
    if (prefs) {
      setForm({
        alert_email: prefs.alert_email || '',
        whatsapp_number: prefs.whatsapp_number || '',
        email_enabled: prefs.email_enabled ?? true,
        whatsapp_enabled: prefs.whatsapp_enabled ?? true,
        job_match_enabled: prefs.job_match_enabled ?? true,
        fresh_only_alerts: prefs.fresh_only_alerts ?? true,
        min_match_score_threshold: prefs.min_match_score_threshold ?? 60,
        application_updates_enabled: prefs.application_updates_enabled ?? true,
        interview_enabled: prefs.interview_enabled ?? true,
        assessment_enabled: prefs.assessment_enabled ?? true,
        action_required_enabled: prefs.action_required_enabled ?? true,
        daily_summary_enabled: prefs.daily_summary_enabled ?? false,
      });
    }
  }, [prefs]);

  const updateMutation = useMutation({
    mutationFn: () => notificationsApi.updatePreferences(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const testAlertMutation = useMutation({
    mutationFn: () => notificationsApi.sendTestAlert(),
    onSuccess: (data) => {
      setTestResult(data.result);
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  if (isLoading) {
    return <div className="p-6 text-sm text-gray-500">Loading notification settings...</div>;
  }

  const waDeepLink = testResult?.channels?.whatsapp?.whatsapp_url;

  return (
    <div className="space-y-6 max-w-3xl">
      <Link href="/settings" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        Back to Settings
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email & WhatsApp Job Match Alerts</h1>
          <p className="text-sm text-gray-500 mt-1">
            Receive instant application links via Email and WhatsApp whenever a genuine, freshly posted job matches your resume skills.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => testAlertMutation.mutate()}
            disabled={testAlertMutation.isPending}
            className="flex items-center px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 text-sm font-medium rounded-lg hover:bg-indigo-100 transition-colors"
          >
            {testAlertMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <Send className="h-4 w-4 mr-1.5" />
            )}
            Send Test Alert
          </button>
          <button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
            className="flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {updateMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-1.5" />
            )}
            {saved ? 'Saved!' : 'Save Changes'}
          </button>
        </div>
      </div>

      {testResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 space-y-2 text-sm text-green-900">
          <div className="flex items-center font-semibold">
            <CheckCircle2 className="h-4 w-4 mr-2 text-green-600" />
            Test Job Alert Dispatched!
          </div>
          <p className="text-xs text-green-800">
            Email Status: <strong>{testResult.channels?.email?.status}</strong> ({testResult.channels?.email?.recipient || 'No email set'}) ·
            WhatsApp Status: <strong>{testResult.channels?.whatsapp?.status}</strong> ({testResult.channels?.whatsapp?.recipient || 'No number set'})
          </p>
          {waDeepLink && (
            <div className="pt-1">
              <a
                href={waDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-700"
              >
                <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                Open Formatted Alert in WhatsApp Now
              </a>
            </div>
          )}
        </div>
      )}

      {/* Direct Delivery Channels (Email & WhatsApp) */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
        <h2 className="text-base font-semibold text-gray-900">Direct Delivery Channels</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg border border-gray-200 bg-gray-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center text-sm font-semibold text-gray-900">
                <Mail className="h-4 w-4 mr-2 text-blue-600" />
                Email Job Link Alerts
              </span>
              <input
                type="checkbox"
                checked={form.email_enabled}
                onChange={(e) => setForm((f) => ({ ...f, email_enabled: e.target.checked }))}
                className="w-4 h-4 text-blue-600 rounded"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Target Email Address</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={form.alert_email}
                onChange={(e) => setForm((f) => ({ ...f, alert_email: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
              />
            </div>
          </div>

          <div className="p-4 rounded-lg border border-gray-200 bg-gray-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center text-sm font-semibold text-gray-900">
                <MessageSquare className="h-4 w-4 mr-2 text-green-600" />
                WhatsApp Job Link Alerts
              </span>
              <input
                type="checkbox"
                checked={form.whatsapp_enabled}
                onChange={(e) => setForm((f) => ({ ...f, whatsapp_enabled: e.target.checked }))}
                className="w-4 h-4 text-green-600 rounded"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">WhatsApp Number (with Country Code)</label>
              <input
                type="tel"
                placeholder="+91 9876543210"
                value={form.whatsapp_number}
                onChange={(e) => setForm((f) => ({ ...f, whatsapp_number: e.target.value }))}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
              />
            </div>
          </div>
        </div>

        {/* Cross-Validation Threshold & Freshness Rules */}
        <div className="pt-4 border-t border-gray-100 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900">Cross-Validation & Freshness Filtering Rules</h3>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">Minimum Skill Match Score for Alert ({form.min_match_score_threshold}%)</p>
              <p className="text-xs text-gray-500">Only send Email/WhatsApp links when cross-validated skill match meets or exceeds this score</p>
            </div>
            <input
              type="range"
              min={30}
              max={95}
              step={5}
              value={form.min_match_score_threshold}
              onChange={(e) => setForm((f) => ({ ...f, min_match_score_threshold: parseInt(e.target.value, 10) }))}
              className="w-40 accent-blue-600"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">Freshly Posted Jobs & Internships Only (≤ 72 Hours)</p>
              <p className="text-xs text-gray-500">Prioritize newly posted openings from career pages, LinkedIn, Internshala, and Naukri</p>
            </div>
            <input
              type="checkbox"
              checked={form.fresh_only_alerts}
              onChange={(e) => setForm((f) => ({ ...f, fresh_only_alerts: e.target.checked }))}
              className="w-4 h-4 text-blue-600 rounded"
            />
          </div>
        </div>
      </div>

      {/* Lifecycle Event Checkboxes */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <h2 className="text-base font-semibold text-gray-900">Application Lifecycle Categories</h2>
        {[
          { key: 'job_match_enabled', label: 'Verified Skill-Matched Jobs & Internships', desc: 'Instant link when a genuine, domain-suitable job matches your resume skills' },
          { key: 'application_updates_enabled', label: 'Application Confirmations', desc: 'When a company confirms receipt of your application' },
          { key: 'interview_enabled', label: 'Interview Invitations', desc: 'When you are invited to a technical or HR interview' },
          { key: 'assessment_enabled', label: 'Online Coding Assessments', desc: 'When you receive a HackerRank, Codility, or take-home challenge' },
          { key: 'action_required_enabled', label: 'Action Required Alerts', desc: 'When manual verification (OTP/CAPTCHA) is needed' },
        ].map((item) => (
          <div key={item.key} className="flex items-start">
            <input
              id={item.key}
              type="checkbox"
              checked={Boolean(form[item.key as keyof typeof form])}
              onChange={(e) => setForm((f) => ({ ...f, [item.key]: e.target.checked }))}
              className="w-4 h-4 mt-1 text-blue-600 border-gray-300 rounded"
            />
            <div className="ml-3 text-sm">
              <label htmlFor={item.key} className="font-medium text-gray-800">{item.label}</label>
              <p className="text-xs text-gray-500">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
