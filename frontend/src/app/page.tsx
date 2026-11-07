"use client";

import { useEffect, useState, useCallback } from "react";
import { Navbar } from "@/components/Navbar";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LeadDrawer } from "@/components/LeadDrawer";
import { LiveScanner } from "@/components/LiveScanner";
import { api } from "@/lib/api";
import { 
  JobLead, 
  JobStats, 
  KanbanStatus, 
  ScanBoardProgress 
} from "@/lib/types";
import { 
  Search, 
  Filter, 
  Sparkles, 
  Layers, 
  Briefcase, 
  UserCheck, 
  Send,
  Zap
} from "lucide-react";

export default function CommandCenterPage() {
  const [jobs, setJobs] = useState<JobLead[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobLead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [leadTypeFilter, setLeadTypeFilter] = useState<string>("all");
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [minScore, setMinScore] = useState<number>(60);

  // Live Scanner state
  const [isScanning, setIsScanning] = useState(false);
  const [scanBoards, setScanBoards] = useState<ScanBoardProgress[]>([]);
  const [scanFoundCount, setScanFoundCount] = useState(0);

  const loadData = useCallback(async () => {
    try {
      const [jobsData, statsData] = await Promise.all([
        api.getJobs({
          search: searchTerm || undefined,
          lead_type: leadTypeFilter !== "all" ? leadTypeFilter : undefined,
          tier: tierFilter !== "all" ? tierFilter : undefined,
          min_score: minScore,
          page_size: 150,
        }),
        api.getJobStats(),
      ]);
      setJobs(jobsData.items);
      setStats(statsData);
    } catch (err: any) {
      console.error("Failed to load jobs:", err);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, leadTypeFilter, tierFilter, minScore]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartScan = async () => {
    setIsScanning(true);
    setScanBoards([]);
    setScanFoundCount(0);

    try {
      // Use Server-Sent Events (SSE) for streaming progress
      const streamUrl = `${api.getBaseUrl()}/api/scan/stream?min_score=${minScore}`;
      const eventSource = new EventSource(streamUrl);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "board_start") {
            setScanBoards((prev) => {
              const existing = prev.find((b) => b.board_id === data.board_id);
              if (existing) {
                return prev.map((b) =>
                  b.board_id === data.board_id ? { ...b, status: "scanning" } : b
                );
              }
              return [
                ...prev,
                {
                  board_id: data.board_id,
                  name: data.name,
                  status: "scanning",
                  found_count: 0,
                },
              ];
            });
          } else if (data.type === "board_complete") {
            setScanBoards((prev) =>
              prev.map((b) =>
                b.board_id === data.board_id
                  ? { ...b, status: "completed", found_count: data.found }
                  : b
              )
            );
            setScanFoundCount((prev) => prev + (data.found || 0));
          } else if (data.type === "board_error") {
            setScanBoards((prev) =>
              prev.map((b) =>
                b.board_id === data.board_id
                  ? { ...b, status: "failed", error: data.error }
                  : b
              )
            );
          } else if (data.type === "scan_finished") {
            setIsScanning(false);
            eventSource.close();
            loadData();
          }
        } catch (e) {
          console.error("SSE parse error:", e);
        }
      };

      eventSource.onerror = async () => {
        eventSource.close();
        // Fallback to standard POST scan if SSE is interrupted
        try {
          const res = await api.triggerScan(undefined, minScore);
          setScanBoards(res.boards);
          setScanFoundCount(res.total_found);
        } catch {
          // ignore
        } finally {
          setIsScanning(false);
          loadData();
        }
      };
    } catch {
      setIsScanning(false);
    }
  };

  const handleStatusChange = async (jobId: string, status: KanbanStatus) => {
    try {
      await api.updateJob(jobId, { status });
      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, status } : j))
      );
      if (selectedJob && selectedJob.id === jobId) {
        setSelectedJob((prev) => (prev ? { ...prev, status } : null));
      }
      const updatedStats = await api.getJobStats();
      setStats(updatedStats);
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Dismiss this job lead?")) return;
    try {
      await api.deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      if (selectedJob && selectedJob.id === jobId) {
        setSelectedJob(null);
      }
      const updatedStats = await api.getJobStats();
      setStats(updatedStats);
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleJobUpdate = (updatedJob: JobLead) => {
    setJobs((prev) =>
      prev.map((j) => (j.id === updatedJob.id ? updatedJob : j))
    );
    setSelectedJob(updatedJob);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#090d16]">
      <Navbar
        onScanClick={handleStartScan}
        isScanning={isScanning}
        totalActiveLeads={stats?.total_active || 0}
      />

      <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full">
        {/* Live Scanner Banner */}
        <LiveScanner
          isScanning={isScanning}
          totalFound={scanFoundCount}
          boards={scanBoards}
          onDismiss={() => setScanBoards([])}
        />

        {/* Top Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Discovered</span>
              <Layers className="h-4 w-4 text-slate-500" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {stats?.counts.discovered || 0}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">Scraped & scored</p>
          </div>

          <div className="rounded-xl border border-cyan-800/40 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-cyan-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Shortlisted</span>
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-cyan-300 tracking-tight">
              {stats?.counts.shortlisted || 0}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">High fit prospects</p>
          </div>

          <div className="rounded-xl border border-indigo-800/40 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-indigo-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Pitched</span>
              <Briefcase className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-indigo-300 tracking-tight">
              {stats?.counts.pitch_generated || 0}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">Assets ready</p>
          </div>

          <div className="rounded-xl border border-amber-800/40 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-amber-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Applied</span>
              <Send className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-amber-300 tracking-tight">
              {stats?.counts.applied || 0}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">Outreach dispatched</p>
          </div>

          <div className="col-span-2 sm:col-span-4 lg:col-span-1 rounded-xl border border-emerald-800/40 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-emerald-400 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider">Interviewing</span>
              <UserCheck className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-emerald-300 tracking-tight">
              {stats?.counts.interviewing || 0}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">Active discussions</p>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between rounded-xl border border-slate-800 bg-slate-900/80 p-3 mb-6">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search by role, company, or tech keywords (e.g. 'RAG', 'FastAPI', 'Founding')..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 py-2 pl-9 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          {/* Quick Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Lead Type */}
            <select
              value={leadTypeFilter}
              onChange={(e) => setLeadTypeFilter(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-300 focus:border-cyan-500 focus:outline-none"
            >
              <option value="all">All Lead Types</option>
              <option value="job">Full-Time Jobs</option>
              <option value="client">Freelance / Contract</option>
            </select>

            {/* Propensity Tier */}
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-300 focus:border-cyan-500 focus:outline-none"
            >
              <option value="all">All Tiers</option>
              <option value="A+ High Value">Tier A+ (High Value)</option>
              <option value="B Qualified">Tier B (Qualified)</option>
              <option value="C Low Priority">Tier C (Low Priority)</option>
            </select>

            {/* Min Quality Score Slider */}
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-slate-400">
              <span>Min Fit:</span>
              <input
                type="range"
                min="50"
                max="90"
                step="5"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-20 accent-cyan-500 cursor-pointer"
              />
              <span className="font-bold text-cyan-400 w-7">{minScore}%</span>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        {isLoading ? (
          <div className="flex h-64 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Zap className="h-4 w-4 animate-spin text-cyan-400" />
              <span>Loading Lead Pipeline...</span>
            </div>
          </div>
        ) : (
          <KanbanBoard
            jobs={jobs}
            onSelectJob={(job) => setSelectedJob(job)}
            onStatusChange={handleStatusChange}
            onDeleteJob={handleDeleteJob}
          />
        )}

        {/* Slide-out Lead Drawer */}
        <LeadDrawer
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
          onUpdate={handleJobUpdate}
        />
      </main>
    </div>
  );
}
