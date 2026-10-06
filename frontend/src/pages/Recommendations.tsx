import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { recommendationsApi } from '../api';
import { Recommendation } from '../api/types';
import { Badge } from '../components/Badge';
import {
  Sparkles,
  AlertCircle,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ArrowRight,
  Bot
} from 'lucide-react';

export const Recommendations: React.FC = () => {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const fetchRecs = async (force: boolean = false) => {
    try {
      const data = await recommendationsApi.getRecommendations(force);
      setRecs(data);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRecs(false);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchRecs(true);
  };

  const handleAction = async (id: number, is_completed: boolean) => {
    try {
      await recommendationsApi.actOnRecommendation(id, { is_completed });
      setRecs((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error('Failed to update recommendation:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" /> Explainable Recommendations
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            4-factor explainable intelligence engine answering "What should I learn next?" and "Why?"
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-300 transition w-fit disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Regenerate Recommendations</span>
        </button>
      </div>

      {/* Recommendations Cards */}
      <div className="space-y-6">
        {recs.length === 0 ? (
          <div className="text-center py-12 bg-slate-900 border border-slate-800 rounded-2xl p-8">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white">All Recommended Tasks Completed!</h3>
            <p className="text-xs text-slate-400 mt-1">Take another quiz to generate fresh learning pathways.</p>
          </div>
        ) : (
          recs.map((rec) => (
            <div
              key={rec.id}
              className="p-6 md:p-8 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition shadow-sm space-y-6"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2.5">
                  <Badge variant={rec.priority === 'high' ? 'rose' : rec.priority === 'medium' ? 'amber' : 'slate'}>
                    {rec.priority.toUpperCase()} PRIORITY
                  </Badge>
                  <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                    {rec.recommendation_type.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> ~{rec.estimated_duration_minutes} mins
                  </span>
                  <Badge variant="indigo">Diff: {rec.difficulty.toUpperCase()}</Badge>
                </div>
              </div>

              {/* Title & WHAT */}
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">{rec.title}</h2>
                <div className="mt-2 text-sm text-slate-200 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <strong className="text-indigo-400 font-mono text-xs uppercase tracking-wider mr-2">WHAT:</strong>
                  {rec.what_description}
                </div>
              </div>

              {/* 4-Pillar Grid: WHY & EVIDENCE */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1.5">
                    <AlertCircle className="w-3.5 h-3.5" />
                    WHY IS THIS RECOMMENDED?
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {rec.why_description}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1.5">
                    <TrendingUp className="w-3.5 h-3.5" />
                    QUANTITATIVE EVIDENCE
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {rec.evidence_description}
                  </p>
                </div>
              </div>

              {/* ACTION & CTAs */}
              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="text-xs text-slate-300">
                  <strong className="text-emerald-400 font-mono uppercase tracking-wider mr-2">ACTION:</strong>
                  <span>{rec.action_description}</span>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleAction(rec.id, true)}
                    className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
                  >
                    Mark Complete
                  </button>
                  <Link
                    to="/quizzes"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition"
                  >
                    <span>Execute Practice</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
