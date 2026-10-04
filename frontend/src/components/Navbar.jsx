import React, { useState, useEffect } from 'react';
import { useAuth, ROLES } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import AuthPanel from './AuthPanel';
import { Dumbbell, Shield, UserCheck, User, Menu, X, Check, Activity, ChevronDown } from 'lucide-react';

export default function Navbar({ onToggleSidebar, sidebarOpen }) {
  const { currentRole, user, switchRole, USER_PROFILES, isAuthenticated } = useAuth();
  const [backendOnline, setBackendOnline] = useState(null);
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);

  // Poll backend health status periodically for the status indicator
  useEffect(() => {
    let isMounted = true;
    const checkConnection = async () => {
      try {
        const res = await healthService.getHealth();
        if (isMounted) setBackendOnline(res.status === 'ok');
      } catch (err) {
        if (isMounted) setBackendOnline(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 15000); // Check every 15s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const getRoleIcon = (role) => {
    switch (role) {
      case ROLES.ADMIN:
        return <Shield className="w-3.5 h-3.5 text-purple-400" />;
      case ROLES.TRAINER:
        return <UserCheck className="w-3.5 h-3.5 text-cyan-400" />;
      case ROLES.MEMBER:
      default:
        return <User className="w-3.5 h-3.5 text-emerald-400" />;
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Left: Mobile Toggle & Brand */}
        <div className="flex items-center gap-3 sm:gap-4">
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle Navigation Menu"
            className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 focus:outline-none"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 p-0.5 shadow-md shadow-emerald-500/10">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Dumbbell className="w-4 h-4 text-emerald-400" />
              </div>
            </div>
            <div>
              <span className="font-extrabold text-base sm:text-lg tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                FitDesk
              </span>
              <span className="hidden md:inline-block ml-2 text-[11px] font-medium text-slate-400 border-l border-slate-800 pl-2">
                Fitness Manager
              </span>
            </div>
          </div>
        </div>

        {/* Right: Live Backend Pill + Role Switcher */}
        <div className="flex items-center gap-3">
          {/* Backend Connection Status Pill */}
          <div
            className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs border ${
              backendOnline === true
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : backendOnline === false
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
            title={backendOnline ? 'Connected to FastAPI & SQLite' : 'Backend offline'}
          >
            <span className="relative flex h-2 w-2">
              {backendOnline && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  backendOnline === true
                    ? 'bg-emerald-400'
                    : backendOnline === false
                    ? 'bg-rose-400'
                    : 'bg-slate-400'
                }`}
              ></span>
            </span>
            <span className="font-medium text-[11px]">
              {backendOnline === true ? 'FastAPI Online' : backendOnline === false ? 'API Offline' : 'Connecting...'}
            </span>
          </div>

          {/* Interactive Role Switcher Dropdown */}
          {!isAuthenticated && <div className="relative">
            <button
              onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors focus:outline-none"
            >
              <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-200">
                {user.avatar}
              </div>
              <div className="text-left hidden sm:block">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-200 leading-none">{user.name}</span>
                  {getRoleIcon(currentRole)}
                </div>
                <span className="text-[10px] text-slate-400 capitalize">{user.roleTitle}</span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
            </button>

            {/* Dropdown Menu */}
            {roleDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setRoleDropdownOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-slate-900/95 border border-slate-800 p-2 shadow-2xl backdrop-blur-xl z-50">
                  <div className="px-3 py-2 border-b border-slate-800/80 mb-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Switch Role (Simulation)
                    </p>
                    <p className="text-xs text-slate-300">Test role-based views & permissions</p>
                  </div>

                  <div className="space-y-1">
                    {Object.values(ROLES).map((role) => {
                      const profile = USER_PROFILES[role];
                      const isSelected = currentRole === role;
                      return (
                        <button
                          key={role}
                          onClick={() => {
                            switchRole(role);
                            setRoleDropdownOpen(false);
                          }}
                          className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition-colors ${
                            isSelected
                              ? 'bg-slate-800/90 text-white'
                              : 'hover:bg-slate-800/50 text-slate-300'
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-slate-950 flex items-center justify-center text-xs font-bold">
                              {profile.avatar}
                            </div>
                            <div>
                              <p className="text-xs font-semibold flex items-center gap-1">
                                {profile.name}
                                {getRoleIcon(role)}
                              </p>
                              <p className="text-[10px] text-slate-400 capitalize">{role}</p>
                            </div>
                          </div>
                          {isSelected && <Check className="w-4 h-4 text-emerald-400" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>}
          <AuthPanel />
        </div>
      </div>
    </header>
  );
}
