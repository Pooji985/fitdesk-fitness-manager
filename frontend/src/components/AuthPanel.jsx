import React, { useState } from 'react';
import { LogIn, LogOut, UserPlus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AuthPanel() {
  const { user, isAuthenticated, authLoading, login, register, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (mode === 'register') {
        await register({ name, email, password });
      } else {
        await login({ email, password });
      }
      setOpen(false);
      setName('');
      setEmail('');
      setPassword('');
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Authentication failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <span className="hidden md:inline text-xs text-slate-300">{user.name}</span>
        <button
          type="button"
          onClick={logout}
          title="Sign out"
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-900 text-xs"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        disabled={authLoading}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 text-xs disabled:opacity-50"
      >
        <LogIn className="w-3.5 h-3.5" />
        <span>{authLoading ? 'Checking' : 'Sign in'}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 z-50 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-slate-700 bg-slate-950 p-4 shadow-2xl">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-white">
              {mode === 'login' ? 'Sign in to FitDesk' : 'Create a member account'}
            </h2>
            <button
              type="button"
              onClick={() => { setOpen(false); setError(''); }}
              aria-label="Close authentication panel"
              className="p-1 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-1 p-1 mb-3 rounded-lg bg-slate-900">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(''); }}
              className={`rounded-md py-1.5 text-xs ${mode === 'login' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => { setMode('register'); setError(''); }}
              className={`rounded-md py-1.5 text-xs ${mode === 'register' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === 'register' && (
              <label className="block space-y-1">
                <span className="text-[11px] text-slate-400">Name</span>
                <input
                  required
                  minLength="2"
                  maxLength="100"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white outline-none focus:border-emerald-500"
                />
              </label>
            )}
            <label className="block space-y-1">
              <span className="text-[11px] text-slate-400">Email</span>
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white outline-none focus:border-emerald-500"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-[11px] text-slate-400">Password</span>
              <input
                required
                type="password"
                minLength={mode === 'register' ? 8 : 1}
                maxLength="128"
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white outline-none focus:border-emerald-500"
              />
            </label>
            {error && <p role="alert" className="text-xs text-rose-300">{error}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {mode === 'register' ? <UserPlus className="w-3.5 h-3.5" /> : <LogIn className="w-3.5 h-3.5" />}
              <span>{submitting ? 'Working...' : mode === 'register' ? 'Create account' : 'Sign in'}</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}