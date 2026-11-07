"use client";

import { ScanBoardProgress } from "@/lib/types";
import { RefreshCw, CheckCircle2, AlertCircle, Clock, Zap } from "lucide-react";

interface LiveScannerProps {
  isScanning: boolean;
  totalFound: number;
  boards: ScanBoardProgress[];
  onDismiss?: () => void;
}

export function LiveScanner({ isScanning, totalFound, boards, onDismiss }: LiveScannerProps) {
  if (!isScanning && boards.length === 0) return null;

  const completedCount = boards.filter((b) => b.status === "completed" || b.status === "failed").length;
  const progressPercent = boards.length > 0 ? Math.round((completedCount / boards.length) * 100) : 0;

  return (
    <div className="w-full rounded-xl border border-cyan-800/40 bg-slate-900/90 p-4 shadow-lg backdrop-blur-md mb-6">
      <div className="flex items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
            {isScanning ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 fill-current text-cyan-400" />
            )}
          </div>
          <div>
            <h4 className="text-xs font-bold text-white tracking-wide">
              {isScanning ? "Autonomous Job Scanner Running..." : "Scan Complete"}
            </h4>
            <p className="text-[11px] text-slate-400">
              {completedCount} of {boards.length} scrapers finished • {totalFound} new leads ingested
            </p>
          </div>
        </div>

        {onDismiss && !isScanning && (
          <button
            onClick={onDismiss}
            className="rounded px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            Dismiss
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-300"
          style={{ width: `${isScanning ? Math.max(progressPercent, 10) : 100}%` }}
        />
      </div>

      {/* Board Status Badges */}
      <div className="flex flex-wrap gap-2">
        {boards.map((b) => {
          let badgeStyle = "bg-slate-950 text-slate-400 border-slate-800";
          let icon = <Clock className="h-3 w-3 text-slate-500" />;

          if (b.status === "scanning") {
            badgeStyle = "bg-cyan-950/80 text-cyan-300 border-cyan-800/80 animate-pulse";
            icon = <RefreshCw className="h-3 w-3 animate-spin text-cyan-400" />;
          } else if (b.status === "completed") {
            badgeStyle = "bg-emerald-950/60 text-emerald-300 border-emerald-800/60";
            icon = <CheckCircle2 className="h-3 w-3 text-emerald-400" />;
          } else if (b.status === "failed") {
            badgeStyle = "bg-rose-950/60 text-rose-300 border-rose-800/60";
            icon = <AlertCircle className="h-3 w-3 text-rose-400" />;
          }

          return (
            <div
              key={b.board_id}
              className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium border ${badgeStyle}`}
            >
              {icon}
              <span>{b.name}</span>
              {b.status === "completed" && b.found_count > 0 && (
                <span className="rounded-full bg-emerald-500/30 px-1.5 text-[10px] font-bold text-emerald-200">
                  +{b.found_count}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
