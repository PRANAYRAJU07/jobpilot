'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard, Briefcase, FileText, Activity, Mail,
  User, Settings, Bell, ChevronRight, Database, LogOut,
  Inbox, Star, ClipboardList
} from 'lucide-react';
import { clsx } from 'clsx';
import { useState } from 'react';

const navGroups = [
  {
    label: 'Main',
    items: [
      { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Jobs', href: '/jobs', icon: Briefcase },
      { name: 'Applications', href: '/applications', icon: FileText },
      { name: 'Activity', href: '/activity', icon: Activity },
    ]
  },
  {
    label: 'Communications',
    items: [
      { name: 'Gmail', href: '/gmail', icon: Mail },
      { name: 'Emails', href: '/emails', icon: Inbox },
      { name: 'Interviews', href: '/interviews', icon: Star },
      { name: 'Assessments', href: '/assessments', icon: ClipboardList },
      { name: 'Notifications', href: '/notifications', icon: Bell },
    ]
  },
  {
    label: 'Profile & Settings',
    items: [
      { name: 'Profile', href: '/profile', icon: User },
      { name: 'Resume', href: '/resume', icon: FileText },
      { name: 'Settings', href: '/settings', icon: Settings },
    ]
  }
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <div className="w-64 bg-gray-950 h-screen text-white flex flex-col fixed left-0 top-0 z-30 border-r border-gray-800">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">J</div>
          <span className="text-lg font-semibold tracking-tight">JobPilot AI</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-6">
        {navGroups.map((group) => (
          <div key={group.label}>
            <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={clsx(
                      'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    )}
                  >
                    <item.icon className="mr-3 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-gray-800">
        <Link
          href="/settings/job-sources"
          className="flex items-center px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <Database className="mr-3 h-4 w-4" />
          Job Sources
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center w-full px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors mt-0.5"
        >
          <LogOut className="mr-3 h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
