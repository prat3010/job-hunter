"use client";

import { useState } from "react";
import { JobLead, KanbanStatus, PitchResponse } from "@/lib/types";
import { api } from "@/lib/api";
import { 
  X, 
  Sparkles, 
  ExternalLink, 
  Mail, 
  Copy, 
  Check, 
  Send, 
  Building2, 
  DollarSign, 
  RefreshCw,
  FileText
} from "lucide-react";

interface LeadDrawerProps {
  job: JobLead | null;
  onClose: () => void;
  onUpdate: (updatedJob: JobLead) => void;
}

export function LeadDrawer({ job, onClose, onUpdate }: LeadDrawerProps) {
  if (!job) return null;

  const [activeTab, setActiveTab] = useState<"email" | "linkedin" | "elevator">("email");
  const [focusAngle, setFocusAngle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedTab, setCopiedTab] = useState<string | null>(null);
  const [notes, setNotes] = useState(job.notes || "");
  const [isSavingNotes, setIsSavingNotes] = useState(false);

  // Local pitches state
  const [pitches, setPitches] = useState<{
    email: string;
    linkedin: string;
    elevator: string;
  }>({
    email: job.pitch_email || "",
    linkedin: job.pitch_linkedin || "",
    elevator: job.pitch_elevator || "",
  });

  const handleGeneratePitch = async () => {
    setIsGenerating(true);
    try {
      const res: PitchResponse = await api.generatePitch(job.id, focusAngle);
      setPitches({
        email: res.email,
        linkedin: res.linkedin,
        elevator: res.elevator_pitch,
      });
      onUpdate({
        ...job,
        pitch_email: res.email,
        pitch_linkedin: res.linkedin,
        pitch_elevator: res.elevator_pitch,
        status: job.status === "discovered" || job.status === "shortlisted" ? "pitch_generated" : job.status,
      });
    } catch (err: any) {
      alert(`Pitch generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = (text: string, tab: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTab(tab);
    setTimeout(() => setCopiedTab(null), 2000);
  };

  const handleSaveNotes = async () => {
    setIsSavingNotes(true);
    try {
      const updated = await api.updateJob(job.id, { notes });
      onUpdate(updated);
    } catch (err: any) {
      alert(`Failed to save notes: ${err.message}`);
    } finally {
      setIsSavingNotes(false);
    }
  };

  const handleStatusChange = async (status: KanbanStatus) => {
    try {
      const updated = await api.updateJob(job.id, { status });
      onUpdate(updated);
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      {/* Backdrop click to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Drawer Panel */}
      <div className="relative flex h-full w-full max-w-2xl flex-col border-l border-slate-800 bg-slate-900 shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-slate-900/95 px-6 py-4 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <span className="rounded bg-cyan-950 px-2 py-0.5 text-xs font-bold text-cyan-400 border border-cyan-800/60">
              {job.quality_score}% Match
            </span>
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300">
              {job.propensity_tier}
            </span>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 space-y-6 p-6">
          {/* Job Overview */}
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{job.role}</h2>
            <div className="mt-1 flex items-center gap-2 text-sm text-slate-400">
              <Building2 className="h-4 w-4 text-slate-500" />
              <span className="font-semibold text-slate-200">{job.company}</span>
              <span>•</span>
              <span className="text-slate-400">{job.intent_source}</span>
            </div>

            {/* Compensation & Direct Contacts */}
            <div className="mt-3 flex flex-wrap gap-2">
              {job.compensation && (
                <div className="flex items-center gap-1.5 rounded-md bg-emerald-950/40 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-800/40">
                  <DollarSign className="h-3.5 w-3.5" />
                  <span>{job.compensation}</span>
                  {job.compensation_inr && (
                    <span className="text-emerald-500/80">({job.compensation_inr})</span>
                  )}
                </div>
              )}

              {job.email && (
                <a
                  href={`mailto:${job.email}?subject=Regarding ${encodeURIComponent(job.role)} at ${encodeURIComponent(job.company)}`}
                  className="flex items-center gap-1.5 rounded-md bg-cyan-950/40 px-2.5 py-1 text-xs font-semibold text-cyan-300 border border-cyan-800/40 hover:bg-cyan-900/60 transition-colors"
                >
                  <Mail className="h-3.5 w-3.5" />
                  <span>{job.email}</span>
                </a>
              )}

              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
              >
                <span>Original Posting</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>

            {/* Reasoning Pill */}
            {job.verification_reason && (
              <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/60 p-2.5 text-xs text-slate-400 font-mono">
                <span className="text-cyan-400 font-bold block mb-1">Semantic Match Breakdown:</span>
                {job.verification_reason}
              </div>
            )}
          </div>

          {/* Description Snippet */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Posting Snippet
            </h4>
            <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-800/80 bg-slate-950/40 p-3 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap">
              {job.description || job.snippet || "No description provided."}
            </div>
          </div>

          {/* Multi-Channel Pitch Hub */}
          <div className="rounded-xl border border-cyan-900/40 bg-slate-950/70 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-cyan-400" />
                <h3 className="font-bold text-sm text-white">Multi-Channel Pitch Studio</h3>
              </div>

              <div className="flex items-center gap-1">
                {(["email", "linkedin", "elevator"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`rounded px-2.5 py-1 text-xs font-semibold capitalize transition-colors ${
                      activeTab === tab
                        ? "bg-cyan-500 text-slate-950 shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {tab === "elevator" ? "Elevator Pitch" : tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Angle Input & Generate Button */}
            <div className="mt-3 flex items-center gap-2">
              <input
                type="text"
                placeholder="Optional angle: e.g. 'Highlight RAG & sub-300ms latency'..."
                value={focusAngle}
                onChange={(e) => setFocusAngle(e.target.value)}
                className="flex-1 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
              />
              <button
                onClick={handleGeneratePitch}
                disabled={isGenerating}
                className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white shadow hover:from-cyan-400 hover:to-indigo-500 transition-all disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Synthesizing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Generate Pitch</span>
                  </>
                )}
              </button>
            </div>

            {/* Pitch Text Area */}
            <div className="mt-3 relative">
              <textarea
                rows={activeTab === "linkedin" ? 4 : 8}
                value={pitches[activeTab]}
                onChange={(e) => setPitches({ ...pitches, [activeTab]: e.target.value })}
                placeholder={`Click 'Generate Pitch' to create tailored ${activeTab} outreach...`}
                className="w-full rounded-lg border border-slate-800 bg-slate-900/90 p-3 text-xs leading-relaxed text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none resize-none font-sans"
              />

              {activeTab === "linkedin" && (
                <div className="flex justify-between items-center text-[10px] mt-1 px-1">
                  <span className={`${pitches.linkedin.length > 280 ? "text-rose-400 font-bold" : "text-slate-500"}`}>
                    {pitches.linkedin.length} / 280 characters
                  </span>
                  {pitches.linkedin.length > 280 && (
                    <span className="text-rose-400 font-medium">Exceeds LinkedIn connection note limit</span>
                  )}
                </div>
              )}

              {/* Copy & Mailto Buttons */}
              {pitches[activeTab] && (
                <div className="mt-2 flex items-center justify-between">
                  <button
                    onClick={() => handleCopy(pitches[activeTab], activeTab)}
                    className="flex items-center gap-1.5 rounded-md bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 transition-colors"
                  >
                    {copiedTab === activeTab ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied to Clipboard!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Copy {activeTab === "elevator" ? "Pitch" : activeTab}</span>
                      </>
                    )}
                  </button>

                  {activeTab === "email" && job.email && (
                    <a
                      href={`mailto:${job.email}?subject=${encodeURIComponent(`Regarding ${job.role} at ${job.company}`)}&body=${encodeURIComponent(pitches.email)}`}
                      className="flex items-center gap-1.5 rounded-md bg-cyan-600 hover:bg-cyan-500 px-3 py-1.5 text-xs font-bold text-slate-950 transition-colors"
                    >
                      <Send className="h-3.5 w-3.5" />
                      <span>Launch Mail Client</span>
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* User Notes */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Outreach Notes
              </h4>
              <button
                onClick={handleSaveNotes}
                disabled={isSavingNotes}
                className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 disabled:opacity-50"
              >
                {isSavingNotes ? "Saving..." : "Save Notes"}
              </button>
            </div>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Sent cold message to founder on Twitter on Friday..."
              className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:outline-none resize-none"
            />
          </div>

          {/* Kanban Status Transition */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Move Pipeline Status
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {(
                [
                  { id: "discovered", label: "Discovered" },
                  { id: "shortlisted", label: "Shortlisted" },
                  { id: "pitch_generated", label: "Pitch Ready" },
                  { id: "applied", label: "Applied" },
                  { id: "interviewing", label: "Interviewing" },
                  { id: "archived", label: "Archived" },
                ] as const
              ).map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleStatusChange(s.id)}
                  className={`rounded-lg p-2 text-xs font-semibold border text-center transition-all ${
                    job.status === s.id
                      ? "border-cyan-500 bg-cyan-950/60 text-cyan-300 font-bold"
                      : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
