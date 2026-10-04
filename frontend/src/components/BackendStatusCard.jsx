import React, { useState, useEffect } from 'react';
import { healthService } from '../services/healthService';
import { Activity, Database, Server, RefreshCw, CheckCircle2, AlertTriangle, ShieldCheck, ExternalLink } from 'lucide-react';

export default function BackendStatusCard() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();
    try {
      const data = await healthService.getHealth();
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      setHealth(data);
    } catch (err) {
      setError(err.message || 'Unable to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const isConnected = health && health.status === 'ok';

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 max-w-2xl mx-auto shadow-2xl relative overflow-hidden transition-all duration-300">
      {/* Background ambient glow */}
      <div className={`absolute -right-16 -top-16 w-56 h-56 rounded-full blur-3xl opacity-20 pointer-events-none ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-700/60">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl ${isConnected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
            <Server className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">FastAPI Backend Bridge</h2>
            <p className="text-xs text-slate-400">Verifying live communication with Python & SQLite</p>
          </div>
        </div>

        <button
          onClick={fetchStatus}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          {loading ? 'Checking...' : 'Re-test Connection'}
        </button>
      </div>

      {/* Body / Connection States */}
      <div className="pt-6">
        {loading && !health ? (
          <div className="py-8 flex flex-col items-center justify-center gap-3">
            <div className="w-10 h-10 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
            <p className="text-sm text-slate-400">Pinging backend endpoint at <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-emerald-400">/api/v1/health</code>...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold text-rose-200">Connection Failed</p>
              <p className="text-xs text-rose-300/80 mt-1">{error}</p>
              <p className="text-xs text-slate-400 mt-2">Ensure FastAPI is running: <code className="text-slate-300">uvicorn app.main:app --port 8000</code></p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Status grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* API Status */}
              <div className="glass-card p-4 rounded-xl border border-slate-700/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <div>
                    <p className="text-xs text-slate-400 font-medium">FastAPI Service</p>
                    <p className="text-sm font-semibold text-slate-200 capitalize">{health?.status || 'Unknown'}</p>
                  </div>
                </div>
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
              </div>

              {/* Database Status */}
              <div className="glass-card p-4 rounded-xl border border-slate-700/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <div>
                    <p className="text-xs text-slate-400 font-medium">SQLite Database</p>
                    <p className="text-sm font-semibold text-slate-200 capitalize">{health?.database || 'Unknown'}</p>
                  </div>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
            </div>

            {/* Details list */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between items-center text-slate-400">
                <span>Backend Project:</span>
                <span className="font-semibold text-slate-200">{health?.project}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>API Version:</span>
                <span className="font-mono text-slate-300">{health?.version}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Roundtrip Latency:</span>
                <span className="font-mono text-emerald-400">{latency} ms</span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Vite Proxy Target:</span>
                <span className="font-mono text-cyan-400">http://127.0.0.1:8000</span>
              </div>
            </div>

            {/* Interactive Docs Link */}
            <div className="pt-2 flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Stage 1 Live Backend Link Verified</span>
              </div>
              <a
                href="http://127.0.0.1:8000/api/v1/docs"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-slate-400 hover:text-emerald-400 transition-colors"
              >
                <span>Swagger Docs</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
