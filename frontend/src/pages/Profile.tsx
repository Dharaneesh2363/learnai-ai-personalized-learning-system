import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/Badge';
import { User, Mail, Shield, Calendar, Award } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, loginAsDemo } = useAuth();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <User className="w-6 h-6 text-indigo-400" /> Student Profile & Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your account settings, credentials, and learning identity.
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-2xl font-bold">
            {user?.full_name.charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{user?.full_name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="indigo">{user?.role.toUpperCase()}</Badge>
              <span className="text-xs text-slate-400 font-mono">Account ID: #{user?.id}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mb-1">
              <Mail className="w-3.5 h-3.5 text-slate-500" /> Email Address
            </span>
            <p className="text-sm font-semibold text-white">{user?.email}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mb-1">
              <Shield className="w-3.5 h-3.5 text-slate-500" /> System Authorization
            </span>
            <p className="text-sm font-semibold text-white uppercase">{user?.role} Access</p>
          </div>
        </div>

        {/* Demo Switcher for Evaluation */}
        <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 font-mono">
            Demo Persona Switcher
          </h3>
          <p className="text-xs text-slate-400">
            Quickly switch personas to experience both the student adaptive dashboard and the administrative educator portal.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => loginAsDemo('student')}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition"
            >
              Switch to Demo Student
            </button>
            <button
              onClick={() => loginAsDemo('admin')}
              className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition"
            >
              Switch to Demo Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
