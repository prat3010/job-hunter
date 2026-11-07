"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { AIConfig, BoardInfo } from "@/lib/types";
import { 
  Settings, 
  Key, 
  Cpu, 
  Clock, 
  Check, 
  Zap, 
  Eye, 
  EyeOff, 
  Save, 
  RefreshCw,
  Layers,
  Radio
} from "lucide-react";

export default function SettingsPage() {
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [boards, setBoards] = useState<BoardInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [provider, setProvider] = useState<"gemini" | "openai" | "anthropic" | "groq" | "ollama">("gemini");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [modelName, setModelName] = useState("gemini-2.5-flash");
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [scanInterval, setScanInterval] = useState<number>(0);
  const [enabledBoards, setEnabledBoards] = useState<string[]>([]);

  // AI Connection Test
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    latency_ms: number;
    response?: string;
    error?: string;
  } | null>(null);

  useEffect(() => {
    async function loadSettings() {
      try {
        const [cfgData, boardsData] = await Promise.all([
          api.getSettings(),
          api.getBoards(),
        ]);
        setConfig(cfgData);
        setProvider(cfgData.provider);
        setModelName(cfgData.model_name || "gemini-2.5-flash");
        setOllamaUrl(cfgData.ollama_url || "http://localhost:11434");
        setScanInterval(cfgData.auto_scan_interval_hours || 0);
        setEnabledBoards(cfgData.enabled_boards || []);
        setBoards(boardsData);
      } catch (err: any) {
        console.error("Failed to load settings:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleProviderChange = (newProvider: "gemini" | "openai" | "anthropic" | "groq" | "ollama") => {
    setProvider(newProvider);
    if (newProvider === "gemini") setModelName("gemini-2.5-flash");
    else if (newProvider === "openai") setModelName("gpt-4o-mini");
    else if (newProvider === "groq") setModelName("llama-3.3-70b-versatile");
    else if (newProvider === "anthropic") setModelName("claude-3-5-haiku-20241022");
    else if (newProvider === "ollama") setModelName("llama3.2");
  };

  const handleToggleBoard = (boardId: string) => {
    setEnabledBoards((prev) =>
      prev.includes(boardId) ? prev.filter((id) => id !== boardId) : [...prev, boardId]
    );
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const payload: any = {
        provider,
        model_name: modelName,
        ollama_url: ollamaUrl,
        auto_scan_interval_hours: scanInterval,
        enabled_boards: enabledBoards,
      };
      if (apiKey.trim()) {
        payload.api_key = apiKey.trim();
      }
      const updated = await api.updateSettings(payload);
      setConfig(updated);
      setApiKey("");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      // First save if key was typed
      if (apiKey.trim()) {
        await api.updateSettings({
          provider,
          model_name: modelName,
          ollama_url: ollamaUrl,
          api_key: apiKey.trim(),
        });
        setApiKey("");
      }
      const res = await api.testAiConnection();
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        latency_ms: 0,
        error: err.message,
      });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#090d16]">
      <Navbar />

      <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            BYOK & Autonomous Scraper Settings
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure your AI synthesis providers and automated board scrapers. All API keys and preferences are stored locally in your SQLite database.
          </p>
        </div>

        <div className="space-y-8">
          {/* Section 1: AI Provider (BYOK) */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-slate-800">
              <Key className="h-4 w-4 text-cyan-400" />
              <h2 className="font-bold text-sm text-white uppercase tracking-wider">
                AI Synthesis Provider (Bring Your Own Key)
              </h2>
            </div>

            {/* Provider Radios */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5">
              {[
                { id: "gemini", name: "Google Gemini", badge: "Recommended" },
                { id: "openai", name: "OpenAI", badge: "GPT-4o" },
                { id: "groq", name: "Groq", badge: "Ultra Fast" },
                { id: "anthropic", name: "Anthropic", badge: "Claude 3.5" },
                { id: "ollama", name: "Local Ollama", badge: "$0 Free" },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleProviderChange(p.id as any)}
                  className={`flex flex-col items-start rounded-lg p-3 text-left border transition-all ${
                    provider === p.id
                      ? "border-cyan-500 bg-cyan-950/40 text-white shadow-md shadow-cyan-950/50"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <span className="text-xs font-bold">{p.name}</span>
                  <span className="text-[10px] text-cyan-400 mt-0.5">{p.badge}</span>
                </button>
              ))}
            </div>

            {/* Provider Configuration Fields */}
            <div className="space-y-4">
              {provider !== "ollama" ? (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-slate-300">
                      API Key
                    </label>
                    {config?.has_api_key && (
                      <span className="text-[11px] text-emerald-400 font-mono">
                        Active Key: {config.masked_api_key}
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={
                        config?.has_api_key
                          ? "Leave blank to keep existing key, or paste new key..."
                          : "Paste API key (e.g. AIza... or sk-...)"
                      }
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 pr-10 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300"
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Ollama Local Base URL
                  </label>
                  <input
                    type="text"
                    value={ollamaUrl}
                    onChange={(e) => setOllamaUrl(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none font-mono"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Retriever and Job Hunter can query local Ollama with zero external API calls or token costs.
                  </p>
                </div>
              )}

              {/* Model Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Model Identifier
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. gemini-2.5-flash, gpt-4o-mini, llama-3.3-70b-versatile, llama3.2"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-100 placeholder-slate-600 focus:border-cyan-500 focus:outline-none font-mono"
                />
              </div>

              {/* Connection Test Action */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="flex items-center gap-1.5 rounded-lg bg-slate-800 px-3.5 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors disabled:opacity-50"
                >
                  {isTesting ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                      <span>Testing Inference...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="h-3.5 w-3.5 text-cyan-400" />
                      <span>Test AI Connection</span>
                    </>
                  )}
                </button>

                {testResult && (
                  <div
                    className={`flex items-center gap-2 text-xs font-medium ${
                      testResult.success ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {testResult.success ? (
                      <>
                        <Check className="h-4 w-4" />
                        <span>
                          Connected! Latency: {testResult.latency_ms}ms ({testResult.response})
                        </span>
                      </>
                    ) : (
                      <span>Error: {testResult.error}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Section 2: Enabled Job Boards */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-slate-800">
              <Layers className="h-4 w-4 text-cyan-400" />
              <h2 className="font-bold text-sm text-white uppercase tracking-wider">
                Active Scraper Sources ({enabledBoards.length} of {boards.length} Enabled)
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {boards.map((b) => {
                const isEnabled = enabledBoards.includes(b.id);
                return (
                  <div
                    key={b.id}
                    onClick={() => handleToggleBoard(b.id)}
                    className={`flex items-center justify-between rounded-lg p-3 border cursor-pointer transition-all ${
                      isEnabled
                        ? "border-cyan-800 bg-cyan-950/30 text-white"
                        : "border-slate-800 bg-slate-950/40 text-slate-500 hover:border-slate-700"
                    }`}
                  >
                    <span className="text-xs font-medium">{b.name}</span>
                    <div
                      className={`h-4 w-4 rounded flex items-center justify-center border ${
                        isEnabled
                          ? "bg-cyan-500 border-cyan-400 text-slate-950"
                          : "border-slate-700 bg-slate-900"
                      }`}
                    >
                      {isEnabled && <Check className="h-3 w-3 stroke-[3]" />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 3: Background Scheduler */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
            <div className="flex items-center gap-2 pb-4 mb-4 border-b border-slate-800">
              <Clock className="h-4 w-4 text-cyan-400" />
              <h2 className="font-bold text-sm text-white uppercase tracking-wider">
                Autonomous Background Scan Schedule
              </h2>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-2">
              {[
                { value: 0, label: "Manual Only", sub: "Off" },
                { value: 6, label: "Every 6 Hours", sub: "High Frequency" },
                { value: 12, label: "Every 12 Hours", sub: "Balanced" },
                { value: 24, label: "Daily (24h)", sub: "Recommended" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setScanInterval(opt.value)}
                  className={`flex flex-col items-start rounded-lg p-3 text-left border transition-all ${
                    scanInterval === opt.value
                      ? "border-cyan-500 bg-cyan-950/40 text-white"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <span className="text-xs font-bold">{opt.label}</span>
                  <span className="text-[10px] text-cyan-400 mt-0.5">{opt.sub}</span>
                </button>
              ))}
            </div>

            <p className="text-[11px] text-slate-500">
              Background scans run asynchronously using APScheduler and automatically ingest new matching leads into your local SQLite database without requiring the browser to be open.
            </p>
          </div>

          {/* Save All Settings */}
          <div className="flex items-center justify-between pt-2">
            {saveSuccess ? (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <Check className="h-4 w-4" />
                Settings & Scraper Preferences Saved!
              </span>
            ) : (
              <span className="text-[11px] text-slate-500">
                Configuration stored in local database.
              </span>
            )}

            <button
              onClick={handleSaveSettings}
              disabled={isSaving}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 transition-all disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? "Saving Settings..." : "Save Settings"}</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
