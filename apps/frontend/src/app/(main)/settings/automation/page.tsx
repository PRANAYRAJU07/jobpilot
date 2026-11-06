'use client';

import Link from 'next/link';
import { ArrowLeft, Cpu, ShieldOff, Clock, AlertTriangle } from 'lucide-react';

export default function AutomationSettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <Link href="/settings" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        Back to Settings
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Automation</h1>
        <p className="text-sm text-gray-500 mt-1">Control the automated application system</p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-start space-x-3">
        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-yellow-800">Automation Disabled — Phase 16</p>
          <p className="text-sm text-yellow-700 mt-0.5">Automated application submission is not enabled in this phase. The system is in discovery and matching mode only. No applications will be submitted without explicit user approval.</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">System Status</h2>
        <div className="space-y-3">
          {[
            { label: 'Job Discovery', status: 'Running', color: 'bg-green-100 text-green-700' },
            { label: 'JD Analysis', status: 'Running', color: 'bg-green-100 text-green-700' },
            { label: 'Eligibility Matching', status: 'Running', color: 'bg-green-100 text-green-700' },
            { label: 'Application Submission', status: 'Disabled', color: 'bg-gray-100 text-gray-500' },
            { label: 'Auto-Submit', status: 'Disabled', color: 'bg-gray-100 text-gray-500' },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <span className="text-sm text-gray-700">{item.label}</span>
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${item.color}`}>{item.status}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Kill Switches</h2>
        <div className="space-y-3">
          {[
            { label: 'Stop All Discovery', description: 'Pause Celery Beat from scheduling new source scans' },
            { label: 'Stop All Applications', description: 'Immediately halt any in-progress application submissions' },
            { label: 'Emergency Reset', description: 'Reset all application states to safe stopped condition' },
          ].map((item) => (
            <div key={item.label} className="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-800">{item.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
              </div>
              <button className="ml-4 flex-shrink-0 px-3 py-1.5 text-xs text-red-600 border border-red-200 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                Trigger
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
