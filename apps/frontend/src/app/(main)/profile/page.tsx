'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profileApi } from '@/lib/api/profile';
import { Save, User, Loader2, CheckCircle, GraduationCap, Link as LinkIcon, Code } from 'lucide-react';

function Field({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm font-medium text-gray-900">{value ?? <span className="text-gray-400">—</span>}</p>
    </div>
  );
}

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
  });

  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    github: '',
    linkedin: '',
    education: '',
    cgpa: '',
    graduation_year: '',
  });

  const startEditing = () => {
    if (!profile) return;
    setForm({
      full_name: profile.full_name || '',
      phone: profile.phone || '',
      github: profile.github || '',
      linkedin: profile.linkedin || '',
      education: profile.education || '',
      cgpa: profile.cgpa != null ? String(profile.cgpa) : '',
      graduation_year: profile.graduation_year != null ? String(profile.graduation_year) : '',
    });
    setEditing(true);
    setSaved(false);
    setFormError(null);
  };

  const updateMutation = useMutation({
    mutationFn: () => profileApi.updateProfile({
      full_name: form.full_name,
      phone: form.phone || undefined,
      github: form.github || undefined,
      linkedin: form.linkedin || undefined,
      education: form.education || undefined,
      cgpa: form.cgpa ? parseFloat(form.cgpa) : undefined,
      graduation_year: form.graduation_year ? parseInt(form.graduation_year) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setEditing(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || 'Failed to save profile.');
    },
  });

  if (isLoading) {
    return (
      <div className="max-w-3xl animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 bg-gray-200 rounded-full" />
            <div className="space-y-2">
              <div className="h-6 bg-gray-200 rounded w-48" />
              <div className="h-4 bg-gray-100 rounded w-64" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="max-w-3xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-700 font-medium">No profile found.</p>
          <p className="text-sm text-yellow-600 mt-1">Please contact support or set up your profile through the API.</p>
        </div>
      </div>
    );
  }

  const initials = profile.full_name
    ? profile.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : 'P';

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Candidate Profile</h1>
        <div className="flex items-center space-x-2">
          {saved && (
            <span className="flex items-center text-green-600 text-sm font-medium">
              <CheckCircle className="h-4 w-4 mr-1" /> Saved
            </span>
          )}
          {!editing ? (
            <button onClick={startEditing} className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
              Edit Profile
            </button>
          ) : (
            <div className="flex space-x-2">
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-gray-600 border border-gray-200 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
                className="flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {updateMutation.isPending ? <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> : <Save className="h-4 w-4 mr-1.5" />}
                Save
              </button>
            </div>
          )}
        </div>
      </div>

      {formError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{formError}</div>
      )}

      {/* Profile Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-6 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-white font-bold text-xl">
              {initials}
            </div>
            <div className="text-white">
              <h2 className="text-xl font-bold">{profile.full_name}</h2>
              <p className="text-blue-100 text-sm mt-0.5">{profile.education || 'Education not set'}</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          {editing ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { field: 'full_name', label: 'Full Name', type: 'text' },
                  { field: 'phone', label: 'Phone', type: 'tel' },
                  { field: 'education', label: 'Education', type: 'text' },
                  { field: 'github', label: 'GitHub URL', type: 'url' },
                  { field: 'linkedin', label: 'LinkedIn URL', type: 'url' },
                  { field: 'cgpa', label: 'CGPA', type: 'number' },
                  { field: 'graduation_year', label: 'Graduation Year', type: 'number' },
                ].map(({ field, label, type }) => (
                  <div key={field} className={field === 'education' ? 'md:col-span-2' : ''}>
                    <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                    <input
                      type={type}
                      value={form[field as keyof typeof form]}
                      onChange={e => setForm(prev => ({ ...prev, [field]: e.target.value }))}
                      className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center"><User className="h-4 w-4 mr-2 text-gray-400" />Personal</h3>
                <Field label="Full Name" value={profile.full_name} />
                <Field label="Phone" value={profile.phone} />
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center"><GraduationCap className="h-4 w-4 mr-2 text-gray-400" />Education</h3>
                <Field label="Degree / Program" value={profile.education} />
                <Field label="CGPA" value={profile.cgpa != null ? `${profile.cgpa} / 10` : null} />
                <Field label="Graduation Year" value={profile.graduation_year} />
              </div>

              <div className="md:col-span-2 space-y-3">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center"><Code className="h-4 w-4 mr-2 text-gray-400" />Links</h3>
                <div className="flex flex-wrap gap-3">
                  {profile.github && (
                    <a href={profile.github} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1.5 text-sm text-blue-600 hover:underline">
                      <LinkIcon className="h-4 w-4" />
                      <span>GitHub</span>
                    </a>
                  )}
                  {profile.linkedin && (
                    <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1.5 text-sm text-blue-600 hover:underline">
                      <LinkIcon className="h-4 w-4" />
                      <span>LinkedIn</span>
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
