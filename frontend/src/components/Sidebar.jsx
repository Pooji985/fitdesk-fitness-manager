import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  CalendarDays,
  BookmarkCheck,
  Users,
  CloudSun,
  Shield,
  UserCheck,
  User,
  Database,
  ContactRound,
} from 'lucide-react';

export default function Sidebar({ activeTab, onSelectTab, isOpen, onClose }) {
  const { currentRole, user, isAdmin, isTrainer, isMember, ROLES } = useAuth();

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      roles: [ROLES.ADMIN, ROLES.TRAINER, ROLES.MEMBER],
      badge: null,
    },
    {
      id: 'schedule',
      label: 'Classes & Schedule',
      icon: CalendarDays,
      roles: [ROLES.ADMIN, ROLES.TRAINER, ROLES.MEMBER],
      badge: 'Weather-Aware',
    },
    {
      id: 'bookings',
      label: isMember ? 'My Bookings' : 'Bookings & Attendance',
      icon: BookmarkCheck,
      roles: [ROLES.ADMIN, ROLES.TRAINER, ROLES.MEMBER],
      badge: null,
    },
    {
      id: 'profile',
      label: 'My Profile',
      icon: ContactRound,
      roles: [ROLES.MEMBER],
      badge: null,
    },
    {
      id: 'members',
      label: 'Member Directory',
      icon: Users,
      roles: [ROLES.ADMIN],
      badge: 'Admin',
    },
  ];

  const filteredItems = navItems.filter((item) => item.roles.includes(currentRole));

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-16 bottom-0 left-0 z-30 w-64 bg-slate-950/95 border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 space-y-6 flex-1 overflow-y-auto">
          {/* Active Role Persona Card */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Active Perspective
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${user.badgeColor}`}>
                {user.role.toUpperCase()}
              </span>
            </div>
            <p className="text-xs font-semibold text-slate-200 mt-1.5">{user.name}</p>
            <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-snug">{user.description}</p>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <div className="px-3 pb-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Navigation
            </div>
            {filteredItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectTab(item.id);
                    onClose();
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Info */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] space-y-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                SQLite Engine
              </span>
              <span className="text-emerald-400 font-medium">Active</span>
            </div>
            <p className="text-[10px] text-slate-500">FastAPI backend ready</p>
          </div>
        </div>
      </aside>
    </>
  );
}
