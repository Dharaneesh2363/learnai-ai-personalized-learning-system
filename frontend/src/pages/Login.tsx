import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, ArrowRight, Sparkles, Shield, User } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login, loginAsDemo } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoClick = async (role: 'student' | 'admin' | 'teacher') => {
    setError('');
    setSubmitting(true);
    try {
      await loginAsDemo(role);
      navigate('/dashboard');
    } catch (err: any) {
      setError('Failed to log in with demo account');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 mx-auto flex items-center justify-center text-white shadow-xl shadow-indigo-500/20 mb-4">
          <GraduationCap className="w-7 h-7" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white">
          LearnAI
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          AI-Powered Personalized Learning & Knowledge Modeling System
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-slate-900 border border-slate-800 py-8 px-6 sm:px-10 rounded-2xl shadow-xl">
          {/* Quick Demo Login Switcher */}
          <div className="mb-6 bg-slate-950/80 border border-indigo-500/30 p-4 rounded-xl">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-2">
              <Sparkles className="w-4 h-4" /> 1-Click Demo Evaluation Personas
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoClick('student')}
                disabled={submitting}
                className="flex items-center justify-center gap-1.5 py-2 px-2 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 rounded-lg text-xs font-semibold text-indigo-200 transition"
              >
                <User className="w-3.5 h-3.5" />
                Demo Student
              </button>
              <button
                type="button"
                onClick={() => handleDemoClick('teacher')}
                disabled={submitting}
                className="flex items-center justify-center gap-1.5 py-2 px-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 rounded-lg text-xs font-semibold text-emerald-200 transition"
              >
                <GraduationCap className="w-3.5 h-3.5" />
                Demo Teacher
              </button>
              <button
                type="button"
                onClick={() => handleDemoClick('admin')}
                disabled={submitting}
                className="flex items-center justify-center gap-1.5 py-2 px-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-xs font-semibold text-purple-200 transition"
              >
                <Shield className="w-3.5 h-3.5" />
                Demo Admin
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50"
            >
              <span>{submitting ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-400 hover:underline font-semibold">
              Register here
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
