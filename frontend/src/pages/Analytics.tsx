import React, { useEffect, useState } from 'react';
import { analyticsApi, masteryApi } from '../api';
import { DashboardAnalytics, MasterySummary } from '../api/types';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';
import {
  BarChart3,
  Flame,
  Award,
  Target,
  TrendingUp,
  Brain,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';

export const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [mastery, setMastery] = useState<MasterySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [aData, mData] = await Promise.all([
          analyticsApi.getDashboard(),
          masteryApi.getSummary(),
        ]);
        setAnalytics(aData);
        setMastery(mData);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const topicChartData = (analytics?.mastery_by_topic || []).map((t) => ({
    name: t.topic_title.length > 15 ? t.topic_title.slice(0, 15) + '...' : t.topic_title,
    score: t.mastery_score,
  }));

  const quizTrendData = (analytics?.quiz_trend || []).map((q) => ({
    name: q.date,
    score: q.percentage,
  }));

  const activityData = (analytics?.recent_activity || []).map((a) => ({
    day: a.date,
    events: a.event_count,
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-400" /> Learning Telemetry & Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Quantitative performance analytics, cognitive growth metrics, and concept tracking.
        </p>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Mastery"
          value={`${analytics?.overall_mastery || 0}%`}
          subtext="Weighted knowledge score"
          icon={Award}
          iconColor="text-indigo-400"
        />
        <StatCard
          title="Learning Streak"
          value={`${analytics?.learning_streak_days || 1} Days`}
          subtext="Daily active practice sessions"
          icon={Flame}
          iconColor="text-amber-400"
        />
        <StatCard
          title="Avg Quiz Accuracy"
          value={`${analytics?.average_quiz_score || 0}%`}
          subtext={`Across ${analytics?.quizzes_taken || 0} attempts`}
          icon={Target}
          iconColor="text-emerald-400"
        />
        <StatCard
          title="Active Concepts"
          value={analytics?.mastery_by_topic.length || 0}
          subtext={`${analytics?.topics_mastered || 0} topics mastered`}
          icon={Brain}
          iconColor="text-purple-400"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Topic Mastery Bar Chart */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white tracking-tight">
              Mastery Score by Topic
            </h2>
            <Badge variant="indigo">0 - 100%</Badge>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quiz Performance Progression Line Chart */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white tracking-tight">
              Quiz Accuracy Progression
            </h2>
            <Badge variant="emerald">Recent Attempts</Badge>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={quizTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Weak & Strong Concepts Tracking */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Identified Weak Concepts */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Target Remediation Concepts</span>
          </div>
          <p className="text-xs text-slate-400">
            Identified through recurring mistakes on quiz question tags:
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            {(analytics?.top_weak_concepts || ['nested_loops', 'while_loop_termination', 'variable_scope']).map((c) => (
              <span
                key={c}
                className="px-3 py-1 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-mono"
              >
                {c}
              </span>
            ))}
          </div>
        </div>

        {/* Identified Strong Concepts */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <CheckCircle2 className="w-4 h-4" />
            <span>Demonstrated Strong Competencies</span>
          </div>
          <p className="text-xs text-slate-400">
            Validated through multiple consecutive correct answers:
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            {(analytics?.top_strong_concepts || ['variable_naming', 'type_casting', 'boolean_truthiness']).map((c) => (
              <span
                key={c}
                className="px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
