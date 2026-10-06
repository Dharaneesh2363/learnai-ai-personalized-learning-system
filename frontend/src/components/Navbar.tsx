import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Flame, LogOut, Sparkles, UserCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, loginAsDemo } = useAuth();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Title / Active Context */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700/60 font-mono">
          Model: Dual-Window Bayesian Trace
        </span>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        {/* Streak Flame */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold">
          <Flame className="w-4 h-4 fill-amber-400" />
          <span>7 Day Streak</span>
        </div>

        {/* Demo Switcher Dropdown / Buttons */}
        <div className="flex items-center bg-slate-800/80 border border-slate-700 rounded-lg p-0.5 text-xs font-medium">
          <button
            onClick={() => loginAsDemo('student')}
            className={`px-2.5 py-1 rounded-md transition ${
              user?.role === 'student' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Student
          </button>
          <button
            onClick={() => loginAsDemo('teacher')}
            className={`px-2.5 py-1 rounded-md transition ${
              user?.role === 'teacher' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Teacher
          </button>
          <button
            onClick={() => loginAsDemo('admin')}
            className={`px-2.5 py-1 rounded-md transition ${
              user?.role === 'admin' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Admin
          </button>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
