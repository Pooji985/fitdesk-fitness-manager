import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import BackendStatusCard from '../components/BackendStatusCard';
import { dashboardService } from '../services/dashboardService';
import {
  Calendar,
  CloudSun,
  Users,
  CheckCircle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Award,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Activity,
  History,
} from 'lucide-react';

const ICON_MAP = {
  Users,
  Calendar,
  CheckCircle,
  CloudSun,
  Award,
  TrendingUp,
};

export default function Dashboard({ onNavigate }) {
  const { user, isAdmin, isTrainer, isMember, isAuthenticated, authLoading } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dashboardService.getMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch live dashboard metrics from FastAPI.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated) fetchMetrics();
    else {
      setMetrics(null);
      setLoading(false);
      setError(null);
    }
  }, [authLoading, isAuthenticated, user.id]);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl glass-panel p-6 sm:p-8 border border-slate-800">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Role: {user.roleTitle}</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
              Welcome back, {user.name}
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              {isAdmin && 'Manage your gym facility, review schedules, monitor capacity, and view live attendance reports.'}
              {isTrainer && 'Review your assigned classes, inspect outdoor weather conditions, and record member attendance.'}
              {isMember && 'Explore upcoming fitness classes, verify outdoor weather forecasts, and manage your workout bookings.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('schedule')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-xs bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
            >
              <span>View Class Timetable</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Role Stats Section Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
            Live System Metrics ({user.roleTitle})
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
            title="Refresh database statistics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hidden sm:inline-block">
            SQLite Verified
          </span>
        </div>
      </div>

      {/* Role Stats Grid (Loading, Error, Empty, or Live Data) */}
      {!isAuthenticated ? (
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 text-center text-xs text-slate-400">
          Sign in to view dashboard metrics for your account.
        </div>
      ) : loading && !metrics ? (
        /* Loading Skeleton */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="p-5 rounded-2xl glass-card border border-slate-800/80 animate-pulse space-y-3"
            >
              <div className="flex justify-between items-center">
                <div className="h-3 w-24 bg-slate-800 rounded"></div>
                <div className="h-9 w-9 bg-slate-800 rounded-xl"></div>
              </div>
              <div className="h-7 w-16 bg-slate-800 rounded"></div>
              <div className="h-3 w-32 bg-slate-800 rounded"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200 text-sm">Failed to Load Live Metrics</p>
              <p className="text-xs text-rose-300/80 mt-1">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchMetrics}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-rose-500/30 text-rose-300 text-xs font-semibold hover:bg-slate-800 transition-colors shrink-0"
          >
            Retry
          </button>
        </div>
      ) : metrics && metrics.stats && metrics.stats.length > 0 ? (
        /* Live Metric Cards */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.stats.map((stat, idx) => {
            const Icon = ICON_MAP[stat.icon] || Award;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl glass-card border border-slate-800/80 hover:border-slate-700/80 transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400">{stat.label}</span>
                  <div className={`p-2.5 rounded-xl ${stat.bg} ${stat.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-2xl font-bold text-white mt-2">{stat.value}</p>
                <p className="text-xs text-slate-400 mt-1">{stat.change}</p>
              </div>
            );
          })}
        </div>
      ) : (
        /* Empty State */
        <div className="p-8 text-center rounded-2xl glass-card border border-slate-800 space-y-2">
          <p className="text-sm font-semibold text-slate-300">No Metrics Available</p>
          <p className="text-xs text-slate-500">No active data points found for this user account.</p>
        </div>
      )}

      {/* Recent Activity Feed & Live Backend Connection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Feed (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
                Recent Activity & Registrations
              </h2>
            </div>
            <span className="text-xs text-slate-500">Live Database Feed</span>
          </div>

          <div className="rounded-2xl glass-panel border border-slate-800 overflow-hidden">
            {!isAuthenticated ? (
              <div className="p-6 text-center text-xs text-slate-400">Sign in to view recent account activity.</div>
            ) : loading && !metrics ? (
              <div className="p-6 text-center text-xs text-slate-400 animate-pulse">
                Loading recent activity logs...
              </div>
            ) : metrics && metrics.recent_activities && metrics.recent_activities.length > 0 ? (
              <div className="divide-y divide-slate-800/60 text-xs">
                {metrics.recent_activities.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/40 transition-colors"
                  >
                    <div className="space-y-0.5">
                      <p className="font-semibold text-slate-200">{item.title}</p>
                      <p className="text-slate-400 text-[11px]">{item.subtitle}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-slate-500 font-mono hidden sm:inline-block">
                        {item.time}
                      </span>
                      <span
                        className={`self-start sm:self-auto px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${item.badge_color}`}
                      >
                        {item.badge}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No recent activity records found.
              </div>
            )}
          </div>
        </div>

        {/* Live Backend Connection Card (1 Col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
              System Diagnostics
            </h2>
            <span className="text-xs text-slate-500">FastAPI + SQLite</span>
          </div>
          <BackendStatusCard />
        </div>
      </div>

      {/* Implementation Roadmap Progress */}
      <section className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
              Project Architecture Roadmap
            </h2>
          </div>
          <span className="text-xs text-emerald-400 font-medium">Stages 1–4 Completed</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { id: 1, name: 'Tooling & Backend Bridge', status: 'completed', desc: 'React, Vite, Tailwind CSS & FastAPI connection' },
            { id: 2, name: 'App Shell & Role Context', status: 'completed', desc: 'Navigation, Admin/Trainer/Member role switcher' },
            { id: 3, name: 'Dashboard & System Metrics', status: 'completed', desc: 'Real-time SQLite KPIs, role metrics & activity feed' },
            { id: 4, name: 'Classes & Open-Meteo Weather', status: 'completed', desc: 'Live class timetable, outdoor weather alerts & class creation' },
            { id: 5, name: 'Bookings & Attendance', status: 'next', desc: 'Self-service reservations & digital check-in' },
            { id: 6, name: 'Member Directory & Polish', status: 'upcoming', desc: 'Tier management & responsive finalization' },
          ].map((stage) => {
            const isDone = stage.status === 'completed';
            const isNext = stage.status === 'next';
            return (
              <div
                key={stage.id}
                className={`p-3.5 rounded-xl border transition-all duration-200 ${
                  isDone
                    ? 'glass-card border-emerald-500/40 bg-emerald-950/20'
                    : isNext
                    ? 'glass-card border-cyan-500/40 bg-cyan-950/20 shadow-sm shadow-cyan-500/10'
                    : 'glass-card border-slate-800/80 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between">
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                      isDone
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : isNext
                        ? 'bg-cyan-500/20 text-cyan-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Stage 0{stage.id}
                  </span>
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isNext ? (
                    <span className="text-[10px] text-cyan-300 font-semibold uppercase tracking-wider">Next Up</span>
                  ) : (
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Pending</span>
                  )}
                </div>
                <h3 className="text-xs font-semibold text-slate-200 mt-2">{stage.name}</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">{stage.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
