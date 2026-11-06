'use client';

import Link from 'next/link';
import { Settings, Database, Bell, Cpu, User } from 'lucide-react';
import { usePathname } from 'next/navigation';

const settingsNav = [
  { name: 'Job Sources', href: '/settings/job-sources', icon: Database, description: 'Configure and monitor job discovery sources' },
  { name: 'Notifications', href: '/settings/notifications', icon: Bell, description: 'Control how and when you receive notifications' },
  { name: 'Automation', href: '/settings/automation', icon: Cpu, description: 'Manage automated application settings and kill switches' },
  { name: 'Account', href: '/settings/account', icon: User, description: 'Account and security settings' },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Configure JobPilot AI system behavior</p>
      </div>

      <div className="space-y-3">
        {settingsNav.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className="flex items-center p-5 bg-white rounded-xl border border-gray-200 hover:shadow-md hover:border-blue-200 transition-all group"
          >
            <div className="w-10 h-10 bg-gray-100 group-hover:bg-blue-50 rounded-lg flex items-center justify-center transition-colors">
              <item.icon className="h-5 w-5 text-gray-500 group-hover:text-blue-600 transition-colors" />
            </div>
            <div className="ml-4 flex-1">
              <p className="font-medium text-gray-900">{item.name}</p>
              <p className="text-sm text-gray-500 mt-0.5">{item.description}</p>
            </div>
            <Settings className="h-4 w-4 text-gray-300 group-hover:text-blue-400 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
