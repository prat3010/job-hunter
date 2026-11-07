"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";
import { ResumeParseResult } from "@/lib/types";
import { UploadCloud, FileText, RefreshCw, CheckCircle2 } from "lucide-react";

interface ResumeDropzoneProps {
  onParsed: (result: ResumeParseResult) => void;
}

export function ResumeDropzone({ onParsed }: ResumeDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    setUploadedFileName(file.name);

    try {
      const result = await api.uploadResume(file);
      onParsed(result);
    } catch (err: any) {
      alert(`Resume parsing failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
        isDragging
          ? "border-cyan-400 bg-cyan-950/20"
          : "border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90"
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
          }
        }}
      />

      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 mb-3">
        {isUploading ? (
          <RefreshCw className="h-6 w-6 animate-spin" />
        ) : uploadedFileName ? (
          <CheckCircle2 className="h-6 w-6 text-emerald-400" />
        ) : (
          <UploadCloud className="h-6 w-6" />
        )}
      </div>

      <h4 className="font-semibold text-sm text-slate-200">
        {isUploading
          ? "Analyzing Resume with AI..."
          : uploadedFileName
          ? `Parsed: ${uploadedFileName}`
          : "Upload or drop resume (PDF / Text)"}
      </h4>

      <p className="mt-1 text-xs text-slate-400 max-w-sm">
        {isUploading
          ? "Extracting skills, target roles, experience highlights, and semantic vectors..."
          : "Instantly auto-populates your target roles, core technical skills, and candidate bio."}
      </p>

      <span className="mt-4 rounded-md bg-slate-800 px-3 py-1 text-[11px] font-medium text-slate-300 border border-slate-700/60">
        Select PDF Document
      </span>
    </div>
  );
}
