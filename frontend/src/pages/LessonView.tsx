import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { coursesApi } from '../api';
import { Lesson } from '../api/types';
import { ArrowLeft, Clock, Bot, HelpCircle, CheckCircle } from 'lucide-react';

export const LessonView: React.FC = () => {
  const { lessonId } = useParams<{ lessonId: string }>();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchLesson = async () => {
      if (!lessonId) return;
      try {
        const data = await coursesApi.getLessonDetail(parseInt(lessonId));
        setLesson(data);
      } catch (err) {
        console.error('Failed to load lesson:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLesson();
  }, [lessonId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Lesson not found.</p>
        <Link to="/courses" className="mt-4 inline-block text-indigo-400 text-sm font-semibold">
          Back to Courses
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Navigation header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back
        </button>

        <div className="flex items-center gap-3">
          <Link
            to="/tutor"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold hover:bg-indigo-600/30 transition"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Ask AI Tutor</span>
          </Link>
          <Link
            to="/quizzes"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold hover:bg-emerald-600/30 transition"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Take Quiz</span>
          </Link>
        </div>
      </div>

      {/* Main Lesson Content Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-10 shadow-lg space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono mb-2">
            <Clock className="w-3.5 h-3.5" />
            <span>{lesson.duration_minutes} minutes estimated read</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            {lesson.title}
          </h1>
        </div>

        {/* Markdown Render */}
        <div className="prose prose-invert prose-indigo max-w-none text-slate-300 text-sm leading-relaxed space-y-4">
          {lesson.content_markdown.split('\n\n').map((paragraph, idx) => {
            if (paragraph.startsWith('```')) {
              const lines = paragraph.split('\n');
              const code = lines.slice(1, -1).join('\n');
              return (
                <div key={idx} className="my-4 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-4">
                  <pre className="font-mono text-xs text-indigo-300 overflow-x-auto">
                    <code>{code}</code>
                  </pre>
                </div>
              );
            }
            if (paragraph.startsWith('# ')) {
              return <h1 key={idx} className="text-xl font-bold text-white mt-6 mb-2">{paragraph.replace('# ', '')}</h1>;
            }
            if (paragraph.startsWith('### ')) {
              return <h3 key={idx} className="text-base font-bold text-slate-200 mt-4 mb-1">{paragraph.replace('### ', '')}</h3>;
            }
            return <p key={idx}>{paragraph}</p>;
          })}
        </div>

        {/* Completion footer */}
        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>Telemetry logged: Completed lesson view event</span>
          </div>
          <Link
            to="/quizzes"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white shadow-md shadow-indigo-600/30 transition"
          >
            <span>Test Knowledge with Adaptive Quiz</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
