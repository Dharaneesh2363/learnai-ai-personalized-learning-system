import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { quizzesApi } from '../api';
import { QuizAttemptDetail } from '../api/types';
import { Badge } from '../components/Badge';
import {
  Award,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  TrendingUp,
  Brain,
  Sparkles
} from 'lucide-react';

export const QuizResult: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [result, setResult] = useState<QuizAttemptDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchResult = async () => {
      if (!attemptId) return;
      try {
        const data = await quizzesApi.getAttemptDetail(parseInt(attemptId));
        setResult(data);
      } catch (err) {
        console.error('Failed to load quiz attempt result:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchResult();
  }, [attemptId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Quiz results not found.</p>
        <Link to="/quizzes" className="mt-4 inline-block text-indigo-400 text-sm font-semibold">
          Back to Quizzes
        </Link>
      </div>
    );
  }

  const passed = result.passed;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Score Summary Card */}
      <div className="relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-8 shadow-xl text-center space-y-4">
        <div className="flex justify-center">
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
              passed
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}
          >
            <Award className="w-8 h-8" />
          </div>
        </div>

        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Assessment Completed
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-1">
            {result.quiz_title}
          </h1>
        </div>

        <div className="flex items-center justify-center gap-4 pt-2">
          <div className="text-center px-4 py-2 rounded-xl bg-slate-950 border border-slate-800">
            <p className="text-xs text-slate-400 font-mono">Final Score</p>
            <p className="text-2xl font-black text-white">{result.score} / {result.max_score}</p>
          </div>
          <div className="text-center px-4 py-2 rounded-xl bg-slate-950 border border-slate-800">
            <p className="text-xs text-slate-400 font-mono">Accuracy</p>
            <p className={`text-2xl font-black ${passed ? 'text-emerald-400' : 'text-amber-400'}`}>
              {result.percentage}%
            </p>
          </div>
          <div className="text-center px-4 py-2 rounded-xl bg-slate-950 border border-slate-800">
            <p className="text-xs text-slate-400 font-mono">Status</p>
            <p className={`text-sm font-bold mt-1.5 ${passed ? 'text-emerald-400' : 'text-rose-400'}`}>
              {passed ? 'PASSED' : 'REMEDIATION NEEDED'}
            </p>
          </div>
        </div>

        {/* Dynamic Mastery Impact Box */}
        {result.mastery_changes && result.mastery_changes.length > 0 && (
          <div className="mt-6 p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 max-w-xl mx-auto text-left">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-indigo-400 mb-2 font-mono">
              <Sparkles className="w-4 h-4" /> Real-time Mastery Model Update
            </div>
            {result.mastery_changes.map((mc) => (
              <div key={mc.topic_id} className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-white font-semibold">{mc.topic_title}</span>
                  <span className="text-slate-400 ml-2 font-mono">({mc.level.toUpperCase()} Tier)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-300 font-mono font-bold">{mc.mastery_score}%</span>
                  <Badge variant={mc.trend === 'improving' ? 'emerald' : mc.trend === 'declining' ? 'rose' : 'slate'}>
                    {mc.trend.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pt-4 flex justify-center gap-3">
          <Link
            to="/recommendations"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white shadow-md shadow-indigo-600/20 transition"
          >
            <span>View Updated Recommendations</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            to="/dashboard"
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-xs text-slate-300 transition"
          >
            Dashboard
          </Link>
        </div>
      </div>

      {/* Question by Question Review */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white tracking-tight">Question Analysis & Explanations</h2>

        <div className="space-y-4">
          {result.answers.map((ans, idx) => (
            <div
              key={idx}
              className={`p-6 rounded-xl border bg-slate-900 transition ${
                ans.is_correct ? 'border-emerald-500/30' : 'border-rose-500/30'
              }`}
            >
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-slate-400">Q{idx + 1}.</span>
                  <span className="text-sm font-semibold text-white">{ans.question_text}</span>
                </div>
                {ans.is_correct ? (
                  <Badge variant="emerald">Correct (+{ans.points_awarded} pts)</Badge>
                ) : (
                  <Badge variant="rose">Incorrect (0 pts)</Badge>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs my-3 p-3 rounded-lg bg-slate-950/80 border border-slate-800">
                <div>
                  <span className="text-slate-400">Your Answer: </span>
                  <span className={ans.is_correct ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                    Option {ans.selected_answer}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Correct Answer: </span>
                  <span className="text-emerald-400 font-bold font-mono">Option {ans.correct_answer}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/80 text-xs text-slate-300">
                <strong className="text-indigo-400">Explanation: </strong>
                {ans.explanation}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
