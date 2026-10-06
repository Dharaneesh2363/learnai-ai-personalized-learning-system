import React, { useEffect, useState } from 'react';
import { adminApi, coursesApi } from '../../api';
import { Badge } from '../../components/Badge';
import { HelpCircle, Sparkles, ArrowLeft, Plus, Check } from 'lucide-react';
import { Link } from 'react-router-dom';

export const AdminQuestions: React.FC = () => {
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  
  // AI Generator form
  const [targetTopicId, setTargetTopicId] = useState<number>(3); // Python Loops by default
  const [difficulty, setDifficulty] = useState<string>('medium');
  const [count, setCount] = useState<number>(2);
  const [weakConcepts, setWeakConcepts] = useState<string>('nested_loops, while_loop_termination');
  const [generating, setGenerating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchQuestions = async () => {
    try {
      const data = await adminApi.getQuestions();
      setQuestions(data);
    } catch (err) {
      console.error('Failed to load questions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, []);

  const handleGenerateAIQuestions = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setSuccessMsg('');
    try {
      const conceptsList = weakConcepts.split(',').map((c) => c.trim()).filter(Boolean);
      const generated = await adminApi.generateAIQuestions({
        topic_id: targetTopicId,
        difficulty,
        count,
        weak_concepts: conceptsList,
      });
      setSuccessMsg(`Successfully generated and added ${generated.length} AI questions!`);
      setShowModal(false);
      await fetchQuestions();
    } catch (err) {
      console.error('Failed to generate AI questions:', err);
    } finally {
      setGenerating(false);
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
      <Link
        to="/admin"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition font-medium"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Admin Hub
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-purple-400" /> Assessment Question Bank
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Authoritative question repository with automated AI generative item synthesis.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 font-semibold text-xs text-white shadow-md shadow-purple-600/20 transition w-fit"
        >
          <Sparkles className="w-4 h-4" />
          <span>Generate AI Questions</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-400 font-medium">
          {successMsg}
        </div>
      )}

      {/* Questions list */}
      <div className="space-y-3">
        {questions.map((q) => (
          <div
            key={q.id}
            className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 hover:border-slate-700 transition"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    q.difficulty === 'hard' ? 'rose' : q.difficulty === 'medium' ? 'amber' : 'emerald'
                  }
                >
                  {q.difficulty.toUpperCase()}
                </Badge>
                {q.is_ai_generated && (
                  <Badge variant="purple">
                    <Sparkles className="w-3 h-3 mr-1 inline" /> AI Generated
                  </Badge>
                )}
                {q.concept_tag && (
                  <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    Tag: {q.concept_tag}
                  </span>
                )}
              </div>
              <span className="text-xs font-mono text-slate-400">Worth {q.points} pt(s)</span>
            </div>

            <p className="text-sm font-semibold text-white whitespace-pre-line">{q.question_text}</p>

            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300">
              <span className="text-emerald-400 font-bold mr-2">Correct Answer ({q.correct_answer}):</span>
              <span>{q.explanation}</span>
            </div>
          </div>
        ))}
      </div>

      {/* AI Generator Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2 text-white font-bold text-base">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <span>AI Question Synthesizer</span>
            </div>
            <p className="text-xs text-slate-400">
              Synthesizes curriculum-aligned questions validated against learning schemas.
            </p>

            <form onSubmit={handleGenerateAIQuestions} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Topic</label>
                <select
                  value={targetTopicId}
                  onChange={(e) => setTargetTopicId(parseInt(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                >
                  <option value={1}>Variables & Data Types</option>
                  <option value={2}>Conditions & Boolean Logic</option>
                  <option value={3}>Loops & Iteration (Weak Topic)</option>
                  <option value={4}>Functions & Scope</option>
                  <option value={5}>Object-Oriented Programming</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Question Count</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={count}
                    onChange={(e) => setCount(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Weak Concepts</label>
                <input
                  type="text"
                  value={weakConcepts}
                  onChange={(e) => setWeakConcepts(e.target.value)}
                  placeholder="nested_loops, while_loop_termination"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white shadow-md shadow-purple-600/20 transition disabled:opacity-50"
                >
                  {generating ? 'Synthesizing...' : 'Generate & Add Questions'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
