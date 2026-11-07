"use client";

import { JobLead, KanbanStatus } from "@/lib/types";
import { JobCard } from "./JobCard";
import { 
  Inbox, 
  Bookmark, 
  Sparkles, 
  Send, 
  UserCheck 
} from "lucide-react";

interface KanbanBoardProps {
  jobs: JobLead[];
  onSelectJob: (job: JobLead) => void;
  onStatusChange: (jobId: string, status: KanbanStatus) => void;
  onDeleteJob: (jobId: string) => void;
}

const COLUMNS: { id: KanbanStatus; title: string; icon: any; color: string }[] = [
  { id: "discovered", title: "Discovered", icon: Inbox, color: "text-slate-400 bg-slate-800" },
  { id: "shortlisted", title: "Shortlisted", icon: Bookmark, color: "text-cyan-400 bg-cyan-950/70 border-cyan-800/40" },
  { id: "pitch_generated", title: "Pitch Ready", icon: Sparkles, color: "text-indigo-400 bg-indigo-950/70 border-indigo-800/40" },
  { id: "applied", title: "Applied", icon: Send, color: "text-amber-400 bg-amber-950/70 border-amber-800/40" },
  { id: "interviewing", title: "Interviewing", icon: UserCheck, color: "text-emerald-400 bg-emerald-950/70 border-emerald-800/40" },
];

export function KanbanBoard({ jobs, onSelectJob, onStatusChange, onDeleteJob }: KanbanBoardProps) {
  const getJobsByStatus = (status: KanbanStatus) => {
    return jobs.filter((j) => j.status === status);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 items-start">
      {COLUMNS.map((col) => {
        const colJobs = getJobsByStatus(col.id);
        const Icon = col.icon;

        return (
          <div
            key={col.id}
            className="flex flex-col rounded-xl border border-slate-800/80 bg-slate-950/50 p-3 min-h-[500px]"
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className={`p-1 rounded border ${col.color}`}>
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <h3 className="font-semibold text-xs text-slate-200 tracking-wide uppercase">
                  {col.title}
                </h3>
              </div>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[11px] font-bold text-slate-400">
                {colJobs.length}
              </span>
            </div>

            {/* Cards Container */}
            <div className="flex flex-col gap-3 overflow-y-auto max-h-[calc(100vh-280px)] pr-1">
              {colJobs.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 rounded-lg border border-dashed border-slate-800/60 text-center my-auto">
                  <Icon className="h-6 w-6 text-slate-700 mb-2" />
                  <p className="text-xs text-slate-500 font-medium">No leads in {col.title.toLowerCase()}</p>
                </div>
              ) : (
                colJobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    onSelect={onSelectJob}
                    onStatusChange={onStatusChange}
                    onDelete={onDeleteJob}
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
