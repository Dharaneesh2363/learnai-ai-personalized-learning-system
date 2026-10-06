import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  HelpCircle,
  Sparkles,
  Calendar,
  Bot,
  BarChart3,
  User as UserIcon,
  Shield,
  GraduationCap
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const isAdminOrTeacher = user?.role === 'admin' || user?.role === 'teacher';

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Courses', path: '/courses', icon: BookOpen },
    { name: 'Quizzes', path: '/quizzes', icon: HelpCircle },
    { name: 'Recommendations', path: '/recommendations', icon: Sparkles, badge: 'AI' },
    { name: 'Study Plan', path: '/study-plan', icon: Calendar },
    { name: 'AI Tutor', path: '/tutor', icon: Bot, badge: 'Live' },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Profile', path: '/profile', icon: UserIcon },
  ];

  if (isAdminOrTeacher) {
    navItems.push({ name: 'Admin Portal', path: '/admin', icon: Shield, badge: 'Manage' });
  }

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
            LearnAI <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">PRO</span>
          </span>
          <p className="text-[11px] text-slate-400">Personalized Engine</p>
        </div>
      </div>

      {/* Nav Links */}
      <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Learning Experience
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition group ${
                  isActive
                    ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 transition group-hover:scale-110" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* User Footer Profile */}
      {user && (
        <div className="p-4 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-sm text-indigo-400">
              {user.full_name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user.full_name}</p>
              <p className="text-[11px] text-slate-400 truncate uppercase font-mono tracking-wider">{user.role}</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
