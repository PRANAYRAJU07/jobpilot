'use client';

import { ClipboardList } from 'lucide-react';
import Link from 'next/link';

export default function AssessmentsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Assessments</h1>
        <p className="text-sm text-gray-500 mt-1">Technical assessments detected from your emails</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 py-20 text-center">
        <ClipboardList className="h-10 w-10 mx-auto text-gray-200 mb-3" />
        <p className="text-gray-500 font-medium">No assessments detected yet.</p>
        <p className="text-sm text-gray-400 mt-1 max-w-sm mx-auto">
          When companies send assessment invitations or coding challenges to your connected Gmail, they will appear here with deadlines.
        </p>
        <Link href="/gmail" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Connect Gmail →
        </Link>
      </div>
    </div>
  );
}
