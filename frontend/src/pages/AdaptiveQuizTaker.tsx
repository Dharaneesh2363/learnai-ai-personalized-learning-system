import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { quizzesApi } from '../api';
import { QuestionClient, AdaptiveStepResponse, QuizTake } from '../api/types';
import { Badge } from '../components/Badge';
import {
  HelpCircle,
  Clock,
  Sparkles,
  CheckCircle2,
  XCircle,
  ArrowRight,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';

export const AdaptiveQuizTaker: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [searchParams] = useSearchParams();
  const quizId = searchParams.get('quizId');
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [quizInfo, setQuizInfo] = useState<QuizTake | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionClient | null>(null);
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  
  // Adaptive step feedback state
  const [stepFeedback, setStepFeedback] = useState<AdaptiveStepResponse | null>(null);
  const [questionCount, setQuestionCount] = useState(1);
  const [currentDifficulty, setCurrentDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');

  useEffect(() => {
    const initQuiz = async () => {
      if (!quizId) return;
      try {
        const takeData = await quizzesApi.getQuizTake(parseInt(quizId));
        setQuizInfo(takeData);
        if (takeData.questions && takeData.questions.length > 0) {
          setCurrentQuestion(takeData.questions[0]);
          setCurrentDifficulty(takeData.questions[0].difficulty);
        }
      } catch (err) {
        console.error('Failed to initialize quiz taker:', err);
      } finally {
        setLoading(false);
      }
    };
    initQuiz();
  }, [quizId]);

  const handleSubmitStep = async () => {
    if (!selectedOption || !currentQuestion || !attemptId) return;
    setSubmitting(true);
    try {
      const stepRes = await quizzesApi.submitAdaptiveStep({
        attempt_id: parseInt(attemptId),
        question_id: currentQuestion.id,
        selected_answer: selectedOption,
        time_spent_seconds: 30,
      });
      setStepFeedback(stepRes);
      setCurrentDifficulty(stepRes.current_difficulty);
    } catch (err) {
      console.error('Failed submitting answer step:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (!stepFeedback) return;
    if (stepFeedback.is_completed) {
      navigate(`/results/${attemptId}`);
      return;
    }
    if (stepFeedback.next_question) {
      setCurrentQuestion(stepFeedback.next_question);
      setSelectedOption('');
      setStepFeedback(null);
      setQuestionCount((prev) => prev + 1);
    } else {
      navigate(`/results/${attemptId}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">No questions available for this assessment.</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Quiz Progress Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold">
            {quizInfo?.title || 'Adaptive Assessment'}
          </span>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm font-bold text-white font-mono">
              Question {questionCount} of {stepFeedback?.total_questions || 5}
            </span>
            <Badge
              variant={
                currentDifficulty === 'hard'
                  ? 'rose'
                  : currentDifficulty === 'medium'
                  ? 'amber'
                  : 'emerald'
              }
            >
              Live Difficulty: {currentDifficulty.toUpperCase()}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Real-time Cognitive Calibration</span>
        </div>
      </div>

      {/* Main Question Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-6 shadow-xl">
        <div className="space-y-2">
          {currentQuestion.concept_tag && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              Concept: {currentQuestion.concept_tag}
            </span>
          )}
          <h2 className="text-lg md:text-xl font-bold text-white whitespace-pre-line leading-relaxed">
            {currentQuestion.question_text}
          </h2>
        </div>

        {/* Options */}
        <div className="space-y-3 pt-2">
          {currentQuestion.options_json.map((opt) => {
            const isSelected = selectedOption === opt.id;
            return (
              <button
                key={opt.id}
                disabled={Boolean(stepFeedback) || submitting}
                onClick={() => setSelectedOption(opt.id)}
                className={`w-full text-left p-4 rounded-xl border transition flex items-center justify-between ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-600/10 text-white shadow-sm'
                    : 'border-slate-800 bg-slate-950/70 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60'
                } disabled:cursor-not-allowed`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                      isSelected
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {opt.id}
                  </div>
                  <span className="text-sm font-medium">{opt.text}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Button (Submit) */}
        {!stepFeedback && (
          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              disabled={!selectedOption || submitting}
              onClick={handleSubmitStep}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-40"
            >
              <span>{submitting ? 'Verifying Answer...' : 'Confirm Answer'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Real-time Pedagogical Feedback Banner */}
        {stepFeedback && (
          <div
            className={`p-5 rounded-xl border transition space-y-3 ${
              stepFeedback.is_correct
                ? 'bg-emerald-950/30 border-emerald-500/40'
                : 'bg-rose-950/30 border-rose-500/40'
            }`}
          >
            <div className="flex items-center gap-2">
              {stepFeedback.is_correct ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold text-emerald-400">
                    Correct! Difficulty adjusted to {stepFeedback.current_difficulty.toUpperCase()}.
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-rose-400" />
                  <span className="text-sm font-bold text-rose-400">
                    Incorrect. Correct Answer: {stepFeedback.correct_answer}
                  </span>
                </>
              )}
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              <strong>Explanation:</strong> {stepFeedback.explanation}
            </p>

            <div className="pt-3 border-t border-slate-800/80 flex justify-end">
              <button
                onClick={handleNextQuestion}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white shadow-md shadow-indigo-600/20 transition"
              >
                <span>
                  {stepFeedback.is_completed ? 'View Complete Assessment Report' : 'Next Adaptive Question'}
                </span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
