import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { quizzesApi } from '../api';
import { QuizSummary } from '../api/types';
import { Badge } from '../components/Badge';
import { HelpCircle, Clock, Award, Sparkles, ArrowRight } from 'lucide-react';

export const Quizzes: React.FC = () => {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchQuizzes = async () => {
      try {
        const data = await quizzesApi.getQuizzes();
        setQuizzes(data);
      } catch (err) {
        console.error('Failed to load quizzes:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchQuizzes();
  }, []);

  const handleStartQuiz = async (quizId: number) => {
    try {
      const attempt = await quizzesApi.startAttempt(quizId);
      navigate(`/quiz/${attempt.id}?quizId=${quizId}`);
    } catch (err) {
      console.error('Failed to start quiz attempt:', err);
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
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <HelpCircle className="w-6 h-6 text-indigo-400" /> Assessment Bank
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Adaptive tests with dynamic real-time difficulty scaling and authoritative grading.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {quizzes.map((quiz) => (
          <div
            key={quiz.id}
            className={`p-6 rounded-2xl bg-slate-900 border transition flex flex-col justify-between shadow-sm ${
              quiz.is_adaptive
                ? 'border-indigo-500/40 bg-gradient-to-br from-indigo-950/30 to-slate-900'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                {quiz.is_adaptive ? (
                  <Badge variant="indigo">
                    <Sparkles className="w-3 h-3 mr-1 inline" /> Real-time Adaptive Engine
                  </Badge>
                ) : (
                  <Badge variant="slate">Standard Diagnostic</Badge>
                )}
                <span className="text-xs font-mono text-slate-400">
                  Pass Mark: {quiz.passing_score}%
                </span>
              </div>

              <h2 className="text-lg font-bold text-white tracking-tight">{quiz.title}</h2>
              <p className="text-xs text-slate-300 leading-relaxed">{quiz.description}</p>

              <div className="flex items-center gap-4 text-xs font-mono text-slate-400 pt-2">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" /> {quiz.time_limit_minutes} mins
                </span>
                <span className="flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-slate-500" /> {quiz.question_count} Questions
                </span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-xs font-mono text-indigo-400 font-semibold">
                {quiz.is_adaptive ? 'Dynamic Difficulty Adjustment' : 'Linear Diagnostic'}
              </span>
              <button
                onClick={() => handleStartQuiz(quiz.id)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white shadow-md shadow-indigo-600/20 transition"
              >
                <span>Launch Assessment</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
