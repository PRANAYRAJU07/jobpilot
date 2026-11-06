'use client';

import Link from 'next/link';
import { ArrowLeft, User as UserIcon, Shield, Key } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/lib/api/profile';

export default function AccountSettingsPage() {
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <Link href="/settings" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4 mr-1.5" />
        Back to Settings
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your account details and security</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 flex items-center border-b pb-2 mb-4">
            <UserIcon className="h-4 w-4 mr-2 text-gray-400" /> Account Information
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Email Address</p>
              <p className="text-sm font-medium mt-1">user@example.com (API does not expose email yet)</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Account ID</p>
              <p className="text-sm font-mono mt-1 text-gray-600">{profile?.user_id || 'Loading...'}</p>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-gray-900 flex items-center border-b pb-2 mb-4">
            <Shield className="h-4 w-4 mr-2 text-gray-400" /> Security
          </h2>
          <button className="flex items-center px-4 py-2 bg-white border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
            <Key className="h-4 w-4 mr-2 text-gray-500" />
            Change Password
          </button>
        </div>
        
        <div className="pt-4 border-t border-gray-100">
          <button className="text-sm text-red-600 hover:text-red-700 font-medium">
            Delete Account
          </button>
          <p className="text-xs text-gray-500 mt-1">Permanently delete your account and all data.</p>
        </div>
      </div>
    </div>
  );
}
