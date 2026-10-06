import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { coursesApi } from '../api';
import { CourseDetail as CourseDetailType } from '../api/types';
import { Badge } from '../components/Badge';
import {
  BookOpen,
  ArrowLeft,
  ChevronRight,
  Clock,
  CheckCircle,
  HelpCircle,
  FileText
} from 'lucide-react';

export const CourseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [course, setCourse] = useState<CourseDetailType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return;
      try {
        const data = await coursesApi.getCourseDetail(parseInt(id));
        setCourse(data);
      } catch (err) {
        console.error('Failed to load course details:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Course not found.</p>
        <Link to="/courses" className="mt-4 inline-block text-indigo-400 text-sm font-semibold">
          Back to Courses
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Back button */}
      <Link
        to="/courses"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition font-medium"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Catalog
      </Link>

      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl bg-slate-900 border border-slate-800 p-6 md:p-8">
        <div className="flex flex-col md:flex-row gap-6 items-start">
          <img
            src={course.thumbnail_url}
            alt={course.title}
            className="w-full md:w-56 h-36 object-cover rounded-xl border border-slate-800 shadow-md"
          />
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                {course.category}
              </span>
              <Badge variant="indigo">{course.difficulty.toUpperCase()}</Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {course.title}
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
              {course.description}
            </p>
          </div>
        </div>
      </div>

      {/* Curriculum Outline */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-tight">Curriculum Syllabus</h2>
          <span className="text-xs text-slate-400 font-mono">
            {course.modules.length} Modules • {course.modules.reduce((acc, m) => acc + m.topics.length, 0)} Topics
          </span>
        </div>

        <div className="space-y-4">
          {course.modules.map((mod, modIdx) => (
            <div
              key={mod.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <span className="text-xs font-mono text-indigo-400 font-semibold uppercase">
                    Module {modIdx + 1}
                  </span>
                  <h3 className="text-base font-bold text-white mt-0.5">{mod.title}</h3>
                  {mod.description && (
                    <p className="text-xs text-slate-400 mt-1">{mod.description}</p>
                  )}
                </div>
              </div>

              {/* Topics inside module */}
              <div className="grid grid-cols-1 gap-3 pt-1">
                {mod.topics.map((topic) => (
                  <div
                    key={topic.id}
                    className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-white">{topic.title}</span>
                        {topic.prerequisites && topic.prerequisites.length > 0 && (
                          <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-mono">
                            Prereq: {topic.prerequisites.map((p) => p.prerequisite_title).filter(Boolean).join(', ')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                        <Clock className="w-3.5 h-3.5" />
                        <span>~{topic.estimated_minutes} mins</span>
                      </div>
                    </div>

                    {topic.description && (
                      <p className="text-xs text-slate-400 mb-3">{topic.description}</p>
                    )}

                    {/* Lessons list */}
                    {topic.lessons && topic.lessons.length > 0 && (
                      <div className="space-y-1.5 mt-2">
                        {topic.lessons.map((lesson) => (
                          <Link
                            key={lesson.id}
                            to={`/learn/${lesson.id}`}
                            className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-indigo-600/10 hover:text-indigo-300 text-xs text-slate-300 transition group border border-transparent hover:border-indigo-500/20"
                          >
                            <div className="flex items-center gap-2">
                              <FileText className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400" />
                              <span>{lesson.title}</span>
                            </div>
                            <span className="text-[11px] text-slate-500 font-mono group-hover:text-indigo-400">
                              {lesson.duration_minutes} min read →
                            </span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
