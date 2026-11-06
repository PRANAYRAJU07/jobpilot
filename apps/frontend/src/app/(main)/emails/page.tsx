'use client';

import { Inbox } from 'lucide-react';
import Link from 'next/link';

export default function EmailsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Classified Emails</h1>
        <p className="text-sm text-gray-500 mt-1">Job-related emails automatically detected from your Gmail</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 py-20 text-center">
        <Inbox className="h-10 w-10 mx-auto text-gray-200 mb-3" />
        <p className="text-gray-500 font-medium">No classified emails yet.</p>
        <p className="text-sm text-gray-400 mt-1 max-w-sm mx-auto">
          Connect your Gmail account to start automatically tracking application emails.
        </p>
        <Link href="/gmail" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Connect Gmail →
        </Link>
      </div>
    </div>
  );
}
