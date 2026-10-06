import React, { useEffect, useState } from 'react';
import { studyPlansApi } from '../api';
import { StudyPlan as StudyPlanType, StudyPlanItem } from '../api/types';
import { ProgressBar } from '../components/ProgressBar';
import { Badge } from '../components/Badge';
import {
  Calendar,
  CheckCircle2,
  Circle,
  Clock,
  RefreshCw,
  Sparkles,
  Award
} from 'lucide-react';

export const StudyPlan: React.FC = () => {
  const [plan, setPlan] = useState<StudyPlanType | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPlan = async () => {
    try {
      const data = await studyPlansApi.getCurrent();
      setPlan(data);
    } catch (err) {
      console.error('Failed to load study plan:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, []);

  const handleToggle = async (itemId: number) => {
    try {
      const updatedItem = await studyPlansApi.toggleItem(itemId);
      setPlan((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          items: prev.items.map((i) => (i.id === itemId ? updatedItem : i)),
        };
      });
    } catch (err) {
      console.error('Failed to toggle item:', err);
    }
  };

  const handleRegenerate = async () => {
    setRefreshing(true);
    try {
      const newPlan = await studyPlansApi.regenerate();
      setPlan(newPlan);
    } catch (err) {
      console.error('Failed to regenerate plan:', err);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">No active study plan found.</p>
      </div>
    );
  }

  const completedCount = plan.items.filter((i) => i.is_completed).length;
  const progressPct = Math.round((completedCount / Math.max(1, plan.items.length)) * 100);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Plan Header & Progress */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 md:p-8 space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                Personalized Adaptive Curriculum
              </span>
              <Badge variant="indigo">Weekly Schedule</Badge>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight mt-1">{plan.title}</h1>
            <p className="text-xs text-slate-400 mt-1">
              Target: {plan.target_hours} hours total • Scheduled based on weak concepts
            </p>
          </div>

          <button
            onClick={handleRegenerate}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-300 transition w-fit disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Regenerate Roadmap</span>
          </button>
        </div>

        {/* Progress meter */}
        <div className="space-y-2 pt-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-slate-400">Weekly Completion Rate</span>
            <span className="text-white font-bold">{completedCount} of {plan.items.length} tasks completed ({progressPct}%)</span>
          </div>
          <ProgressBar value={progressPct} size="md" />
        </div>
      </div>

      {/* Task Checklist */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white tracking-tight">Daily Milestones</h2>

        <div className="space-y-3">
          {plan.items.map((item) => (
            <div
              key={item.id}
              onClick={() => handleToggle(item.id)}
              className={`cursor-pointer p-5 rounded-xl border transition flex items-start gap-4 ${
                item.is_completed
                  ? 'bg-slate-950/40 border-slate-800/60 opacity-80'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700 shadow-sm'
              }`}
            >
              <button
                type="button"
                className="mt-0.5 text-slate-400 hover:text-indigo-400 transition"
              >
                {item.is_completed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-500" />
                )}
              </button>

              <div className="flex-1 space-y-1">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <h3
                    className={`text-sm font-semibold ${
                      item.is_completed ? 'line-through text-slate-400' : 'text-white'
                    }`}
                  >
                    {item.title}
                  </h3>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>{item.estimated_minutes} mins</span>
                  </div>
                </div>

                {item.description && (
                  <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
