import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { masteryApi, recommendationsApi, analyticsApi, coursesApi } from '../api';
import { MasterySummary, Recommendation, DashboardAnalytics, Course } from '../api/types';
import { StatCard } from '../components/StatCard';
import { ProgressBar } from '../components/ProgressBar';
import { Badge } from '../components/Badge';
import {
  Sparkles,
  Flame,
  Award,
  BookOpen,
  ArrowRight,
  Target,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  Brain,
  CheckCircle2
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [masterySummary, setMasterySummary] = useState<MasterySummary | null>(null);
  const [heroRec, setHeroRec] = useState<Recommendation | null>(null);
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const [mSummary, hRec, dashAnalytics, courseList] = await Promise.all([
        masteryApi.getSummary(),
        recommendationsApi.getHero(),
        analyticsApi.getDashboard(),
        coursesApi.getCourses(),
      ]);
      setMasterySummary(mSummary);
      setHeroRec(hRec);
      setAnalytics(dashAnalytics);
      setCourses(courseList);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await recommendationsApi.getRecommendations(true); // force refresh recommendations
    await fetchDashboardData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading personalized learning telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Welcome back, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Your personalized knowledge telemetry and adaptive study roadmap.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-300 transition w-fit disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {/* Top Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Mastery"
          value={`${masterySummary?.overall_mastery || 0}%`}
          subtext={`${masterySummary?.mastered_count || 0} of ${masterySummary?.total_topics || 0} topics mastered`}
          icon={Award}
          iconColor="text-indigo-400"
          trend="+4.2% this week"
          trendPositive={true}
        />
        <StatCard
          title="Active Learning Streak"
          value={`${analytics?.learning_streak_days || 1} Days`}
          subtext="Consistent study boosts retention"
          icon={Flame}
          iconColor="text-amber-400"
          trend="Top 10% Consistency"
          trendPositive={true}
        />
        <StatCard
          title="Quizzes Completed"
          value={analytics?.quizzes_taken || 0}
          subtext={`Avg accuracy: ${analytics?.average_quiz_score || 0}%`}
          icon={Target}
          iconColor="text-emerald-400"
        />
        <StatCard
          title="Study Time Logged"
          value={`${Math.round((analytics?.total_time_spent_minutes || 0) / 60 * 10) / 10} hrs`}
          subtext={`${analytics?.total_time_spent_minutes || 0} minutes total`}
          icon={BookOpen}
          iconColor="text-purple-400"
        />
      </div>

      {/* EXPLAINABLE HERO RECOMMENDATION CARD */}
      {heroRec && (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-950/70 via-slate-900 to-slate-900 border border-indigo-500/30 p-6 md:p-8 shadow-xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex items-center gap-2 mb-3">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold uppercase tracking-wider font-mono">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Primary Intelligence Recommendation
            </span>
            <Badge variant="rose">Priority: {heroRec.priority.toUpperCase()}</Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div className="lg:col-span-2 space-y-4">
              <div>
                <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
                  {heroRec.title}
                </h2>
                <p className="mt-2 text-sm text-slate-300 font-medium">
                  {heroRec.what_description}
                </p>
              </div>

              {/* Explainability Breakdown (WHAT, WHY, EVIDENCE, ACTION) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    Why is this recommended?
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {heroRec.why_description}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Diagnostic Evidence
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {heroRec.evidence_description}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Action Plan:</span>
                <span>{heroRec.action_description}</span>
              </div>
            </div>

            {/* Action CTA */}
            <div className="flex flex-col gap-3 justify-center items-start lg:items-end border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-6">
              <div className="text-left lg:text-right">
                <p className="text-xs text-slate-400 font-mono">Estimated Duration</p>
                <p className="text-base font-bold text-white">{heroRec.estimated_duration_minutes} Mins</p>
              </div>

              {heroRec.topic_id && (
                <button
                  onClick={() => navigate(`/quizzes`)}
                  className="w-full lg:w-auto flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm text-white shadow-lg shadow-indigo-600/30 transition"
                >
                  <span>Start Adaptive Practice</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TOPIC MASTERY BREAKDOWN & RADAR */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Mastery List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Topic Mastery Breakdown</h2>
              <p className="text-xs text-slate-400">
                Calculated via recent quiz accuracy, historical retention, and concept mistakes
              </p>
            </div>
            <Link
              to="/analytics"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              Detailed Analytics <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-4">
            {masterySummary?.topics.slice(0, 6).map((topic) => (
              <div
                key={topic.id}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div>
                    <span className="text-sm font-semibold text-white">{topic.topic_title}</span>
                    <span className="text-xs text-slate-500 ml-2 font-mono">({topic.course_title})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        topic.level === 'mastered'
                          ? 'emerald'
                          : topic.level === 'proficient'
                          ? 'indigo'
                          : topic.level === 'developing'
                          ? 'amber'
                          : 'rose'
                      }
                    >
                      {topic.level.toUpperCase()}
                    </Badge>
                    <span className="text-xs font-mono font-bold text-white">{topic.mastery_score}%</span>
                  </div>
                </div>

                <ProgressBar value={topic.mastery_score} size="md" />

                {/* Concept tags */}
                <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
                  {topic.weak_concepts.length > 0 && (
                    <>
                      <span className="text-[11px] text-rose-400 font-medium">Needs Work:</span>
                      {topic.weak_concepts.map((concept) => (
                        <span
                          key={concept}
                          className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] font-mono"
                        >
                          {concept}
                        </span>
                      ))}
                    </>
                  )}
                  {topic.strong_concepts.length > 0 && (
                    <>
                      <span className="text-[11px] text-emerald-400 font-medium ml-2">Solid:</span>
                      {topic.strong_concepts.slice(0, 2).map((concept) => (
                        <span
                          key={concept}
                          className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono"
                        >
                          {concept}
                        </span>
                      ))}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: AI Tutor Quick Launcher & Strengths/Weaknesses */}
        <div className="space-y-6">
          {/* AI Tutor Card */}
          <div className="bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/30 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-sm">Context-Aware AI Tutor</h3>
                <p className="text-xs text-slate-400">Ask questions about your weak concepts</p>
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              Your tutor has full visibility into your recent mistakes in <strong>Python Loops</strong> and will tailor explanations step-by-step.
            </p>
            <Link
              to="/tutor"
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white transition shadow-md shadow-indigo-600/20"
            >
              <span>Launch AI Tutor Session</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Quick Stats: Mastered vs Weak */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h3 className="font-bold text-white text-sm mb-4">Knowledge Distribution</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Mastered (80-100%)
                </span>
                <span className="font-mono font-bold text-white">{masterySummary?.mastered_count || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Proficient (60-79%)
                </span>
                <span className="font-mono font-bold text-white">{masterySummary?.proficient_count || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Developing (40-59%)
                </span>
                <span className="font-mono font-bold text-white">{masterySummary?.developing_count || 0}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-300">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Beginner (0-39%)
                </span>
                <span className="font-mono font-bold text-white">{masterySummary?.beginner_count || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Courses Catalog Carousel/Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Active Curriculum</h2>
            <p className="text-xs text-slate-400">Courses tailored to your learning track</p>
          </div>
          <Link to="/courses" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
            View All Courses <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div
              key={course.id}
              className="group bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden hover:border-indigo-500/50 transition flex flex-col"
            >
              <div className="h-32 w-full overflow-hidden relative">
                <img
                  src={course.thumbnail_url}
                  alt={course.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                />
                <div className="absolute top-2 right-2">
                  <Badge variant="indigo">{course.difficulty.toUpperCase()}</Badge>
                </div>
              </div>
              <div className="p-4 flex-1 flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                    {course.category}
                  </span>
                  <h3 className="font-bold text-white text-sm mt-1 group-hover:text-indigo-400 transition">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {course.description}
                  </p>
                </div>
                <Link
                  to={`/courses/${course.id}`}
                  className="mt-4 flex items-center justify-between text-xs font-semibold text-slate-300 group-hover:text-white transition"
                >
                  <span>Open Course</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
