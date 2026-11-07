"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Briefcase, 
  UserCheck, 
  Settings, 
  Compass, 
  Zap, 
  RefreshCw 
} from "lucide-react";

interface NavbarProps {
  onScanClick?: () => void;
  isScanning?: boolean;
  totalActiveLeads?: number;
}

export function Navbar({ onScanClick, isScanning, totalActiveLeads = 0 }: NavbarProps) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-white text-base">
                  JOB HUNTER
                </span>
                <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-400 border border-cyan-800/50">
                  STUDIO
                </span>
              </div>
              <p className="text-[11px] text-slate-400 -mt-0.5">Autonomous Outreach & Matching</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 ml-4">
            <Link
              href="/"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                pathname === "/"
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Briefcase className="h-3.5 w-3.5" />
              Command Center
              {totalActiveLeads > 0 && (
                <span className="ml-1 rounded-full bg-cyan-500/20 px-1.5 py-0.2 text-[10px] font-bold text-cyan-300">
                  {totalActiveLeads}
                </span>
              )}
            </Link>

            <Link
              href="/profile"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                pathname === "/profile"
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <UserCheck className="h-3.5 w-3.5" />
              Profile Studio
            </Link>

            <Link
              href="/settings"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                pathname === "/settings"
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Settings className="h-3.5 w-3.5" />
              BYOK & Settings
            </Link>
          </nav>
        </div>

        {/* Right Action: Quick Scan Trigger */}
        <div className="flex items-center gap-3">
          {onScanClick && (
            <button
              onClick={onScanClick}
              disabled={isScanning}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold shadow-md transition-all ${
                isScanning
                  ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                  : "bg-gradient-to-r from-cyan-500 to-indigo-600 text-white hover:from-cyan-400 hover:to-indigo-500 shadow-cyan-500/20 active:scale-95"
              }`}
            >
              {isScanning ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                  <span>Scanning Boards...</span>
                </>
              ) : (
                <>
                  <Zap className="h-3.5 w-3.5 fill-current" />
                  <span>Run Live Scan</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
