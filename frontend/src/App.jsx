import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Schedule from './pages/Schedule';
import Bookings from './pages/Bookings';
import Members from './pages/Members';
import MyProfile from './pages/MyProfile';

function AppShell() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Keep the member directory out of non-admin perspectives.
  useEffect(() => {
    if (!isAdmin && activeTab === 'members') {
      setActiveTab('dashboard');
    }
  }, [isAdmin, activeTab]);

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-white">
      {/* Top Sticky Navbar */}
      <Navbar
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex-1 flex">
        {/* Responsive Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main Content Area (offset by sidebar width on desktop) */}
        <main className="flex-1 lg:pl-64 flex flex-col justify-between min-h-[calc(100vh-4rem)]">
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-8">
            {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
            {activeTab === 'schedule' && <Schedule />}
            {activeTab === 'bookings' && <Bookings onNavigate={setActiveTab} />}
            {activeTab === 'profile' && <MyProfile />}
            {activeTab === 'members' && (
              isAdmin ? (
                <Members />
              ) : (
                <div className="p-8 text-center glass-card rounded-2xl border border-slate-800 space-y-3">
                  <p className="text-amber-400 font-semibold text-sm">Access Restricted</p>
                  <p className="text-xs text-slate-400">The Member Directory is restricted to Administrators.</p>
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
                  >
                    Return to Dashboard
                  </button>
                </div>
              )
            )}
          </div>

          {/* Footer */}
          <footer className="border-t border-slate-900 bg-slate-950/60 py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p>FitDesk Fitness Manager • FastAPI (SQLite) & React (Tailwind CSS)</p>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Stage 4 Complete • Classes & Weather Engine
              </span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
