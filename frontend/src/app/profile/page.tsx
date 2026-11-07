"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { ResumeDropzone } from "@/components/ResumeDropzone";
import { api } from "@/lib/api";
import { UserProfile, ResumeParseResult } from "@/lib/types";
import { 
  User, 
  Tag, 
  ShieldAlert, 
  Globe, 
  DollarSign, 
  Save, 
  Check, 
  Plus, 
  X,
  FileCheck
} from "lucide-react";

export default function ProfileStudioPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [targetRoles, setTargetRoles] = useState<string[]>([]);
  const [skills, setSkills] = useState<string[]>([]);
  const [negativeKeywords, setNegativeKeywords] = useState<string[]>([]);
  const [preferredLocations, setPreferredLocations] = useState<string[]>([]);
  const [minSalary, setMinSalary] = useState<number>(0);

  // Inputs for adding new tags
  const [newRoleInput, setNewRoleInput] = useState("");
  const [newSkillInput, setNewSkillInput] = useState("");
  const [newNegInput, setNewNegInput] = useState("");
  const [newLocInput, setNewLocInput] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await api.getProfile();
        setProfile(data);
        setFullName(data.full_name || "");
        setHeadline(data.headline || "");
        setBio(data.bio || "");
        setTargetRoles(data.target_roles || []);
        setSkills(data.skills || []);
        setNegativeKeywords(data.negative_keywords || []);
        setPreferredLocations(data.preferred_locations || []);
        setMinSalary(data.min_salary || 0);
      } catch (err: any) {
        console.error("Failed to load profile:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleResumeParsed = (result: ResumeParseResult) => {
    if (result.full_name && result.full_name !== "Candidate") {
      setFullName(result.full_name);
    }
    if (result.headline) {
      setHeadline(result.headline);
    }
    if (result.bio) {
      setBio(result.bio);
    }
    if (result.suggested_target_roles?.length) {
      const merged = Array.from(new Set([...targetRoles, ...result.suggested_target_roles]));
      setTargetRoles(merged);
    }
    if (result.suggested_skills?.length) {
      const merged = Array.from(new Set([...skills, ...result.suggested_skills]));
      setSkills(merged);
    }
    if (result.suggested_negative_keywords?.length) {
      const merged = Array.from(new Set([...negativeKeywords, ...result.suggested_negative_keywords]));
      setNegativeKeywords(merged);
    }
    setSaveSuccess(false);
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const updated = await api.updateProfile({
        full_name: fullName,
        headline,
        bio,
        target_roles: targetRoles,
        skills,
        negative_keywords: negativeKeywords,
        preferred_locations: preferredLocations,
        min_salary: minSalary,
      });
      setProfile(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Tag helper
  const addTag = (
    item: string,
    list: string[],
    setList: (val: string[]) => void,
    setInput: (val: string) => void
  ) => {
    const trimmed = item.trim();
    if (trimmed && !list.includes(trimmed)) {
      setList([...list, trimmed]);
      setInput("");
    }
  };

  const removeTag = (index: number, list: string[], setList: (val: string[]) => void) => {
    setList(list.filter((_, i) => i !== index));
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#090d16]">
      <Navbar />

      <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Profile Studio & Matcher Training
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure your candidate profile. The Scikit-Learn TF-IDF vectorizer indexes these parameters dynamically to score incoming job opportunities and generate hyper-tailored outreach pitches.
          </p>
        </div>

        {/* Resume Dropzone */}
        <div className="mb-8">
          <ResumeDropzone onParsed={handleResumeParsed} />
        </div>

        {/* Profile Form */}
        <div className="space-y-6 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
          {/* Basic Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Alex Mercer"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Headline / Title
              </label>
              <input
                type="text"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior Full-Stack & AI Solutions Architect"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Executive Bio */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Candidate Bio & Systems Background
            </label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Provide a 2-3 sentence summary of your technical architecture strengths, past production scale, and forward-deployed capabilities..."
              className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none resize-none leading-relaxed"
            />
          </div>

          {/* Target Roles */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Target Roles (Priority alignment keywords)
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {targetRoles.map((role, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1 rounded-md bg-cyan-950/70 text-cyan-300 px-2 py-1 text-xs font-medium border border-cyan-800/60"
                >
                  {role}
                  <button
                    onClick={() => removeTag(idx, targetRoles, setTargetRoles)}
                    className="hover:text-white"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Add target role (e.g. 'Founding Engineer')..."
                value={newRoleInput}
                onChange={(e) => setNewRoleInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(newRoleInput, targetRoles, setTargetRoles, setNewRoleInput);
                  }
                }}
                className="flex-1 rounded-lg border border-slate-800 bg-slate-950 p-2 text-xs text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => addTag(newRoleInput, targetRoles, setTargetRoles, setNewRoleInput)}
                className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Core Technical Skills */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Core Technical Skills (Indexed by TF-IDF Cosine Similarity)
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1 rounded-md bg-indigo-950/70 text-indigo-300 px-2 py-1 text-xs font-medium border border-indigo-800/60"
                >
                  {skill}
                  <button
                    onClick={() => removeTag(idx, skills, setSkills)}
                    className="hover:text-white"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Add skill (e.g. 'RAG', 'FastAPI', 'Next.js 16', 'PyTorch')..."
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(newSkillInput, skills, setSkills, setNewSkillInput);
                  }
                }}
                className="flex-1 rounded-lg border border-slate-800 bg-slate-950 p-2 text-xs text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => addTag(newSkillInput, skills, setSkills, setNewSkillInput)}
                className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Excluded Technologies / Negative Keywords */}
          <div>
            <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-rose-300 mb-1.5">
              <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
              Negative Tech Blacklist (Instant 0-score exclusion filter)
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {negativeKeywords.map((neg, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1 rounded-md bg-rose-950/60 text-rose-300 px-2 py-1 text-xs font-medium border border-rose-800/60"
                >
                  {neg}
                  <button
                    onClick={() => removeTag(idx, negativeKeywords, setNegativeKeywords)}
                    className="hover:text-white"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Add unwanted keyword (e.g. 'wordpress', 'php', 'swift', 'salesforce')..."
                value={newNegInput}
                onChange={(e) => setNewNegInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(newNegInput, negativeKeywords, setNegativeKeywords, setNewNegInput);
                  }
                }}
                className="flex-1 rounded-lg border border-slate-800 bg-slate-950 p-2 text-xs text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => addTag(newNegInput, negativeKeywords, setNegativeKeywords, setNewNegInput)}
                className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Location Preferences & Compensation Floor */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Preferred Locations (Remote Eligibility)
              </label>
              <div className="flex flex-wrap gap-1 mb-2">
                {preferredLocations.map((loc, idx) => (
                  <span
                    key={idx}
                    className="flex items-center gap-1 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300"
                  >
                    {loc}
                    <button onClick={() => removeTag(idx, preferredLocations, setPreferredLocations)}>
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="e.g. Remote, Worldwide, India..."
                  value={newLocInput}
                  onChange={(e) => setNewLocInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag(newLocInput, preferredLocations, setPreferredLocations, setNewLocInput);
                    }
                  }}
                  className="flex-1 rounded-lg border border-slate-800 bg-slate-950 p-2 text-xs text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => addTag(newLocInput, preferredLocations, setPreferredLocations, setNewLocInput)}
                  className="rounded-lg bg-slate-800 px-3 py-2 text-xs text-slate-200"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Minimum Annual Compensation Floor ($ USD)
              </label>
              <input
                type="number"
                value={minSalary}
                onChange={(e) => setMinSalary(Number(e.target.value))}
                placeholder="0 = No minimum"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Postings below this compensation floor will be demoted in ranking.
              </p>
            </div>
          </div>

          {/* Save Action */}
          <div className="pt-4 flex items-center justify-between border-t border-slate-800">
            {saveSuccess ? (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <Check className="h-4 w-4" />
                Profile Saved & Semantic Vectors Re-Indexed!
              </span>
            ) : (
              <span className="text-[11px] text-slate-500">
                Updates are persisted locally in SQLite.
              </span>
            )}

            <button
              onClick={handleSaveProfile}
              disabled={isSaving}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 transition-all disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? "Saving & Re-Indexing..." : "Save Profile & Re-Index"}</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
