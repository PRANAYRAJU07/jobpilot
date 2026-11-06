'use client';

import { Star } from 'lucide-react';
import Link from 'next/link';

export default function InterviewsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Interviews</h1>
        <p className="text-sm text-gray-500 mt-1">Interview invitations detected from your emails</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 py-20 text-center">
        <Star className="h-10 w-10 mx-auto text-gray-200 mb-3" />
        <p className="text-gray-500 font-medium">No interviews detected yet.</p>
        <p className="text-sm text-gray-400 mt-1 max-w-sm mx-auto">
          When recruiters send interview invitations to your connected Gmail, they will appear here automatically.
        </p>
        <Link href="/gmail" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Connect Gmail →
        </Link>
      </div>
    </div>
  );
}
