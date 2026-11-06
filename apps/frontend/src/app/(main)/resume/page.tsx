'use client';

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  documentsApi,
  profileApi,
  type UploadedDocument,
  type CandidateSkill,
  type CandidateProject,
} from '@/lib/api/profile';
import {
  FileText,
  Upload,
  CheckCircle2,
  Sparkles,
  Plus,
  Trash2,
  RefreshCw,
  Loader2,
  ShieldCheck,
  Briefcase,
  Award,
} from 'lucide-react';
import { format } from 'date-fns';

export default function ResumePage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('AI/ML & Data Science');
  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [rematchSummary, setRematchSummary] = useState<any | null>(null);

  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getDocuments,
  });

  const { data: skills = [], isLoading: skillsLoading } = useQuery({
    queryKey: ['profile-skills'],
    queryFn: profileApi.getSkills,
  });

  const { data: projects = [] } = useQuery({
    queryKey: ['profile-projects'],
    queryFn: profileApi.getProjects,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.uploadResume(file),
    onSuccess: (data) => {
      setUploadResult(data);
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['profile-skills'] });
      queryClient.invalidateQueries({ queryKey: ['profile-projects'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || 'Failed to upload and parse resume.');
    },
  });

  const addSkillMutation = useMutation({
    mutationFn: () => profileApi.addSkill(newSkillName, newSkillCategory),
    onSuccess: () => {
      setNewSkillName('');
      queryClient.invalidateQueries({ queryKey: ['profile-skills'] });
    },
  });

  const deleteSkillMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteSkill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile-skills'] });
    },
  });

  const rematchMutation = useMutation({
    mutationFn: () => profileApi.triggerRematch(true),
    onSuccess: (data) => {
      setRematchSummary(data.summary);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  // Group skills by category
  const skillsByCategory = skills.reduce<Record<string, CandidateSkill[]>>((acc, s) => {
    const cat = s.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(s);
    return acc;
  }, {});

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume & Skill Intelligence Hub</h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload your resume (PDF, DOCX, or TXT) to automatically learn your skills, projects, and domain focus, then cross-validate against fresh jobs.
          </p>
        </div>

        <button
          onClick={() => rematchMutation.mutate()}
          disabled={rematchMutation.isPending}
          className="inline-flex items-center px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {rematchMutation.isPending ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Cross-Validate All Jobs & Send Alerts
        </button>
      </div>

      {/* Upload Box */}
      <div className="bg-white rounded-xl border-2 border-dashed border-blue-200 p-8 text-center hover:border-blue-400 transition-colors">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
          {uploadMutation.isPending ? (
            <Loader2 className="h-7 w-7 animate-spin" />
          ) : (
            <Upload className="h-7 w-7" />
          )}
        </div>
        <h2 className="text-base font-semibold text-gray-900">
          {uploadMutation.isPending ? 'Analyzing Resume & Learning Skills...' : 'Upload Master Resume (PDF, DOCX, TXT)'}
        </h2>
        <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
          JobPilot extracts your technical skills, projects, CGPA, graduation year, and domain specialization, then cross-validates every discovered job and dispatches Email & WhatsApp links.
        </p>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending}
          className="mt-4 inline-flex items-center px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Upload className="h-4 w-4 mr-2" />
          Select Resume File
        </button>
      </div>

      {uploadError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
          {uploadError}
        </div>
      )}

      {/* Instant Upload & Cross-Validation Summary Banner */}
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-green-800 font-semibold">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span>Resume Parsed & Cross-Validated: {uploadResult.filename}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-white rounded-lg p-3 border border-green-100">
              <p className="text-xs text-gray-500">Skills Learned</p>
              <p className="text-xl font-bold text-gray-900">{uploadResult.parse_summary?.skills_count ?? 0}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-100">
              <p className="text-xs text-gray-500">Projects Extracted</p>
              <p className="text-xl font-bold text-gray-900">{uploadResult.parse_summary?.projects_extracted ?? 0}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-100">
              <p className="text-xs text-gray-500">Jobs Cross-Validated</p>
              <p className="text-xl font-bold text-green-700">
                {uploadResult.rematch_summary?.cross_validation_passed_jobs ?? 0}
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-green-100">
              <p className="text-xs text-gray-500">Alerts Dispatched</p>
              <p className="text-xl font-bold text-blue-700">
                {uploadResult.rematch_summary?.alerts_dispatched ?? 0}
              </p>
            </div>
          </div>
          {uploadResult.parse_summary?.inferred_domains && (
            <p className="text-xs text-green-800">
              <strong>Inferred Domain Focus:</strong> {uploadResult.parse_summary.inferred_domains.join(', ')}
            </p>
          )}
        </div>
      )}

      {rematchSummary && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 flex items-center justify-between text-sm text-indigo-900">
          <div>
            <strong>Cross-Validation Complete:</strong> Evaluated {rematchSummary.total_jobs_evaluated} jobs ·{' '}
            <span className="text-green-700 font-semibold">{rematchSummary.cross_validation_passed_jobs} passed skill & domain validation</span> ·{' '}
            <span className="text-indigo-700 font-semibold">{rematchSummary.alerts_dispatched} Email/WhatsApp alerts sent</span>.
          </div>
        </div>
      )}

      {/* Uploaded Documents List */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="h-4 w-4 mr-2 text-blue-600" />
          Uploaded Resume Documents ({documents.length})
        </h2>
        {docsLoading ? (
          <p className="text-sm text-gray-400">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-gray-500">No resume uploaded yet. Upload a PDF or DOCX above to get started.</p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc: UploadedDocument) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3.5 rounded-lg border border-gray-100 bg-gray-50"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-xs text-gray-500">
                      Uploaded {doc.upload_timestamp ? format(new Date(doc.upload_timestamp), 'MMM d, yyyy h:mm a') : 'recently'}
                      {doc.parsed_metadata?.skills_count != null && ` · ${doc.parsed_metadata.skills_count} skills learned`}
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <ShieldCheck className="h-3.5 w-3.5 mr-1" />
                  {doc.verification_status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Learned Skills & Evidence Graph */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-900 flex items-center">
              <Sparkles className="h-4 w-4 mr-2 text-indigo-600" />
              Learned Candidate Skills & Evidence Graph ({skills.length})
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              These verified skills are cross-validated against every discovered job requirement before triggering Email or WhatsApp alerts.
            </p>
          </div>

          {/* Add Custom Skill */}
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Add skill (e.g. LangChain)"
              value={newSkillName}
              onChange={(e) => setNewSkillName(e.target.value)}
              className="text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={newSkillCategory}
              onChange={(e) => setNewSkillCategory(e.target.value)}
              className="text-xs border border-gray-200 rounded-lg px-2.5 py-2 bg-white"
            >
              <option value="AI/ML & Data Science">AI/ML & Data Science</option>
              <option value="GenAI & LLMs">GenAI & LLMs</option>
              <option value="Programming Languages">Programming</option>
              <option value="Backend & APIs">Backend & APIs</option>
              <option value="Frontend & Mobile">Frontend</option>
              <option value="Databases & Storage">Databases</option>
              <option value="Cloud, DevOps & MLOps">Cloud & DevOps</option>
            </select>
            <button
              onClick={() => newSkillName.trim() && addSkillMutation.mutate()}
              disabled={addSkillMutation.isPending || !newSkillName.trim()}
              className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Plus className="h-3.5 w-3.5 mr-1" />
              Add
            </button>
          </div>
        </div>

        {skillsLoading ? (
          <p className="text-sm text-gray-400">Loading learned skills...</p>
        ) : Object.keys(skillsByCategory).length === 0 ? (
          <p className="text-sm text-gray-500">No skills learned yet. Upload your resume above or add skills manually.</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(skillsByCategory).map(([category, catSkills]) => (
              <div key={category} className="border border-gray-100 rounded-lg p-4 bg-gray-50/60">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2.5">
                  {category} ({catSkills.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {catSkills.map((sk) => (
                    <div
                      key={sk.id}
                      className="group inline-flex items-center space-x-1.5 bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-xs shadow-2xs"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-600 flex-shrink-0" />
                      <span className="font-medium text-gray-800">{sk.name}</span>
                      {sk.evidence && sk.evidence.length > 0 && (
                        <span className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                          {sk.evidence[0]}
                        </span>
                      )}
                      <button
                        onClick={() => deleteSkillMutation.mutate(sk.id)}
                        className="text-gray-300 hover:text-red-500 ml-1 transition-colors"
                        title="Remove skill"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extracted Projects */}
      {projects.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center">
            <Briefcase className="h-4 w-4 mr-2 text-blue-600" />
            Verified Projects Backing Your Skills ({projects.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((p: CandidateProject) => (
              <div key={p.id} className="p-4 rounded-lg border border-gray-100 bg-gray-50">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center">
                  <Award className="h-4 w-4 mr-1.5 text-indigo-600 flex-shrink-0" />
                  {p.title}
                </h3>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
