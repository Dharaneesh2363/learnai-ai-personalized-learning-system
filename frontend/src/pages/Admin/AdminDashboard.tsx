import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsApi, adminApi } from '../../api';
import { StatCard } from '../../components/StatCard';
import { Badge } from '../../components/Badge';
import {
  Shield,
  Users,
  BookOpen,
  HelpCircle,
  TrendingUp,
  Sparkles,
  ArrowRight
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [adminData, setAdminData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminStats = async () => {
      try {
        const data = await analyticsApi.getAdmin();
        setAdminData(data);
      } catch (err) {
        console.error('Failed to load admin stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAdminStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-purple-400" /> Educator & Administrator Portal
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor cohort performance, curriculum engagement, and AI assessment generation.
        </p>
      </div>

      {/* Admin KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Students"
          value={adminData?.total_students || 0}
          subtext="Enrolled learners"
          icon={Users}
          iconColor="text-indigo-400"
        />
        <StatCard
          title="Platform Average Mastery"
          value={`${adminData?.average_platform_mastery || 0}%`}
          subtext="Cross-topic mean mastery"
          icon={TrendingUp}
          iconColor="text-emerald-400"
        />
        <StatCard
          title="Active Curriculums"
          value={adminData?.total_courses || 0}
          subtext="Published courses"
          icon={BookOpen}
          iconColor="text-amber-400"
        />
        <StatCard
          title="Quizzes Evaluated"
          value={adminData?.total_quizzes_completed || 0}
          subtext="Authoritative attempts"
          icon={HelpCircle}
          iconColor="text-purple-400"
        />
      </div>

      {/* Admin Quick Action Hub */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white tracking-tight">Curriculum & Questions Bank</h2>
          <p className="text-xs text-slate-400">
            Inspect live assessment questions, edit metadata, or generate curriculum-aligned questions using the AI Provider.
          </p>
          <Link
            to="/admin/questions"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition"
          >
            <span>Manage Question Bank & AI Generator</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white tracking-tight">Student Cohort Roster</h2>
          <p className="text-xs text-slate-400">
            View individual student mastery trajectories, attempt history, and identified concept bottlenecks.
          </p>
          <Link
            to="/admin/students"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white shadow-md shadow-purple-600/20 transition"
          >
            <span>Inspect Student Performance</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};
