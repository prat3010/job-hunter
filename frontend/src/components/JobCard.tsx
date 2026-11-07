"use client";

import { JobLead, KanbanStatus } from "@/lib/types";
import { 
  Building2, 
  ExternalLink, 
  Mail, 
  Sparkles, 
  DollarSign, 
  ChevronRight,
  Trash2
} from "lucide-react";

interface JobCardProps {
  job: JobLead;
  onSelect: (job: JobLead) => void;
  onStatusChange: (jobId: string, status: KanbanStatus) => void;
  onDelete: (jobId: string) => void;
}

export function JobCard({ job, onSelect, onStatusChange, onDelete }: JobCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-emerald-400 bg-emerald-950/60 border-emerald-800/60";
    if (score >= 70) return "text-cyan-400 bg-cyan-950/60 border-cyan-800/60";
    return "text-amber-400 bg-amber-950/60 border-amber-800/60";
  };

  const getTierColor = (tier: string) => {
    if (tier.startsWith("A+")) return "text-emerald-300 bg-emerald-950/80 border-emerald-700/50";
    if (tier.startsWith("B")) return "text-cyan-300 bg-cyan-950/80 border-cyan-700/50";
    return "text-slate-400 bg-slate-900 border-slate-800";
  };

  const statusOptions: { value: KanbanStatus; label: string }[] = [
    { value: "discovered", label: "Discovered" },
    { value: "shortlisted", label: "Shortlisted" },
    { value: "pitch_generated", label: "Pitch Ready" },
    { value: "applied", label: "Applied" },
    { value: "interviewing", label: "Interviewing" },
    { value: "archived", label: "Archive" },
  ];

  return (
    <div className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm hover:border-slate-700 hover:bg-slate-900 hover:shadow-md transition-all">
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Score */}
            <span
              className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-bold border ${getScoreColor(
                job.quality_score
              )}`}
            >
              <Sparkles className="h-3 w-3" />
              {job.quality_score}%
            </span>

            {/* Propensity Tier */}
            <span
              className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold border ${getTierColor(
                job.propensity_tier
              )}`}
            >
              {job.propensity_tier}
            </span>

            {/* Lead Type */}
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
                job.lead_type === "client"
                  ? "bg-purple-950/70 text-purple-300 border border-purple-800/50"
                  : "bg-blue-950/70 text-blue-300 border border-blue-800/50"
              }`}
            >
              {job.lead_type === "client" ? "Freelance/Contract" : "Full-Time"}
            </span>
          </div>

          {/* External Link */}
          <a
            href={job.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1"
            title="Open original job posting"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>

        {/* Role & Company */}
        <h4 
          onClick={() => onSelect(job)}
          className="font-semibold text-slate-100 text-sm hover:text-cyan-400 cursor-pointer transition-colors line-clamp-1"
        >
          {job.role}
        </h4>

        <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
          <Building2 className="h-3.5 w-3.5 text-slate-500" />
          <span className="font-medium text-slate-300">{job.company}</span>
          <span className="text-slate-600">•</span>
          <span className="text-[11px] text-slate-500">{job.intent_source}</span>
        </div>

        {/* Compensation (if present) */}
        {job.compensation && (
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium mt-2 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-900/30 w-fit">
            <DollarSign className="h-3 w-3 -mr-0.5" />
            <span>{job.compensation}</span>
            {job.compensation_inr && (
              <span className="text-emerald-500/80 text-[10px]">({job.compensation_inr})</span>
            )}
          </div>
        )}

        {/* Verification Reasoning / Snippet */}
        {job.verification_reason && (
          <p className="mt-2 text-[11px] text-slate-400 line-clamp-2 bg-slate-950/40 p-1.5 rounded border border-slate-800/60 font-mono">
            {job.verification_reason}
          </p>
        )}
      </div>

      {/* Footer Actions */}
      <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        {/* Status Dropdown */}
        <select
          value={job.status}
          onChange={(e) => onStatusChange(job.id, e.target.value as KanbanStatus)}
          onClick={(e) => e.stopPropagation()}
          className="rounded bg-slate-950 text-slate-300 text-[11px] px-2 py-1 border border-slate-700/80 focus:border-cyan-500 focus:outline-none cursor-pointer"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Pitch Button / Inspect */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onSelect(job)}
            className="flex items-center gap-1 rounded bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-800/60 px-2 py-1 text-[11px] font-medium transition-all"
          >
            <Sparkles className="h-3 w-3" />
            <span>{job.pitch_email ? "Pitch Ready" : "Generate Pitch"}</span>
            <ChevronRight className="h-3 w-3 -ml-0.5" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(job.id);
            }}
            className="p-1 text-slate-500 hover:text-rose-400 transition-colors rounded hover:bg-rose-950/30"
            title="Dismiss lead"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
